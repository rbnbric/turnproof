# Devpost additional information

## Upload a file

Upload `turnproof-judging-evidence.zip`. It contains the source-linked
verification receipt, gallery frame, narrated demo, friction log, and project
story. The complete source remains in the public GitHub repository.

## Submitter identity

- **Submitter Type:** Organization
- **Organization Name:** Armada Ventures LLC
- **Submitter Country of Residence:** select Robin's actual country of residence
- **Canadian province:** `N/A` unless Robin resides in Canada

## Competition fields

- **Primary Track:** Alexa+
- **Code repository:** https://github.com/rbnbric/turnproof
- **New or existing before August 31, 2026:** New
- **Existing-project update explanation:** leave blank; the project is new

## AWS Builder Mini Challenge

- **Submitting:** No
- **AWS services incorporated:** `N/A — Turnproof does not use AWS services in this submission.`

## Open Source Mini Challenge

- **Submitting:** Yes
- **Contribution URL:** https://github.com/rbnbric/turnproof/commits/master/
- **Project Repository URL:** https://github.com/rbnbric/turnproof
- **GitHub Username:** `rbnbric`

### Description of what you did, how it works, and why it matters

Turnproof is a new Apache-2.0 semantic firewall and adversarial laboratory for
conversational applications. It was created during the hackathon and published
with its complete source, tests, documentation, evidence, and reproducible demo
tools.

Developers define conversational facts, dependencies, corrections, actions, and
preconditions as a contract. Turnproof applies proposed changes through a
revisioned deterministic reducer, preserves superseded values, binds actions to
the exact semantic digest that was approved, rejects stale writes and actions,
and returns idempotent effect receipts. The same contracts generate multi-turn
attacks for partial input, unknown values, corrections, retries, concurrency,
and order convergence.

This matters because a model can produce fluent dialogue while silently
corrupting durable state. Turnproof provides an inspectable open-source boundary
between probabilistic interpretation and consequential application effects.
The current release passes 24 direct tests, 16 generated adversarial checks,
and 6 source-linked conformance gates.

## Optional feature requests

**Critical — public Alexa+ MCP test client and replay format.** Provide an
ungated browser or CLI that can connect to a self-hosted MCP endpoint, show the
structured calls Alexa+ proposes, replay corrections, interruptions, retries,
and session changes, and export a versioned trace. This would let teams test the
same interaction boundary locally and distinguish MCP server defects from
simulator differences.

**Important — one canonical custom-simulation example.** Publish a minimal
reference flow containing a simulated utterance, tool call, rendered response,
and follow-up turn, with an explicit checklist of what judges expect to be real.

## Optional friction log

https://github.com/rbnbric/turnproof/blob/master/docs/FRICTION_LOG.md

## Optional project testing link

https://github.com/rbnbric/turnproof/blob/master/evidence/latest.json

## Feedback Question 1: tools, APIs, and SDKs used

We implemented the public Model Context Protocol 2025-11-25 Streamable HTTP
interface as a self-hosted Alexa+ add-on boundary. Python and FastAPI provide
the MCP and browser endpoints; SQLite stores revisioned semantic state;
standard-library unittest drives direct tests; HTML, CSS, and JavaScript render
the custom observatory. We also used GitHub for the public Apache-2.0 repository
and retained evidence. We did not use the partner-only Alexa MCP Toolkit, Alexa
AI CLI, Category SDK, or an AWS service.

## Feedback Question 2: what worked well

The organizer clarification that a self-hosted MCP endpoint and custom
simulation are acceptable made an open participant path possible. MCP's narrow
JSON tool boundary works well for separating model interpretation from
deterministic application policy. FastAPI made the Streamable HTTP transport and
same-origin browser surface straightforward, while SQLite provided portable,
inspectable transactions for revisions and idempotency. The Devpost FAQ and
organizer forum answers were useful once found, especially their honest
clarification of restricted tooling.

## Feedback Question 3: what needs work

The public onboarding material needs to distinguish partner-only Alexa+ tools
from the supported hackathon path much earlier. The Category SDK, MCP Toolkit,
CLI, and web simulator appear central before participants learn that they cannot
access them. There is also no public Alexa+ test client or canonical minimum
simulation, so teams must invent their own interaction target and cannot replay
Alexa+-specific corrections, retries, or session behavior. A versioned public
simulator, structured-call inspector, and trace export would close the largest
testing gap.

## Feedback Question 4: onboarding experience

Getting from zero to a working MCP endpoint required more research than coding.
We first had to determine whether the prominently documented tools were required
and why they were unavailable. The FAQ and organizer forum eventually clarified
that self-hosted MCP and a custom simulation are valid; after that, implementing
the open transport was direct. A single ungated quickstart should lead with that
path, provide one runnable endpoint and follow-up turn, then identify the
partner-only tools as optional previews rather than prerequisites.

## Feedback Question 5: build with these services again?

**Yes.** Alexa+ and MCP create a useful boundary for conversational products:
natural language can remain flexible while application state and effects stay
inspectable. We would build with this approach again. A public Alexa+ simulator,
an ungated quickstart, and replayable integration traces would substantially
improve confidence and reduce onboarding time.
