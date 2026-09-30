"""MCP 2025-11-25 tool definitions and JSON-RPC dispatch."""

from __future__ import annotations

from .engine import DiagnosisEngine, DiagnosisError

PROTOCOL_VERSION = "2025-11-25"

TOOLS = [
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
]


def call_tool(engine: DiagnosisEngine, name: str, arguments: dict) -> dict:
    try:
        if name == "open_incident":
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
        else:
            raise DiagnosisError(f"Unknown tool: {name}")
        return {"content": [{"type": "text", "text": __import__("json").dumps(value, sort_keys=True)}],
                "structuredContent": value, "isError": False}
    except (DiagnosisError, KeyError, TypeError) as exc:
        return {"content": [{"type": "text", "text": str(exc)}], "isError": True}


def dispatch(engine: DiagnosisEngine, message: dict) -> dict | None:
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
            "serverInfo": {"name": "sounding", "version": "0.1.0"},
            "instructions": "Use one check at a time. Never bypass a safety_stop.",
        })
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        return _result(request_id, call_tool(engine, params.get("name", ""), params.get("arguments", {})))
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
