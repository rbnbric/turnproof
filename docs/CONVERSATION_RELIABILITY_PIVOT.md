# Turnproof: a semantic firewall and adversarial laboratory for Alexa+

## North star

Turnproof makes consequential conversational software testable in the way web
applications, compilers, and databases are testable.

A developer declares what a conversation is allowed to mean: facts, constraints,
dependencies, corrections, unknowns, commitments, and invariants. Turnproof
compiles that contract into four connected artifacts:

1. a deterministic state reducer that owns current meaning;
2. a runtime firewall between probabilistic interpretation and application
   effects;
3. a shared voice/visual projection that cannot disagree about the current
   revision;
4. an adversarial conformance suite that attacks the actual MCP endpoint and
   retains a reproducible receipt.

The goal is larger than making one add-on robust. The goal is to establish a
missing engineering layer for voice agents: **conversation semantics as
executable infrastructure**.

Alexa+ is the first target because its MCP add-ons expose exactly the boundary
where generated language becomes structured intent and potentially becomes an
effect. The design is portable to other MCP clients and voice-agent runtimes.

## The specific opening

Adjacent products and research generally do one of these things:

- test whether a transcript sounds relevant or coherent, often by asking
  another model to grade it;
- hard-code a safe state machine for one application;
- protect a narrow consequential action with confirmation and idempotency.

Turnproof joins those isolated concerns into a development system. It asks a
harder question: if the words, order, transport, model, or session boundary
change while the user's intended meaning does not, can the application prove it
reached the same valid state? If the intended meaning changes, can it prove that
only the affected facts and consequences changed?

That gives Turnproof a role no public contest entry currently attempts: not one
more reliable agent, but machinery for compiling, enforcing, and falsifying the
meaning of multi-turn agent interactions from one contract.

This is a combination claim, not a claim that its components have never existed.
Rasa supports deterministic dialogue state and authored end-to-end conversation
stories. Microsoft and commercial test products evaluate multi-turn agents.
ServiceNow EVA applies audio perturbations to voice-agent evaluation. The
official MCP conformance suite tests protocol behavior. AgentAssert, Edictum,
and the AgentContract draft enforce behavioral or tool-use policies at runtime.
Academic VUI-testing work has used state models to generate voice-interface
tests.

Turnproof's narrower opening is to use one domain-semantic contract to generate
the reducer, runtime enforcement, model-based adversarial sequences, coverage
metrics, cross-modal projections, and reproducible MCP-endpoint receipts. The
competitive audit found strong precedents for every part except that complete
loop.

## One contract, four products

### 1. Conversation compiler

The input is a small declarative contract describing:

- facts and their types, admissible values, and provenance requirements;
- required, optional, derived, mutually exclusive, and dependent facts;
- whether a new value adds, replaces, clears, or conflicts with an old value;
- questions available to resolve ambiguity and their information value;
- actions, preconditions, consequence tiers, and confirmation policies;
- facts whose change invalidates a proposal or receipt;
- invariants that must hold at every revision;
- which fields must agree across voice and visual output.

The compiler produces a typed reducer, JSON Schemas for narrow domain tools,
state projections, and a model-based test graph. The generated code is an
inspectable starting point; the contract remains the source of truth.

### 2. Runtime semantic firewall

Alexa or another model may propose a tool call. The firewall converts it into a
candidate state patch, validates it against the compiled contract, and either:

- applies it as one revision;
- requests the smallest clarifying fact;
- records an explicit unknown without guessing;
- rejects a contradiction with a specific repair path;
- invalidates a stale proposal;
- deduplicates a retry; or
- blocks an effect whose preconditions or approval no longer match.

No model receives direct write authority. Domain code receives only a valid,
versioned transition.

### 3. Adversarial conversation laboratory

Turnproof generates and executes stateful sequences, rather than a list of
pleasant example prompts. The first attack families are:

- omitted required facts;
- facts arriving in different valid orders;
- correction after confirmation;
- correction that changes one field but accidentally resets another;
- contradiction within one turn or across turns;
- `unknown`, silence, timeout, and failed recognition confused with `no`;
- pronoun or referent ambiguity represented as competing candidates;
- interruption followed by a new transport session;
- duplicate, delayed, dropped, and reordered calls;
- retry after an ambiguous network outcome;
- proposal expiration and underlying state drift;
- two actors editing the same task concurrently;
- out-of-scope input and malformed tool calls;
- compact voice output disagreeing with the full visual projection;
- baseline/current model adapters producing different structured calls for
  semantically equivalent inputs.

This is model-based property testing. The oracle is the compiled semantic
contract, not an LLM's opinion of transcript quality.

### 4. Conversation observatory

The browser experience renders the live state graph rather than imitating a
chat application. It shows:

- the active facts at the current revision;
- superseded facts and the exact revision that replaced them;
- unresolved alternatives and why they remain ambiguous;
- commitments, their bound digest, and whether they are still valid;
- the path taken through the state graph;
- adversarial coverage by state, transition, correction, recovery, and
  consequence boundary;
- differential results between two server builds or interpretation adapters;
- deterministic replay from the retained receipt.

The user-facing MCP App is a small projection of this same record: what was
understood, what changed, what remains unknown, and what happens next.

## Ambitious research goals

Turnproof should establish metrics that voice-agent teams can actually act on:

- **semantic state coverage:** declared states and transitions exercised;
- **correction coverage:** mutable facts proven replaceable from each reachable
  state;
- **recovery coverage:** recoverable errors with an exercised path back to work;
- **commitment integrity:** effects whose approval, revision, and idempotency
  boundaries were tested;
- **metamorphic stability:** equivalent inputs and call orders that converge on
  the same semantic digest;
- **locality of change:** a correction changes only contractually dependent
  fields;
- **cross-modal parity:** voice and visual projections share a revision and agree
  on consequential values;
- **drift budget:** behavioral differences between a pinned baseline and a new
  model, schema, prompt, or server build;
- **minimum-clarification score:** whether the system asks for the smallest fact
  needed to proceed safely rather than restarting or interrogating the user.

These are not engagement metrics. They are falsifiable properties of an
interaction system.

## Competition proof

The submission must be a working Alexa+ experience as well as infrastructure.
The existing household diagnostician becomes one reference application compiled
through Turnproof. A second, structurally different fixture proves the engine is
general rather than a renamed appliance state machine.

The film starts with a smooth happy path, then attacks the same live endpoint:

1. correct a prior observation and show only its dependent diagnosis change;
2. inject silence and prove no false `no` was recorded;
3. interrupt and resume through a new MCP session;
4. race two edits and resolve the stale revision;
5. change evidence after a proposed action and show the action expire;
6. duplicate the valid effect call and show one write with two stable receipts;
7. switch from the household contract to the second fixture;
8. reveal the generated state graph and adversarial coverage;
9. replay the receipt against the same source digest;
10. change one schema or adapter version and show the differential gate catch a
    regression before deployment.

The headline is not “our demo survived.” It is “the contract generated the
attacks, the live endpoint survived them, and the receipt lets you reproduce
that claim.”

## Second fixture

Use a compact delegation workflow that is structurally unlike diagnosis. A user
creates a household handoff containing recipient, task, time window, constraints,
and acknowledgement policy. It exercises referents, revisions, schedule
constraints, confirmation, and one simulated delivery effect without importing
the diagnostic ranking engine.

Example:

> “Ask Sam to pick up the prescription after work—actually, Jordan, and only if
> the pharmacy confirms it is ready.”

The reference app must retain the distinction between changing the recipient,
adding a precondition, and authorizing delivery. All people, messages, and
providers are fictional fixtures; no real message is sent.

## Stretch system

If access and time permit, add adapters that run one utterance corpus through
two interpretation systems and compare their candidate patches. The firewall's
verdict remains deterministic. A model update can then be evaluated by the
semantic differences it produces rather than by subjective transcript scoring.

Further stretch work:

- a proxy that imports `tools/list` from an existing MCP endpoint and wraps its
  mutating tools with contract enforcement;
- automatic candidate invariants inferred from schemas but requiring developer
  acceptance before becoming authoritative;
- audio perturbation fixtures for the custom simulator, clearly separated from
  claims about production Alexa ASR;
- responsive screenshot checks for Echo Show-sized, mobile, web, and voice-only
  projections;
- CI annotations that link a failing generated sequence to the smallest
  reproducible state path.

## Reference product thesis

Turnproof is an Alexa+ household-diagnosis add-on that remains correct when a
real conversation becomes messy. A user can begin with partial information,
correct an earlier answer, leave and resume later, reject a misunderstood
observation, or retry after a network failure without silently corrupting the
incident.

The reference experience is backed by the Turnproof compiler, firewall, and
laboratory. It exists to prove that the infrastructure improves a real Alexa+
interaction, not to define the scope of the platform.

The model may interpret language and propose a structured change. Deterministic
code validates and applies that change. The model never owns durable state,
supersession, commitment authority, or the pass/fail verdict.

## Honest platform boundary

Alexa+ owns speech, conversational routing, tool selection, historical
conversation context, verbal responses, and resumption after interruptions.
An MCP add-on cannot replace or intercept Alexa's global dialogue manager.

Turnproof can control and verify:

- the MCP tools and their schemas;
- the add-on's persistent task state;
- whether an observation adds, replaces, or leaves a value unchanged;
- the difference between `yes`, `no`, `unknown`, no input, and unsupported
  input;
- the minimum information required before an action can be proposed;
- whether a proposed action is still valid after evidence changes;
- idempotency under retries;
- the structured data Alexa uses to speak and render the result;
- an MCP App view that shows the current interpretation and recent changes;
- endpoint-level multi-turn conformance.

The simulator can demonstrate language variants and interruptions, but it must
not claim to validate Alexa ASR, Alexa's production phrasing, or production
device behavior unless those surfaces are actually exercised.

## The user-facing promise

> Correct me. Interrupt me. Come back tomorrow. I will show what I understood
> and will not act on an obsolete version of it.

The visible interface answers four questions at every consequential turn:

1. What did I understand?
2. What changed?
3. What is still unknown?
4. What happens next?

This is more useful than a transcript. A transcript records words; Turnproof
records the current meaning, the revisions that produced it, and the boundary
between a suggestion and a commitment.

## Reference journey

The existing dehumidifier scenario becomes the main demonstration.

1. **Partial start.** “The dehumidifier runs, but the bucket stays dry.” The
   add-on opens an incident, records only supported facts, and asks the one safe
   question with the highest expected information gain.
2. **Ordinary answer.** The user says the bucket light is off. The evidence card
   records `bucket_light = no`, advances its revision, and recalculates causes.
3. **Correction.** “Actually, the light is on. I was looking at the timer.” The
   current value becomes `yes`; the former value remains in revision history but
   no longer contributes to the diagnosis. The card explicitly shows
   `bucket light: no -> yes`.
4. **Non-answer.** Silence, a failed recognition, or “I can't tell” records no
   false observation. `unknown` is explicit and distinct from `no`.
5. **Interruption and resume.** A new MCP session requests the incident. The
   current interpretation, revision, unanswered checks, and next safe question
   return without replaying old questions.
6. **Stale proposal.** The engine proposes a bounded action against revision 4.
   A later correction changes relevant evidence to revision 5. Attempting to
   accept the old proposal fails with `STATE_CHANGED` and returns a revised
   proposal.
7. **Retry.** The same verification request is delivered twice. Its idempotency
   key produces one state transition and the same receipt twice.
8. **Recoverable error.** An unsupported or malformed observation returns a
   specific correction path and preserves the valid state.

The washing-machine scenario proves that the machinery is not hard-coded to one
conversation.

## Runtime contract

Every incident has a monotonic revision. Every accepted mutation records:

- incident ID;
- revision before and after;
- field/check ID;
- previous and current value;
- operation: `add`, `replace`, `clear`, or `no_change`;
- source turn/call identifier;
- timestamp;
- optional interpretation confidence as metadata only;
- state digest after the mutation.

Every proposed consequential action binds to:

- incident ID and current revision;
- the evidence digest;
- exact action identifier and parameters;
- expiration;
- one idempotency scope.

If the revision or digest changes, the proposal expires. The response explains
which fact changed and offers the next valid step. It never substitutes the new
proposal silently.

## MCP surface

Keep tools narrow and intent-specific, in line with Alexa+'s schema guidance:

- `open_incident`
- `answer_check`
- `correct_check`
- `skip_check`
- `get_next_check`
- `review_incident`
- `propose_resolution`
- `accept_resolution`
- `verify_resolution`
- `resume_incident`

The reusable layer lives below those domain tools. It is a library, not one
generic “do conversation” tool. That keeps tool meanings distinct and makes the
schemas useful to Alexa's selection process.

Tool results use a shared envelope:

```json
{
  "status": "needs_input",
  "revision": 5,
  "understood": {},
  "changed": [],
  "still_needed": [],
  "next": {},
  "recovery": null,
  "state_digest": "sha256:..."
}
```

The envelope is self-contained so voice-only Alexa surfaces remain intelligible.
The optional MCP App uses the same fields rather than maintaining a second truth.

## Conversation conformance pack

The test author declares invariants, not preferred prose. Initial gates:

1. **Partial input:** missing data leads to a bounded request for the smallest
   useful next fact, not an invented default.
2. **Correction:** the new value supersedes the old value exactly once.
3. **No-input integrity:** silence, timeout, and recognition failure do not
   become `false`, `no`, or an empty committed value.
4. **Unknown integrity:** “I don't know” is preserved as unknown and remains
   revisable.
5. **Resume:** a fresh protocol session reconstructs the same semantic state and
   next step.
6. **Stale-action rejection:** any relevant correction invalidates an older
   proposal.
7. **Retry idempotency:** duplicate mutation or commitment calls produce one
   effect and stable receipts.
8. **Order robustness:** independent facts can arrive in different orders and
   converge on the same current state.
9. **Error recovery:** malformed and out-of-scope calls leave the last valid
   state intact and provide a path forward.
10. **Voice/visual parity:** the structured spoken summary and rendered card are
    derived from the same revision and digest.

The runner executes each sequence through the actual MCP transport, captures
calls, responses, revisions, and source digest, and writes deterministic JSON.
No LLM grades whether the conversation “felt right.” Optional model adapters may
be tested separately for utterance-to-tool interpretation, but they cannot
change the state-machine verdict.

## UX

The MCP App is a compact evidence card, not a chat transcript.

- **Current understanding** shows only active facts.
- **Changed this turn** highlights replacements for one turn, then moves them to
  history.
- **Still unknown** exposes gaps without implying failure.
- **Next safe check** gives one instruction suitable for voice-only use.
- **Revision/receipt** is subdued but inspectable for the demo and developers.

Inline mode handles a single question, correction, or confirmation. Fullscreen
mode handles incident review and revision history. The voice summary names the
same changed values, quantities, and status visible on screen.

## Competitive separation

The live contest entries contain adjacent pieces:

- HERMX ProofGate proves exact approval and stale-state rejection for a study
  coach and includes an MCP endpoint harness.
- Show, Don't Tell keeps a revised travel plan visible in one card.
- Ripple proves interruption recovery, approval binding, and idempotent repair
  execution.
- Understudy distinguishes missing evidence from missing policy.

Turnproof should not claim those pieces as novel by themselves. Its distinct
contribution is turning conversational semantics into a reusable executable
contract, generating adversarial multi-turn sequences from that contract, and
showing the same machinery inside a complete consumer add-on. None of the 20
public submissions reviewed on 2026-09-30 presents that combination.

## Why this scores better than the current build

- It remains a complete Alexa+ experience rather than a testing dashboard.
- It directly implements Amazon's published test advice for partial requests,
  mid-flow corrections, errors, voice/visual agreement, and cross-session task
  completion.
- It demonstrates context-aware state across sessions, an MCP App, and agentic
  workflow behavior rather than a single-turn wrapper.
- The failure sequences are visually obvious in a short demo.
- The compiler, firewall, laboratory, and coverage model are a credible
  open-source developer product rather than a few reusable test helpers.
- The existing MCP transport, SQLite persistence, deterministic diagnosis,
  information-gain selection, browser shell, and source-linked verification
  remain useful.

## Build boundary

For the competition build:

- refactor incident storage into revisioned events plus materialized current
  state;
- add correction, unknown/no-input, proposal binding, and idempotency behavior;
- return the shared result envelope from every domain tool;
- replace the current evidence panel with the four-part understanding card;
- build the adversarial sequence runner and source-linked receipt;
- demonstrate the same suite against both diagnostic scenarios;
- retain a clearly labelled Alexa+ simulator unless production access becomes
  available;
- do not claim Alexa ASR, device rendering, global Alexa memory, or production
  Alexa integration without direct evidence.

Defer general contract authoring UI, arbitrary third-party add-on wrapping,
production authentication, cloud deployment, and device-matrix automation until
the reference implementation and conformance receipt are complete.

## Demo spine

1. “Assistants sound smooth until the user says, ‘Actually…’”
2. Show the initial answer and ranked evidence.
3. Correct it; hold on the visible `no -> yes` revision and changed diagnosis.
4. simulate no-input and prove that nothing was recorded;
5. start a fresh session and resume;
6. invalidate a stale proposed action;
7. retry a valid action and show one effect/two identical receipts;
8. reveal the conformance matrix passing against the same live endpoint;
9. close on: “Alexa handles the conversation. Turnproof proves the meaning
   survived it.”

## Sources

- [Alexa+ MCP client and app lifecycle](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-client-lifecycle.html)
- [Alexa+ tools, schema, and data design](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-addon-tools-schema-data-design.html)
- [Alexa+ customer-experience testing guide](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-addon-test-addon-cx.html)
- [Alexa+ MCP design overview](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-addon-design-guide-overview.html)
- [Hackathon rules and judging guidance](https://amazonappdev2026.devpost.com/rules)
- [Official MCP conformance framework](https://github.com/modelcontextprotocol/conformance)
- [Rasa end-to-end conversation testing](https://legacy-docs-oss.rasa.com/docs/rasa/testing-your-assistant/)
- [ServiceNow EVA voice-agent evaluation](https://github.com/ServiceNow/eva)
- [AgentAssert behavioral contracts](https://github.com/qualixar/agentassert-abc)
- [Edictum runtime tool governance](https://github.com/edictum-ai/edictum)
- [AgentContract draft specification](https://github.com/agentcontract/spec/blob/main/SPEC.md)
