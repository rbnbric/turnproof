# Judging alignment

## Technical implementation

The runtime is a self-hosted MCP 2025-11-25 server over Streamable HTTP. Tests cover initialization, negotiated-version headers, secure sessions, origin validation, notifications, GET behavior, deletion, persistence, safety stops, ranking, and verified resolution.

## Design

Voice drives the inspection while a glanceable evidence panel shows retained observations, ranked causes, and the next safe check. The interface avoids a generic chat dashboard: conversation is temporary; the evidence trail is the product.

## Potential impact

People frequently describe household failures vaguely and lose the details between attempts, family members, and service calls. Sounding creates a structured record that can shorten diagnosis, prevent repeated checks, and make escalation more useful.

## Quality of idea

The LLM performs language interpretation and tool selection. Deterministic code owns safety, persistent state, ranking, and verification. This division keeps the core behavior stable when prompts or models change and makes every recommendation reproducible from its evidence.

