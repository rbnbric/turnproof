# Alexa+ track friction log

## 2026-09-30 — partner-only tooling looked like a prerequisite

**Task:** establish the supported local development path for an Alexa+ MCP submission.

**Steps attempted:** reviewed the Alexa+ setup material for the Category SDK,
MCP Toolkit, CLI, and web simulator, then searched the FAQ and organizer forum
for installation and access instructions.

**Expected:** a public quickstart leading from account setup to one locally
testable Alexa+ tool call.

**Actual:** the named tools are restricted to select partners. Their placement
in the setup material made them appear to be the expected participant path. The
FAQ and an organizer response eventually clarified that entrants should instead
build a self-hosted MCP server or custom simulation.

**Severity:** Important. Development was not blocked, but the ambiguity cost
research time and made it difficult to distinguish a required runtime from an
inaccessible preview tool.

**Workaround:** Turnproof implements MCP 2025-11-25 Streamable HTTP directly and
provides its own browser observatory backed by the real endpoint.

**Actionable suggestion:** put the access limitation and the two supported
participant paths at the top of every Alexa+ hackathon setup page: (1)
self-hosted MCP/Agent Skill and (2) custom simulation. Link the open MCP
transport requirements before introducing partner-only tooling.

References:

- <https://amazonappdev2026.devpost.com/details/faqs>
- <https://amazonappdev2026.devpost.com/forum_topics/45262-is-the-alexa-mcp-toolkit-alexa-ai-cli-available-to-hackathon-participants>

## 2026-09-30 — custom simulations lack a canonical minimum contract

**Task:** design a judgeable Alexa+ simulation that accurately represents the
implemented integration boundary.

**Steps attempted:** reviewed the track requirements and organizer clarification
for what a simulation must reproduce, whether voice is required, and which
parts of the backend must be real.

**Expected:** one small reference flow showing the minimum acceptable chain from
simulated user input through a structured call to a visible result.

**Actual:** organizers usefully confirmed that a simulation need not reproduce
Alexa+ visually, that voice is optional, and that the backend can be real while
the Alexa layer is simulated. That flexibility leaves entrants without a
canonical interaction target or checklist.

**Severity:** Nice-to-have. The project could proceed, but every team must
independently interpret the minimum credible simulation boundary.

**Workaround:** Turnproof labels its browser as a custom simulation and makes
every visible state transition correspond to a real MCP tool call. The README
states exactly which Alexa+ behaviors remain outside the proof of concept.

**Actionable suggestion:** publish a short reference example containing one
simulated utterance, its MCP tool call, a visual response, and a follow-up turn.
Keep visual styling and voice optional while making the behavioral boundary
explicit.

Reference:

- <https://amazonappdev2026.devpost.com/forum_topics/45058-clarification-on-simulated-alexa-web-experience-requirements>

## 2026-10-01 — no public conformance target for conversational state

**Task:** verify corrections, retries, stale approvals, and session changes
against an Alexa+ development target.

**Steps attempted:** mapped the available public MCP transport requirements and
searched the participant materials for a test client or replay fixture covering
multi-turn Alexa+ state behavior.

**Expected:** a public simulator or conformance fixture that accepts an MCP
endpoint and replays a small set of Alexa+-shaped interactions.

**Actual:** the open protocol is sufficient to test transport behavior, but the
participant path provides no public Alexa+ client for multi-turn correction and
retry scenarios.

**Severity:** Important for reliability-focused entries. Transport can be
verified locally, but Alexa+-specific integration behavior cannot be reproduced
without partner tooling.

**Workaround:** Turnproof separates the claims. Its generated laboratory attacks
the real MCP endpoint and deterministic state boundary; it makes no claim that
the custom browser reproduces production Alexa speech recognition or dialogue
routing.

**Actionable suggestion:** provide a public, versioned test client that can load
an MCP endpoint, display proposed structured calls, replay interruptions and
retries, and export a trace suitable for submissions and regression testing.
