"""MCP 2025-11-25 tool definitions and JSON-RPC dispatch."""

from __future__ import annotations

from .contracts import DIAGNOSIS_CONTRACT, HANDOFF_CONTRACT
from .engine import DiagnosisEngine, DiagnosisError
from .semantic import SemanticEngine, SemanticError

PROTOCOL_VERSION = "2025-11-25"

TOOLS = [
    {
        "name": "start_turnproof_diagnosis",
        "description": "Start a revisioned household diagnosis, preserving partial facts without inventing missing values.",
        "inputSchema": {
            "type": "object", "additionalProperties": False, "properties": {
                "scenario": {"type": "string", "enum": ["dehumidifier", "washer"]},
                "symptom": {"type": "string", "minLength": 1},
            },
        },
    },
    {
        "name": "start_turnproof_handoff",
        "description": "Start a revisioned household handoff and retain only the details the customer actually supplied.",
        "inputSchema": {
            "type": "object", "additionalProperties": False, "properties": {
                "recipient": {"type": "string", "minLength": 1},
                "task": {"type": "string", "minLength": 1},
                "time_window": {"type": "string", "minLength": 1},
                "precondition": {"type": "string", "minLength": 1},
                "acknowledgement_required": {"type": "boolean"},
            },
        },
    },
    {
        "name": "revise_turnproof_fact",
        "description": "Add, correct, mark unknown, or clear one fact in a Turnproof conversation using optimistic revision control.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["conversation_id", "expected_revision", "idempotency_key", "field", "operation"],
            "properties": {
                "conversation_id": {"type": "string"},
                "expected_revision": {"type": "integer", "minimum": 0},
                "idempotency_key": {"type": "string", "minLength": 1},
                "field": {"type": "string", "minLength": 1},
                "operation": {"type": "string", "enum": ["set", "unknown", "clear"]},
                "value": {},
            },
        },
    },
    {
        "name": "review_turnproof_conversation",
        "description": "Review the current understood facts, changes, unknowns, and smallest missing fact.",
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["conversation_id"],
                        "properties": {"conversation_id": {"type": "string"}}},
    },
    {
        "name": "propose_turnproof_action",
        "description": "Create a reviewable action bound to the exact current conversation revision and semantic digest.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["conversation_id", "action"],
            "properties": {
                "conversation_id": {"type": "string"}, "action": {"type": "string"},
                "parameters": {"type": "object"},
            },
        },
    },
    {
        "name": "commit_turnproof_action",
        "description": "Commit one proposed action if its revision still matches, returning an idempotent receipt.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["proposal_id", "idempotency_key"],
            "properties": {"proposal_id": {"type": "string"},
                           "idempotency_key": {"type": "string", "minLength": 1}},
        },
    },
    {
        "name": "open_incident",
        "description": "Open a persistent household diagnostic incident. Safety-stop terms are handled deterministically.",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "required": ["scenario", "symptom"],
            "properties": {
                "scenario": {"type": "string", "enum": ["dehumidifier", "washer"]},
                "symptom": {"type": "string", "minLength": 1},
            },
        },
    },
    {
        "name": "get_next_check", "description": "Return the next safe, deterministic inspection step.",
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["incident_id"],
                        "properties": {"incident_id": {"type": "string"}}},
    },
    {
        "name": "record_observation", "description": "Record yes, no, or unknown evidence for a requested check.",
        "inputSchema": {"type": "object", "additionalProperties": False,
                        "required": ["incident_id", "check_id", "result"],
                        "properties": {"incident_id": {"type": "string"}, "check_id": {"type": "string"},
                                       "result": {"type": "string", "enum": ["yes", "no", "unknown"]}},
        },
    },
    {
        "name": "propose_resolution", "description": "Propose the next bounded action from recorded evidence.",
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["incident_id"],
                        "properties": {"incident_id": {"type": "string"}}},
    },
    {
        "name": "verify_resolution", "description": "Close the scientific loop by recording whether the action worked.",
        "inputSchema": {"type": "object", "additionalProperties": False,
                        "required": ["incident_id", "worked"],
                        "properties": {"incident_id": {"type": "string"}, "worked": {"type": "boolean"}}},
    },
    {
        "name": "incident_summary", "description": "Read the complete evidence trail and ranked causes.",
        "inputSchema": {"type": "object", "additionalProperties": False, "required": ["incident_id"],
                        "properties": {"incident_id": {"type": "string"}}},
    },
    {
        "name": "list_incidents", "description": "List retained incidents so a household can resume work across sessions.",
        "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
    },
]


def call_tool(engine: DiagnosisEngine, semantic: SemanticEngine, name: str, arguments: dict) -> dict:
    try:
        if name == "start_turnproof_diagnosis":
            value = semantic.open_conversation(DIAGNOSIS_CONTRACT.contract_id, arguments)
        elif name == "start_turnproof_handoff":
            value = semantic.open_conversation(HANDOFF_CONTRACT.contract_id, arguments)
        elif name == "revise_turnproof_fact":
            value = semantic.apply_changes(
                arguments["conversation_id"],
                [{"field": arguments["field"], "operation": arguments["operation"],
                  **({"value": arguments.get("value")} if arguments["operation"] == "set" else {})}],
                expected_revision=arguments["expected_revision"],
                idempotency_key=arguments["idempotency_key"],
            )
        elif name == "review_turnproof_conversation":
            value = semantic.review(arguments["conversation_id"])
        elif name == "propose_turnproof_action":
            value = semantic.propose(arguments["conversation_id"], arguments["action"], arguments.get("parameters"))
        elif name == "commit_turnproof_action":
            value = semantic.commit(arguments["proposal_id"], idempotency_key=arguments["idempotency_key"])
        elif name == "open_incident":
            value = engine.open_incident(arguments["scenario"], arguments["symptom"])
        elif name == "get_next_check":
            value = engine.next_check(arguments["incident_id"])
        elif name == "record_observation":
            value = engine.record_observation(arguments["incident_id"], arguments["check_id"], arguments["result"])
        elif name == "propose_resolution":
            value = engine.propose_resolution(arguments["incident_id"])
        elif name == "verify_resolution":
            value = engine.verify_resolution(arguments["incident_id"], arguments["worked"])
        elif name == "incident_summary":
            value = engine.summary(arguments["incident_id"])
        elif name == "list_incidents":
            value = engine.list_incidents()
        else:
            raise DiagnosisError(f"Unknown tool: {name}")
        return {"content": [{"type": "text", "text": __import__("json").dumps(value, sort_keys=True)}],
                "structuredContent": value, "isError": False}
    except (DiagnosisError, SemanticError, KeyError, TypeError) as exc:
        structured = {"code": getattr(exc, "code", "INVALID_REQUEST"), "message": str(exc)}
        return {"content": [{"type": "text", "text": str(exc)}], "structuredContent": structured, "isError": True}


def dispatch(engine: DiagnosisEngine, semantic: SemanticEngine, message: dict) -> dict | None:
    if message.get("jsonrpc") != "2.0":
        return _error(message.get("id"), -32600, "Invalid JSON-RPC request")
    method = message.get("method")
    if method and method.startswith("notifications/"):
        return None
    request_id = message.get("id")
    params = message.get("params", {})
    if method == "initialize":
        requested = params.get("protocolVersion")
        if requested != PROTOCOL_VERSION:
            return _error(request_id, -32602, f"Protocol {requested!r} is unsupported")
        return _result(request_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}},
            "serverInfo": {"name": "turnproof", "version": "0.2.0"},
            "instructions": "Preserve explicit unknowns and revisions. Never commit a stale proposal.",
        })
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        return _result(request_id, call_tool(engine, semantic, params.get("name", ""), params.get("arguments", {})))
    if method == "resources/list":
        return _result(request_id, {"resources": [{
            "uri": "sounding://incidents", "name": "Incident history", "mimeType": "application/json",
            "description": "Persistent diagnostic evidence trails"
        }]})
    if method == "resources/read" and params.get("uri") == "sounding://incidents":
        import json
        return _result(request_id, {"contents": [{"uri": "sounding://incidents", "mimeType": "application/json",
                                                   "text": json.dumps(engine.list_incidents(), sort_keys=True)}]})
    return _error(request_id, -32601, f"Method not found: {method}")


def _result(request_id: object, value: object) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": value}


def _error(request_id: object, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
