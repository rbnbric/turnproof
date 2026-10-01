"""Fail if the demo shell loses a required control or local asset."""

from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / "web" / "index.html").read_text()
javascript = (root / "web" / "app.js").read_text()

required_html = ["id=\"facts\"", "id=\"history\"", "id=\"checks\"", "id=\"trace\"", "id=\"run-lab\"", "id=\"commit-stale\""]
required_tools = ["start_turnproof_diagnosis", "start_turnproof_handoff", "revise_turnproof_fact",
                  "propose_turnproof_action", "commit_turnproof_action"]

missing = [item for item in required_html if item not in html]
missing += [item for item in required_tools if item not in javascript]
if missing:
    raise SystemExit(f"missing demo contract: {', '.join(missing)}")
print(f"web contract: {len(required_html)} controls, {len(required_tools)} tool calls")
