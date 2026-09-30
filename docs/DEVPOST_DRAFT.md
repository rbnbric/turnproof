# Sounding

**Alexa+, help me find what actually changed.**

## Inspiration

Household problems rarely arrive as clean error codes. A person hears a new bang, notices that an appliance stopped collecting water, tries two things, leaves for work, and later explains a different version to someone else. Ordinary assistants answer the latest message. They do not preserve the experiment.

Sounding treats troubleshooting as an evidence problem. Alexa+ provides the natural, hands-free interaction while a deterministic engine retains what the household observed, chooses the next useful check, and records whether the eventual action worked.

## What it does

A user describes a symptom. Sounding opens a persistent incident and ranks known causes from explicit priors. It calculates the expected information gain of every remaining safe check, asks the most discriminating question, and updates the ranking with Bayes' rule after each answer.

The incident can be resumed in a later session without repeating checks. When the evidence supports a bounded action, Sounding proposes it and keeps the incident open until the user verifies the result. Hazard terms such as smoke, sparks, gas, or electrical shock bypass diagnosis and force a safety stop.

The proof of concept includes complete dehumidifier and washing-machine scenarios, a safety-stop path, retained incident history, and a browser-based Alexa+ simulation.

## How we built it

Sounding is a Python and FastAPI application with a self-hosted MCP server implementing protocol version 2025-11-25 over Streamable HTTP. Seven MCP tools expose the incident lifecycle, and a read-only MCP resource exposes retained evidence histories. SQLite keeps the state inspectable and portable.

The language model is allowed to interpret speech and select tools. It does not own safety policy, state transitions, Bayesian ranking, question selection, or outcome verification. Those decisions are deterministic and can be reproduced without an LLM.

We built a conformance gauntlet around that boundary. It checks source syntax, evidence behavior, MCP session and protocol behavior, origin validation, persistence, safety stops, and the browser contract. Each run emits a JSON receipt tied to a SHA-256 digest of the tested source.

## Challenges we ran into

Alexa+'s partner-only CLI, MCP Toolkit, and web simulator are unavailable to hackathon participants. We therefore implemented the open MCP transport directly and built a custom simulation around the real backend.

The deeper design challenge was avoiding a generic repair chatbot. A confident answer is weak evidence. Sounding needed persistent incidents, an explicit safety boundary, a mathematical reason for each next question, and a verification step after the recommendation.

Live browser testing also found an origin-validation rule that was correct on the default port but rejected the same local app on another port. We added the case to the transport suite before recording the final evidence receipt.

## Accomplishments that we're proud of

- A working MCP 2025-11-25 Streamable HTTP server
- Bayesian cause ranking and expected-information-gain question selection
- Incidents that survive server and browser sessions
- Explicit safety stops that cannot be overridden by model wording
- A complete path from vague symptom to verified or unresolved outcome
- A source-linked conformance receipt with all four gate families passing

## What we learned

Voice is useful because troubleshooting happens away from a keyboard, but conversation should not be the system of record. The durable product is the evidence trail.

We also learned that model resilience is an architectural choice. When safety, state, ranking, and verification are executable contracts, changing the conversational model changes the phrasing without silently changing the household's diagnostic policy.

## What's next

Next we would add signed manufacturer diagnostic packs, household asset identities, optional IoT sensor observations, timed checks, shared incidents for family members and technicians, and calibration data from verified outcomes. The same engine can then select experiments across many devices without turning the LLM into an unreviewable repair authority.

## Built with

Python, FastAPI, SQLite, MCP 2025-11-25, Streamable HTTP, JavaScript, HTML, CSS, unittest, Bayesian inference, information theory

