# Sounding scope

Sounding is an Alexa+ household diagnostician. It converts a vague symptom into a persistent evidence trail, asks one safe and useful question at a time, ranks known causes, proposes a bounded action, and records whether that action worked.

The proof of concept supports two complete scenarios: a dehumidifier that no longer collects water and a washing machine that bangs during spin. A deterministic safety gate stops the flow when the symptom mentions smoke, sparks, flames, a burning smell, gas, or electrical shock.

## Distinctive approach

The language model may translate conversation into tool calls. It never owns incident state, safety policy, cause ranking, check order, or outcome verification. Those behaviors live in an inspectable engine and are reproducible across models. This makes the product useful after a model update and testable without an LLM.

## Submission boundary

- MCP 2025-11-25 Streamable HTTP endpoint
- Persistent SQLite incident and observation store
- Six narrow tools plus one read-only MCP resource
- Browser-based Alexa+ simulation
- Two end-to-end household scenarios and a safety-stop demonstration
- Transport, safety, persistence, ranking, and resolution tests

Authentication, broad appliance coverage, sensor ingestion, manufacturer manuals, and production deployment remain outside the first proof of concept.

