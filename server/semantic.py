"""Revisioned semantic state and effect boundaries for Turnproof contracts."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .contracts import CONTRACTS, ConversationContract, ContractError


class SemanticError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class SemanticEngine:
    """Apply candidate conversational changes as atomic, inspectable revisions."""

    def __init__(self, database: str | Path, contracts: dict[str, ConversationContract] | None = None) -> None:
        self.database = str(database)
        self.contracts = contracts or CONTRACTS
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.database)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    contract_id TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 0,
                    state_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS mutations (
                    conversation_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_digest TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    response_json TEXT NOT NULL,
                    PRIMARY KEY (conversation_id, idempotency_key),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                CREATE TABLE IF NOT EXISTS semantic_events (
                    conversation_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    sequence INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    previous_json TEXT,
                    current_json TEXT,
                    source TEXT NOT NULL,
                    PRIMARY KEY (conversation_id, revision, sequence),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    bound_revision INTEGER NOT NULL,
                    bound_digest TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    receipt_json TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );
                CREATE TABLE IF NOT EXISTS effects (
                    conversation_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    receipt_json TEXT NOT NULL,
                    PRIMARY KEY (conversation_id, idempotency_key),
                    FOREIGN KEY (proposal_id) REFERENCES proposals(id)
                );
            """)
            mutation_columns = {row[1] for row in db.execute("PRAGMA table_info(mutations)")}
            if "request_digest" not in mutation_columns:
                db.execute("ALTER TABLE mutations ADD COLUMN request_digest TEXT NOT NULL DEFAULT ''")

    def open_conversation(self, contract_id: str, initial: dict[str, Any] | None = None) -> dict[str, Any]:
        contract = self._contract(contract_id)
        conversation_id = uuid.uuid4().hex[:12]
        with self._connect() as db:
            db.execute(
                "INSERT INTO conversations (id, contract_id) VALUES (?, ?)",
                (conversation_id, contract.contract_id),
            )
        if initial:
            return self.apply_changes(
                conversation_id,
                [{"field": name, "operation": "set", "value": value} for name, value in initial.items()],
                expected_revision=0,
                idempotency_key="initial",
                source="open",
            )
        return self.review(conversation_id)

    def apply_changes(
        self,
        conversation_id: str,
        changes: list[dict[str, Any]],
        *,
        expected_revision: int,
        idempotency_key: str,
        source: str = "conversation",
    ) -> dict[str, Any]:
        if not idempotency_key.strip():
            raise SemanticError("INVALID_REQUEST", "idempotency_key is required")
        request_digest = hashlib.sha256(_json({
            "expected_revision": expected_revision, "changes": changes, "source": source,
        }).encode()).hexdigest()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            replay = db.execute(
                "SELECT request_digest, response_json FROM mutations WHERE conversation_id=? AND idempotency_key=?",
                (conversation_id, idempotency_key),
            ).fetchone()
            if replay:
                if replay["request_digest"] != request_digest:
                    raise SemanticError("IDEMPOTENCY_CONFLICT", "Idempotency key was already used for different input")
                return json.loads(replay["response_json"])
            row = self._conversation(db, conversation_id)
            if row["revision"] != expected_revision:
                raise SemanticError(
                    "REVISION_CONFLICT",
                    f"Expected revision {expected_revision}, current revision is {row['revision']}",
                )
            contract = self._contract(row["contract_id"])
            state = json.loads(row["state_json"])
            next_state = json.loads(row["state_json"])
            events: list[dict[str, Any]] = []
            for change in changes:
                events.append(self._apply_candidate(contract, next_state, change))
            material = [event for event in events if event["operation"] != "no_change"]
            revision = row["revision"] + (1 if material else 0)
            if material:
                db.execute(
                    "UPDATE conversations SET revision=?, state_json=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    (revision, _json(next_state), conversation_id),
                )
                changed_fields = {event["field"] for event in material}
                self._invalidate_proposals(db, conversation_id, contract, changed_fields)
                for sequence, event in enumerate(material):
                    db.execute(
                        "INSERT INTO semantic_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            conversation_id, revision, sequence, event["field"], event["operation"],
                            _json(event["previous"]) if event["previous"] is not None else None,
                            _json(event["current"]) if event["current"] is not None else None,
                            source,
                        ),
                    )
            response = self._projection(contract, conversation_id, revision, next_state, material)
            db.execute(
                "INSERT INTO mutations (conversation_id, idempotency_key, request_digest, revision, response_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (conversation_id, idempotency_key, request_digest, revision, _json(response)),
            )
            return response

    def review(self, conversation_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = self._conversation(db, conversation_id)
        contract = self._contract(row["contract_id"])
        return self._projection(contract, conversation_id, row["revision"], json.loads(row["state_json"]), [])

    def history(self, conversation_id: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            self._conversation(db, conversation_id)
            rows = db.execute(
                "SELECT * FROM semantic_events WHERE conversation_id=? ORDER BY revision, sequence",
                (conversation_id,),
            ).fetchall()
        return [{
            "revision": row["revision"], "field": row["field_name"], "operation": row["operation"],
            "previous": json.loads(row["previous_json"]) if row["previous_json"] else None,
            "current": json.loads(row["current_json"]) if row["current_json"] else None,
            "source": row["source"],
        } for row in rows]

    def propose(self, conversation_id: str, action_name: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._connect() as db:
            row = self._conversation(db, conversation_id)
            contract = self._contract(row["contract_id"])
            if action_name not in contract.actions:
                raise SemanticError("UNKNOWN_ACTION", f"Unknown action: {action_name}")
            action = contract.actions[action_name]
            state = json.loads(row["state_json"])
            missing = [name for name in action.required_fields if state.get(name, {}).get("status") != "known"]
            if missing:
                raise SemanticError("MISSING_FACTS", f"Action requires known fields: {missing}")
            digest = self.state_digest(state)
            proposal_id = uuid.uuid4().hex[:12]
            db.execute(
                "INSERT INTO proposals VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL, CURRENT_TIMESTAMP)",
                (proposal_id, conversation_id, action_name, row["revision"], digest, _json(parameters or {})),
            )
        return {
            "proposal_id": proposal_id, "conversation_id": conversation_id, "action": action_name,
            "consequence": action.consequence, "bound_revision": row["revision"],
            "bound_digest": digest, "status": "pending",
        }

    def commit(self, proposal_id: str, *, idempotency_key: str) -> dict[str, Any]:
        if not idempotency_key.strip():
            raise SemanticError("INVALID_REQUEST", "idempotency_key is required")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            proposal = db.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
            if proposal is None:
                raise SemanticError("UNKNOWN_PROPOSAL", f"Unknown proposal: {proposal_id}")
            replay = db.execute(
                "SELECT proposal_id, receipt_json FROM effects WHERE conversation_id=? AND idempotency_key=?",
                (proposal["conversation_id"], idempotency_key),
            ).fetchone()
            if replay:
                if replay["proposal_id"] != proposal_id:
                    raise SemanticError("IDEMPOTENCY_CONFLICT", "Idempotency key was already used for another proposal")
                return json.loads(replay["receipt_json"])
            current = self._conversation(db, proposal["conversation_id"])
            digest = self.state_digest(json.loads(current["state_json"]))
            if proposal["status"] != "pending" or current["revision"] != proposal["bound_revision"] or digest != proposal["bound_digest"]:
                raise SemanticError("STATE_CHANGED", "The conversation changed after this action was proposed")
            receipt = {
                "receipt_id": uuid.uuid4().hex[:16],
                "proposal_id": proposal_id,
                "conversation_id": proposal["conversation_id"],
                "action": proposal["action_name"],
                "revision": current["revision"],
                "state_digest": digest,
                "effect": "simulated",
            }
            encoded = _json(receipt)
            db.execute("UPDATE proposals SET status='committed', receipt_json=? WHERE id=?", (encoded, proposal_id))
            db.execute(
                "INSERT INTO effects VALUES (?, ?, ?, ?)",
                (proposal["conversation_id"], idempotency_key, proposal_id, encoded),
            )
            return receipt

    @staticmethod
    def state_digest(state: dict[str, Any]) -> str:
        return "sha256:" + hashlib.sha256(_json(state).encode()).hexdigest()

    def _apply_candidate(
        self, contract: ConversationContract, state: dict[str, dict[str, Any]], change: dict[str, Any]
    ) -> dict[str, Any]:
        field_name = change.get("field")
        if field_name not in contract.fields:
            raise SemanticError("UNKNOWN_FIELD", f"Unknown field: {field_name}")
        operation = change.get("operation", "set")
        if operation not in {"set", "unknown", "clear"}:
            raise SemanticError("INVALID_OPERATION", f"Unsupported operation: {operation}")
        previous = state.get(field_name)
        if operation == "set":
            try:
                contract.fields[field_name].validate(change.get("value"))
            except ContractError as exc:
                raise SemanticError("INVALID_VALUE", str(exc)) from exc
            current = {"status": "known", "value": change["value"]}
        elif operation == "unknown":
            current = {"status": "unknown"}
        else:
            current = None
        if previous == current:
            return {"field": field_name, "operation": "no_change", "previous": previous, "current": current}
        if current is None:
            state.pop(field_name, None)
            actual = "clear"
        else:
            state[field_name] = current
            actual = "add" if previous is None else "replace"
        return {"field": field_name, "operation": actual, "previous": previous, "current": current}

    def _projection(
        self,
        contract: ConversationContract,
        conversation_id: str,
        revision: int,
        state: dict[str, dict[str, Any]],
        changed: list[dict[str, Any]],
    ) -> dict[str, Any]:
        understood = {name: item["value"] for name, item in state.items() if item.get("status") == "known"}
        unknown = sorted(name for name, item in state.items() if item.get("status") == "unknown")
        still_needed = sorted(
            name for name, field in contract.fields.items()
            if field.required and state.get(name, {}).get("status") != "known"
        )
        return {
            "conversation_id": conversation_id,
            "contract_id": contract.contract_id,
            "revision": revision,
            "understood": understood,
            "unknown": unknown,
            "changed": changed,
            "still_needed": still_needed,
            "next": contract.next_missing(state),
            "state_digest": self.state_digest(state),
        }

    def _invalidate_proposals(
        self,
        db: sqlite3.Connection,
        conversation_id: str,
        contract: ConversationContract,
        changed_fields: set[str],
    ) -> None:
        actions = {name for name, action in contract.actions.items() if changed_fields & set(action.invalidated_by)}
        if not actions:
            return
        placeholders = ",".join("?" for _ in actions)
        db.execute(
            f"UPDATE proposals SET status='invalidated' WHERE conversation_id=? AND status='pending' "
            f"AND action_name IN ({placeholders})",
            (conversation_id, *sorted(actions)),
        )

    def _conversation(self, db: sqlite3.Connection, conversation_id: str) -> sqlite3.Row:
        row = db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
        if row is None:
            raise SemanticError("UNKNOWN_CONVERSATION", f"Unknown conversation: {conversation_id}")
        return row

    def _contract(self, contract_id: str) -> ConversationContract:
        try:
            return self.contracts[contract_id]
        except KeyError as exc:
            raise SemanticError("UNKNOWN_CONTRACT", f"Unknown contract: {contract_id}") from exc
