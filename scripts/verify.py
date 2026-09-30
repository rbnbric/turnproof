"""Run bounded conformance gates and retain a machine-readable receipt."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = [
    ("syntax", [sys.executable, "-m", "py_compile", "server/app.py", "server/catalog.py", "server/engine.py", "server/mcp.py"]),
    ("evidence_engine", [sys.executable, "-m", "unittest", "-v", "tests.test_engine"]),
    ("mcp_transport", [sys.executable, "-m", "unittest", "-v", "tests.test_mcp"]),
    ("browser_contract", [sys.executable, "scripts/check_web.py"]),
]


def digest_sources() -> str:
    digest = hashlib.sha256()
    for path in sorted([*ROOT.glob("server/*.py"), *ROOT.glob("tests/*.py"), *ROOT.glob("web/*")]):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> int:
    results = []
    for name, command in GATES:
        started = time.monotonic()
        process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=30)
        results.append({
            "gate": name,
            "passed": process.returncode == 0,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
            "output": (process.stdout + process.stderr)[-4000:],
        })
    report = {
        "schema_version": 1,
        "project": "Sounding",
        "source_sha256": digest_sources(),
        "passed": sum(result["passed"] for result in results),
        "total": len(results),
        "gates": results,
    }
    target = ROOT / "evidence" / "latest.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Sounding conformance: {report['passed']}/{report['total']} gates passed")
    print(target)
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

