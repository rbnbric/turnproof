"""Run generated Turnproof contract attacks and print their JSON receipt."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.contracts import CONTRACTS
from server.lab import run_contract_lab


def main() -> int:
    reports = [run_contract_lab(contract) for contract in CONTRACTS.values()]
    receipt = {
        "passed": sum(report["passed"] for report in reports),
        "total": sum(report["total"] for report in reports),
        "contracts": reports,
    }
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["passed"] == receipt["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
