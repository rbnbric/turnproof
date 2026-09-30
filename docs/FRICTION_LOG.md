# Alexa+ track friction log

## 2026-09-30 — gated tooling looked like a prerequisite

The Alexa+ setup material referenced the Category SDK, MCP Toolkit, CLI, and web simulator, but those tools are restricted to select partners. The hackathon FAQ and an organizer response clarified that participants cannot obtain access and should build a self-hosted MCP server or their own simulation.

**Cost:** research time was spent attempting to distinguish required runtime technology from inaccessible preview tooling.

**Workaround:** Sounding implements the open MCP 2025-11-25 Streamable HTTP specification directly and provides its own browser simulation.

**Suggested improvement:** put the access limitation and the two supported participant paths at the top of every Alexa+ hackathon setup page: (1) self-hosted MCP/Agent Skill, and (2) custom simulation. Link the open MCP transport requirements before mentioning partner-only tooling.

References:

- <https://amazonappdev2026.devpost.com/details/faqs>
- <https://amazonappdev2026.devpost.com/forum_topics/45262-is-the-alexa-mcp-toolkit-alexa-ai-cli-available-to-hackathon-participants>

## 2026-09-30 — a custom simulator has no canonical interaction target

An organizer confirmed that a simulation does not need to reproduce Alexa+ visually, voice is optional, and the backend can be real while the Alexa layer is simulated. That flexibility is useful, but it leaves entrants without a concrete minimum interaction contract.

**Workaround:** the Sounding simulator shows a conversational turn beside the actual persisted evidence, so every visible transition corresponds to a real MCP tool behavior.

**Suggested improvement:** publish one short reference flow showing a simulated utterance, tool call, visual response, and follow-up turn. Keep visual styling optional.

Reference:

- <https://amazonappdev2026.devpost.com/forum_topics/45058-clarification-on-simulated-alexa-web-experience-requirements>
