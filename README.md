# Sounding

**Alexa+, help me find what actually changed.**

Sounding is a voice-first household diagnostician built for the Alexa+ track of the 2026 Build, Ship, Shape Amazon Developer Hackathon. It preserves observations across sessions, selects one safe inspection at a time, ranks known causes deterministically, and verifies whether the proposed action worked.

The LLM interprets conversation. The evidence engine owns safety, state transitions, rankings, and action gates.

## Run

Requires Python 3.11+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The MCP endpoint is `http://127.0.0.1:8000/mcp` and implements protocol version `2025-11-25` over Streamable HTTP.

## Verify

```bash
python -m unittest discover -v
```

The tests exercise persistent evidence, deterministic ranking, safety stops, resolution verification, MCP initialization, session lifecycle, required headers, and origin validation.

To run the submission gauntlet and write a source-linked JSON receipt:

```bash
python scripts/verify.py
```

## MCP tools

- `open_incident`
- `get_next_check`
- `record_observation`
- `propose_resolution`
- `verify_resolution`
- `incident_summary`

The read-only `sounding://incidents` resource exposes the retained evidence trails.

## Safety boundary

Sounding only supplies exterior or manufacturer-designated user checks. Hazard terms force a safety stop. The proof of concept does not provide internal electrical, gas, refrigeration, or disassembly instructions.

## License

Apache-2.0. See `LICENSE`.
