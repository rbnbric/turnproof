"""Declarative conversation contracts compiled into deterministic runtime rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ContractError(ValueError):
    """A contract or value violates the declared semantic rules."""


@dataclass(frozen=True)
class FieldSpec:
    name: str
    value_type: str
    required: bool = False
    enum: tuple[Any, ...] = ()
    depends_on: tuple[str, ...] = ()
    clarification_priority: int = 100

    def validate(self, value: Any) -> None:
        valid = {
            "string": lambda item: isinstance(item, str) and bool(item.strip()),
            "boolean": lambda item: isinstance(item, bool),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        }
        if self.value_type not in valid:
            raise ContractError(f"Unsupported type {self.value_type!r} for {self.name}")
        if not valid[self.value_type](value):
            raise ContractError(f"{self.name} must be a non-empty {self.value_type}")
        if self.enum and value not in self.enum:
            raise ContractError(f"{self.name} must be one of {list(self.enum)!r}")


@dataclass(frozen=True)
class ActionSpec:
    name: str
    required_fields: tuple[str, ...]
    invalidated_by: tuple[str, ...]
    consequence: str = "review"


@dataclass(frozen=True)
class ConversationContract:
    contract_id: str
    title: str
    fields: dict[str, FieldSpec]
    actions: dict[str, ActionSpec]

    def next_missing(self, state: dict[str, dict[str, Any]]) -> str | None:
        candidates = [
            field for field in self.fields.values()
            if field.required and state.get(field.name, {}).get("status") != "known"
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: (item.clarification_priority, item.name)).name


def compile_contract(definition: dict[str, Any]) -> ConversationContract:
    """Validate a compact mapping and return immutable runtime rules."""
    contract_id = str(definition.get("id", "")).strip()
    title = str(definition.get("title", "")).strip()
    if not contract_id or not title:
        raise ContractError("Contract id and title are required")
    raw_fields = definition.get("fields")
    if not isinstance(raw_fields, dict) or not raw_fields:
        raise ContractError("At least one field is required")
    fields: dict[str, FieldSpec] = {}
    for name, raw in raw_fields.items():
        if not isinstance(raw, dict):
            raise ContractError(f"Field {name} must be an object")
        fields[name] = FieldSpec(
            name=name,
            value_type=raw.get("type", "string"),
            required=bool(raw.get("required", False)),
            enum=tuple(raw.get("enum", ())),
            depends_on=tuple(raw.get("depends_on", ())),
            clarification_priority=int(raw.get("clarification_priority", 100)),
        )
    for field in fields.values():
        unknown = set(field.depends_on) - fields.keys()
        if unknown:
            raise ContractError(f"{field.name} depends on unknown fields: {sorted(unknown)}")
    _reject_dependency_cycles(fields)

    actions: dict[str, ActionSpec] = {}
    raw_actions = definition.get("actions", {})
    if not isinstance(raw_actions, dict):
        raise ContractError("Actions must be an object")
    for name, raw in raw_actions.items():
        if not isinstance(raw, dict):
            raise ContractError(f"Action {name} must be an object")
        required = tuple(raw.get("required_fields", ()))
        invalidated = tuple(raw.get("invalidated_by", required))
        unknown = (set(required) | set(invalidated)) - fields.keys()
        if unknown:
            raise ContractError(f"Action {name} references unknown fields: {sorted(unknown)}")
        actions[name] = ActionSpec(
            name=name,
            required_fields=required,
            invalidated_by=invalidated,
            consequence=str(raw.get("consequence", "review")),
        )
    return ConversationContract(contract_id, title, fields, actions)


def _reject_dependency_cycles(fields: dict[str, FieldSpec]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visiting:
            raise ContractError(f"Dependency cycle includes {name}")
        if name in visited:
            return
        visiting.add(name)
        for dependency in fields[name].depends_on:
            visit(dependency)
        visiting.remove(name)
        visited.add(name)

    for name in fields:
        visit(name)


DIAGNOSIS_CONTRACT = compile_contract({
    "id": "household_diagnosis_v1",
    "title": "Household diagnosis",
    "fields": {
        "scenario": {"type": "string", "required": True, "enum": ["dehumidifier", "washer"],
                     "clarification_priority": 10},
        "symptom": {"type": "string", "required": True, "clarification_priority": 20},
        "bucket_light": {"type": "string", "enum": ["yes", "no"], "clarification_priority": 30},
        "airflow": {"type": "string", "enum": ["yes", "no"], "clarification_priority": 40},
        "room_cold": {"type": "string", "enum": ["yes", "no"], "clarification_priority": 50},
    },
    "actions": {
        "accept_resolution": {
            "required_fields": ["scenario", "symptom", "bucket_light"],
            "invalidated_by": ["scenario", "symptom", "bucket_light", "airflow", "room_cold"],
            "consequence": "bounded_household_action",
        }
    },
})


HANDOFF_CONTRACT = compile_contract({
    "id": "household_handoff_v1",
    "title": "Household handoff",
    "fields": {
        "recipient": {"type": "string", "required": True, "clarification_priority": 10},
        "task": {"type": "string", "required": True, "clarification_priority": 20},
        "time_window": {"type": "string", "required": True, "clarification_priority": 30},
        "precondition": {"type": "string", "clarification_priority": 40},
        "acknowledgement_required": {"type": "boolean", "clarification_priority": 50},
    },
    "actions": {
        "send_handoff": {
            "required_fields": ["recipient", "task", "time_window"],
            "invalidated_by": ["recipient", "task", "time_window", "precondition", "acknowledgement_required"],
            "consequence": "simulated_message",
        }
    },
})


CONTRACTS = {item.contract_id: item for item in (DIAGNOSIS_CONTRACT, HANDOFF_CONTRACT)}
