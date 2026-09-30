"""HTTP entry point for the MCP server and Alexa+ browser simulation."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .engine import DiagnosisEngine, DiagnosisError
from .mcp import PROTOCOL_VERSION, call_tool, dispatch

ROOT = Path(__file__).resolve().parents[1]
DATABASE = os.environ.get("SOUNDING_DATABASE", str(ROOT / "sounding.db"))
ALLOWED_ORIGINS = {
    value.strip() for value in os.environ.get(
        "SOUNDING_ALLOWED_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000"
    ).split(",") if value.strip()
}

engine = DiagnosisEngine(DATABASE)
app = FastAPI(title="Sounding", version="0.1.0")
sessions: set[str] = set()


def _validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        raise HTTPException(403, "Origin is not allowed")


def _validate_accept(request: Request) -> None:
    accepted = request.headers.get("accept", "")
    if "application/json" not in accepted or "text/event-stream" not in accepted:
        raise HTTPException(406, "Accept must include application/json and text/event-stream")


def _validate_session(session_id: str | None, protocol: str | None) -> None:
    if not session_id:
        raise HTTPException(400, "MCP-Session-Id is required")
    if session_id not in sessions:
        raise HTTPException(404, "Unknown MCP session")
    if protocol != PROTOCOL_VERSION:
        raise HTTPException(400, f"MCP-Protocol-Version must be {PROTOCOL_VERSION}")


@app.post("/mcp")
async def mcp_post(
    request: Request,
    mcp_session_id: str | None = Header(default=None),
    mcp_protocol_version: str | None = Header(default=None),
) -> Response:
    _validate_origin(request)
    _validate_accept(request)
    try:
        message = await request.json()
    except Exception as exc:
        raise HTTPException(400, "Body must be one JSON-RPC message") from exc
    is_initialize = message.get("method") == "initialize"
    if not is_initialize:
        _validate_session(mcp_session_id, mcp_protocol_version)
    reply = dispatch(engine, message)
    if reply is None:
        return Response(status_code=202)
    headers = {}
    if is_initialize and "result" in reply:
        session_id = secrets.token_urlsafe(24)
        sessions.add(session_id)
        headers["MCP-Session-Id"] = session_id
    return JSONResponse(reply, headers=headers)


@app.get("/mcp")
async def mcp_get(
    request: Request,
    mcp_session_id: str | None = Header(default=None),
    mcp_protocol_version: str | None = Header(default=None),
) -> Response:
    _validate_origin(request)
    _validate_session(mcp_session_id, mcp_protocol_version)
    return Response(status_code=405, headers={"Allow": "POST, DELETE"})


@app.delete("/mcp", status_code=204)
async def mcp_delete(
    request: Request,
    mcp_session_id: str | None = Header(default=None),
    mcp_protocol_version: str | None = Header(default=None),
) -> Response:
    _validate_origin(request)
    _validate_session(mcp_session_id, mcp_protocol_version)
    sessions.discard(mcp_session_id)
    return Response(status_code=204)


@app.post("/api/tools/{name}")
async def demo_tool(name: str, request: Request) -> JSONResponse:
    _validate_origin(request)
    result = call_tool(engine, name, await request.json())
    status = 400 if result.get("isError") else 200
    return JSONResponse(result, status_code=status)


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(ROOT / "web" / "index.html")


app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")

