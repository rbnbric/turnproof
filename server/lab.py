"""Generated adversarial checks for any compiled Turnproof contract."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .contracts import ConversationContract
from .semantic import SemanticEngine, SemanticError


def run_contract_lab(contract: ConversationContract) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as directory:
        engine = SemanticEngine(Path(directory) / "lab.db", {contract.contract_id: contract})
        action = next(iter(contract.actions.values()))
        required = [field for field in contract.fields.values() if field.required]
        fixture_names = {field.name for field in required} | set(action.required_fields)
        fixtures = {
            name: _fixture(contract.fields[name].value_type, contract.fields[name].enum, 0)
            for name in sorted(fixture_names)
        }

        opened = engine.open_conversation(contract.contract_id)
        checks.append(_check("partial_input", opened["next"] == min(
            required, key=lambda field: (field.clarification_priority, field.name)
        ).name))

        mutable = contract.fields[action.invalidated_by[0]]
        first = _fixture(mutable.value_type, mutable.enum, 0)
        second = _fixture(mutable.value_type, mutable.enum, 1)
        conversation = engine.open_conversation(contract.contract_id, fixtures)
        before = conversation["revision"]
        unknown = engine.apply_changes(
            conversation["conversation_id"], [{"field": mutable.name, "operation": "unknown"}],
            expected_revision=before, idempotency_key="unknown",
        )
        checks.append(_check("unknown_is_not_no", mutable.name in unknown["unknown"] and mutable.name not in unknown["understood"]))
        correction_changes = [{"field": mutable.name, "operation": "set", "value": second}]
        correction_revision = unknown["revision"]
        corrected = engine.apply_changes(
            conversation["conversation_id"], correction_changes,
            expected_revision=correction_revision, idempotency_key="correction",
        )
        checks.append(_check("correction_supersedes", corrected["understood"][mutable.name] == second
                             and corrected["changed"][0]["operation"] == "replace"))

        replay = engine.apply_changes(
            conversation["conversation_id"], correction_changes,
            expected_revision=correction_revision, idempotency_key="correction",
        )
        checks.append(_check("mutation_retry_is_idempotent", replay == corrected))

        proposal_conversation = engine.open_conversation(contract.contract_id, fixtures)
        proposal = engine.propose(proposal_conversation["conversation_id"], action.name)
        current = engine.review(proposal_conversation["conversation_id"])
        engine.apply_changes(
            proposal_conversation["conversation_id"],
            [{"field": mutable.name, "operation": "set", "value": second}],
            expected_revision=current["revision"], idempotency_key="invalidate",
        )
        checks.append(_expect_error("stale_action_rejected", "STATE_CHANGED", lambda: engine.commit(
            proposal["proposal_id"], idempotency_key="commit-stale"
        )))

        stable = engine.open_conversation(contract.contract_id, fixtures)
        stable_proposal = engine.propose(stable["conversation_id"], action.name)
        receipt = engine.commit(stable_proposal["proposal_id"], idempotency_key="commit")
        duplicate = engine.commit(stable_proposal["proposal_id"], idempotency_key="commit")
        checks.append(_check("effect_retry_is_idempotent", receipt == duplicate))

        race = engine.open_conversation(contract.contract_id, fixtures)
        engine.apply_changes(
            race["conversation_id"], [{"field": mutable.name, "operation": "set", "value": second}],
            expected_revision=race["revision"], idempotency_key="winner",
        )
        checks.append(_expect_error("concurrent_stale_write_rejected", "REVISION_CONFLICT", lambda: engine.apply_changes(
            race["conversation_id"], [{"field": mutable.name, "operation": "set", "value": first}],
            expected_revision=race["revision"], idempotency_key="loser",
        )))

        left = engine.open_conversation(contract.contract_id)
        right = engine.open_conversation(contract.contract_id)
        ordered = list(fixtures.items())
        for index, (name, value) in enumerate(ordered):
            left = engine.apply_changes(left["conversation_id"], [{"field": name, "operation": "set", "value": value}],
                                        expected_revision=left["revision"], idempotency_key=f"left-{index}")
        for index, (name, value) in enumerate(reversed(ordered)):
            right = engine.apply_changes(right["conversation_id"], [{"field": name, "operation": "set", "value": value}],
                                         expected_revision=right["revision"], idempotency_key=f"right-{index}")
        checks.append(_check("independent_order_converges", left["state_digest"] == right["state_digest"]))

    return {
        "contract_id": contract.contract_id,
        "passed": sum(item["passed"] for item in checks),
        "total": len(checks),
        "checks": checks,
    }


def _fixture(value_type: str, enum: tuple[Any, ...], variant: int) -> Any:
    if enum:
        return enum[min(variant, len(enum) - 1)]
    if value_type == "string":
        return "alternate value" if variant else "fixture value"
    if value_type == "boolean":
        return bool(variant)
    if value_type == "integer":
        return variant + 1
    if value_type == "number":
        return variant + 0.5
    raise ValueError(value_type)


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed)}


def _expect_error(name: str, code: str, callback: Any) -> dict[str, Any]:
    try:
        callback()
    except SemanticError as exc:
        return _check(name, exc.code == code)
    return _check(name, False)
