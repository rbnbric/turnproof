"""Deterministic evidence engine. Natural language never decides safety or state."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from .catalog import HAZARD_TERMS, SCENARIOS


class DiagnosisError(ValueError):
    pass


class DiagnosisEngine:
    def __init__(self, database: str | Path = "sounding.db") -> None:
        self.database = str(database)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY, scenario TEXT NOT NULL, symptom TEXT NOT NULL,
                    status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolution TEXT, verified INTEGER
                );
                CREATE TABLE IF NOT EXISTS observations (
                    incident_id TEXT NOT NULL, check_id TEXT NOT NULL, result TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (incident_id, check_id),
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
            """)

    def open_incident(self, scenario: str, symptom: str) -> dict:
        scenario = scenario.strip().lower()
        symptom = symptom.strip()
        if scenario not in SCENARIOS:
            raise DiagnosisError(f"Unsupported scenario: {scenario}")
        if not symptom:
            raise DiagnosisError("symptom must not be empty")
        incident_id = uuid.uuid4().hex[:12]
        hazardous = any(term in symptom.lower() for term in HAZARD_TERMS)
        status = "safety_stop" if hazardous else "investigating"
        with self._connect() as db:
            db.execute(
                "INSERT INTO incidents (id, scenario, symptom, status) VALUES (?, ?, ?, ?)",
                (incident_id, scenario, symptom, status),
            )
        result = self.summary(incident_id)
        if hazardous:
            result["safety_message"] = (
                "Stop using the equipment, keep clear, disconnect power only if safe, "
                "and contact emergency or qualified service support as appropriate."
            )
        return result

    def record_observation(self, incident_id: str, check_id: str, result: str) -> dict:
        result = result.strip().lower()
        if result not in {"yes", "no", "unknown"}:
            raise DiagnosisError("result must be yes, no, or unknown")
        incident = self._incident(incident_id)
        if incident["status"] != "investigating":
            raise DiagnosisError(f"incident is {incident['status']}")
        scenario = SCENARIOS[incident["scenario"]]
        if check_id not in {check["id"] for check in scenario["checks"]}:
            raise DiagnosisError(f"Unknown check: {check_id}")
        with self._connect() as db:
            db.execute(
                "INSERT INTO observations (incident_id, check_id, result) VALUES (?, ?, ?) "
                "ON CONFLICT(incident_id, check_id) DO UPDATE SET result=excluded.result, created_at=CURRENT_TIMESTAMP",
                (incident_id, check_id, result),
            )
        return self.summary(incident_id)

    def next_check(self, incident_id: str) -> dict | None:
        incident = self._incident(incident_id)
        if incident["status"] != "investigating":
            return None
        answered = set(self._observations(incident_id))
        remaining = [c for c in SCENARIOS[incident["scenario"]]["checks"] if c["id"] not in answered]
        if not remaining:
            return None
        check = sorted(remaining, key=lambda item: (-item["priority"], item["id"]))[0]
        return {key: check[key] for key in ("id", "prompt", "instruction")}

    def propose_resolution(self, incident_id: str) -> dict:
        incident = self._incident(incident_id)
        if incident["status"] != "investigating":
            raise DiagnosisError(f"incident is {incident['status']}")
        observations = self._observations(incident_id)
        if not observations:
            raise DiagnosisError("At least one observation is required before a resolution")
        top = self._ranked(incident)[0]
        action = SCENARIOS[incident["scenario"]]["resolutions"][top["id"]]
        with self._connect() as db:
            db.execute(
                "UPDATE incidents SET status='proposed', resolution=? WHERE id=?",
                (action, incident_id),
            )
        return {"incident_id": incident_id, "cause": top, "action": action, "requires_verification": True}

    def verify_resolution(self, incident_id: str, worked: bool) -> dict:
        incident = self._incident(incident_id)
        if incident["status"] != "proposed":
            raise DiagnosisError("A resolution must be proposed before verification")
        status = "resolved" if worked else "unresolved"
        with self._connect() as db:
            db.execute(
                "UPDATE incidents SET status=?, verified=? WHERE id=?",
                (status, int(worked), incident_id),
            )
        return self.summary(incident_id)

    def summary(self, incident_id: str) -> dict:
        incident = self._incident(incident_id)
        observations = self._observations(incident_id)
        return {
            "incident_id": incident["id"],
            "scenario": incident["scenario"],
            "scenario_label": SCENARIOS[incident["scenario"]]["label"],
            "symptom": incident["symptom"],
            "status": incident["status"],
            "observations": observations,
            "ranked_causes": self._ranked(incident),
            "next_check": self.next_check(incident_id) if incident["status"] == "investigating" else None,
            "resolution": incident["resolution"],
            "verified": None if incident["verified"] is None else bool(incident["verified"]),
        }

    def list_incidents(self) -> list[dict]:
        with self._connect() as db:
            ids = [row["id"] for row in db.execute("SELECT id FROM incidents ORDER BY created_at DESC, id")]
        return [self.summary(incident_id) for incident_id in ids]

    def _incident(self, incident_id: str) -> sqlite3.Row:
        with self._connect() as db:
            row = db.execute("SELECT * FROM incidents WHERE id=?", (incident_id,)).fetchone()
        if row is None:
            raise DiagnosisError(f"Unknown incident: {incident_id}")
        return row

    def _observations(self, incident_id: str) -> dict[str, str]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT check_id, result FROM observations WHERE incident_id=? ORDER BY check_id",
                (incident_id,),
            ).fetchall()
        return {row["check_id"]: row["result"] for row in rows}

    def _ranked(self, incident: sqlite3.Row) -> list[dict]:
        scenario = SCENARIOS[incident["scenario"]]
        scores = {key: float(value["prior"]) for key, value in scenario["causes"].items()}
        observations = self._observations(incident["id"])
        checks = {check["id"]: check for check in scenario["checks"]}
        for check_id, result in observations.items():
            if result == "unknown":
                continue
            for cause, factor in checks[check_id]["effects"].get(result, {}).items():
                scores[cause] *= factor
        total = sum(scores.values()) or 1.0
        ranked = [
            {"id": cause, "label": scenario["causes"][cause]["label"], "confidence": round(score / total, 3)}
            for cause, score in scores.items()
        ]
        return sorted(ranked, key=lambda item: (-item["confidence"], item["id"]))


def compact_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)
