# Turnproof — Devpost project story

## Inspiration

Voice interfaces are easy to demonstrate and difficult to trust. A polished
conversation can conceal a damaged state: silence recorded as “no,” a correction
that leaves an old answer active, a retry that performs the same action twice,
or an approval that remains usable after the underlying facts have changed.

The language model is usually blamed when this happens, but changing prompts or
models does not solve the engineering problem. Language interpretation is
probabilistic. Durable state, corrections, commitments, and effects need firmer
rules.

Turnproof grew from a question: what would conversational software look like if
we treated meaning as executable infrastructure? Instead of testing only a few
pleasant transcripts, could we declare what a conversation is allowed to mean,
generate attacks from that declaration, and preserve a reproducible receipt of
the result?

Alexa+ provides a useful boundary for that experiment. Its MCP add-ons connect
natural conversation to structured tools. Turnproof protects the point where a
model's interpretation becomes persistent state or an application effect.

## What it does

Turnproof is a semantic firewall and adversarial laboratory for conversational
applications.

A developer defines a conversation contract: its facts, types, dependencies,
required information, allowed corrections, actions, and action preconditions.
Turnproof compiles that declaration into runtime rules and generated multi-turn
checks.

The current proof of concept includes two different contracts:

1. A household diagnosis that accepts partial evidence and later corrections.
2. A household handoff containing a recipient, task, time window, precondition,
   and acknowledgement policy.

Both contracts use the same semantic engine. The engine distinguishes an
explicit unknown from “no,” records every accepted change as a revision,
preserves superseded values, and creates a digest of the current meaning.

Before an action can occur, Turnproof creates a reviewable proposal bound to
that exact revision and digest. If any relevant state changes afterward, the
old proposal is rejected with `STATE_CHANGED`. Successful effects return stable
idempotent receipts, so a network retry cannot silently perform the same action
twice.

The browser observatory makes this visible without pretending to be a chat
window. It displays:

- the facts currently understood;
- the revision ledger and corrected values;
- the semantic digest to which an action is bound;
- the runtime verdict when state changes;
- every generated adversarial check and its result.

The guided demonstration records “no,” corrects it to “yes,” binds an action,
changes another fact, and then attempts the stale action. The runtime blocks it.
The same screen reports the laboratory result: **16 of 16 generated attacks
passing across both contracts**.

## How we built it

Turnproof is a dependency-light Python application built with FastAPI, SQLite,
the Model Context Protocol, standard-library `unittest`, and a plain
HTML/CSS/JavaScript observatory.

The semantic engine owns state. Each conversation has a monotonically increasing
revision, and each mutation carries an expected revision and an idempotency key.
A mutation batch is atomic: either every valid change becomes one revision or
none of it does. A reused idempotency key must describe the same operation; it
cannot conceal a different mutation.

Corrections are append-only events. The active projection shows the newest
meaning, while the ledger preserves what it replaced. This gives the voice and
visual layers one source of truth without asking the language model to remember
which statement won.

Actions use a two-step boundary:

1. `propose_turnproof_action` validates the contract and binds the proposal to
   the current revision and semantic digest.
2. `commit_turnproof_action` verifies that the binding is still current and
   returns one stable effect receipt.

The adversarial laboratory is generated from the same compiled contracts. It
checks partial input, explicit unknowns, correction supersession, mutation
retries, effect retries, concurrent stale writes, stale action rejection, and
convergence when independent facts arrive in different orders.

We also retained the earlier deterministic diagnosis engine as a reference
subsystem. This prevents the pivot to a general semantic layer from erasing its
existing safety and evidence tests.

The repository has three levels of evidence:

- **24 direct unit and integration tests** for contracts, state, MCP transport,
  diagnosis behavior, retries, and concurrency;
- **16 generated adversarial checks** across two contracts;
- **6 independent conformance gates** that run syntax, contract tests, the
  generated laboratory, the reference engine, MCP transport, and the browser
  contract.

The gate runner records bounded output, duration, exit status, and a SHA-256
digest of the tested source in a reproducible JSON receipt.

## Challenges we ran into

The hardest problem was deciding where determinism belongs. An Alexa+ add-on
cannot replace Alexa's speech recognition, global dialogue manager, or choice
of words. Claiming otherwise would make the project sound more powerful while
making the result less credible.

We placed the boundary at the MCP tool call. The model may interpret language
and propose a structured change. Turnproof decides whether that change is valid,
whether it conflicts with a newer revision, and whether it may produce an
effect.

Corrections exposed another subtle problem. Updating the latest value is not
enough; the system must retain which value was superseded and ensure that an
action approved under the previous meaning cannot survive the correction.
Binding proposals to both a revision and a semantic digest made that property
explicit and testable.

Retries also required care. Returning the previous result for every repeated
key appears idempotent, but it is unsafe if the caller reuses that key for a
different mutation. Turnproof therefore compares the request identity as well
as the key and rejects conflicting reuse.

Finally, we wanted tests that did not merely restate the implementation. The
most useful checks describe properties: independent fact order should converge,
unknown must not become false, stale writes must fail, and a committed effect
must have one stable receipt. These properties can survive changes to the code
and to the model interpreting the conversation.

## Accomplishments that we're proud of

The strongest result is a complete, inspectable failure boundary:

- **24/24 direct tests pass**;
- **16/16 generated conversational attacks pass**;
- **6/6 conformance gates pass**;
- corrections remain visible without leaving obsolete meaning active;
- stale approvals are rejected before the simulated effect;
- retries return stable receipts and conflicting key reuse is blocked;
- two structurally different contracts run through the same engine;
- the evidence receipt is tied to the exact tested source.

We are also proud that the interface shows the proof directly. A judge does not
have to accept a completion claim or inspect a wall of logs. The current meaning,
revision history, stale-action verdict, and adversarial results share one screen.

## What we learned

Conversational correctness is a state-management problem as much as a language
problem.

Better prompts can improve interpretation, but they cannot provide atomic
updates, optimistic concurrency, idempotent effects, or an authoritative
correction ledger. Those properties belong in ordinary inspectable code.

We also learned that the contract is most useful when it drives both runtime
behavior and testing. If the runtime rule and the test oracle are maintained as
unrelated prose, they can drift apart. A shared declaration lets a new contract
inherit the same attack families and makes missing rules easier to see.

The broader lesson is that model drift does not have to become application
drift. Models, prompts, and phrasing may change while the deterministic boundary
continues to enforce the same meaning and effect rules.

## What's next for Turnproof

The next milestone is a production Alexa+ integration using the existing MCP
tools, followed by a recorded device or simulator walkthrough. The current
browser experience is an explicitly labelled custom simulation backed by the
real self-hosted MCP endpoint.

We also plan to:

- load contracts from external declarative files rather than Python fixtures;
- generate narrow JSON Schemas and more attack families from each contract;
- compare two model or prompt versions by the semantic patches they propose;
- add interruption, delayed-call, and transport-reordering scenarios;
- render voice and visual projections from the same revision;
- publish retained receipts in continuous integration;
- wrap existing MCP tools so teams can add a Turnproof boundary without
  rebuilding their entire application.

The long-term goal is to make consequential conversation testable like any other
software interface: declare the contract, attack the boundary, inspect the
evidence, and refuse effects that no longer match what the user meant.

## Built with

Use these Devpost tags:

`Alexa+`, `Python`, `FastAPI`, `Model Context Protocol`, `MCP`, `SQLite`,
`JavaScript`, `HTML`, `CSS`, `JSON`, `unittest`, `JSON Schema`,
`Deterministic Testing`, `Model-Based Testing`, `Property Testing`,
`Concurrency Control`, `Idempotency`, `Developer Tools`, `AI-Assisted Development`

## Try it out links

**Source code and local demo:** https://github.com/rbnbric/turnproof

The repository contains the observatory, MCP endpoint, verification commands,
generated laboratory, source-linked evidence receipt, and the rendered
submission walkthrough at `evidence/turnproof-demo.mp4`. Use the uploaded
YouTube copy of that walkthrough for Devpost's required Video Demo Link.

## Suggested gallery captions

1. **One screen shows the complete proof: current meaning, correction history,
   a stale-action verdict, and 16 generated attacks passing across two contracts.**
2. **Every correction creates a revision. Superseded answers remain inspectable
   while only the latest valid meaning drives the application.**
3. **Actions are bound to an exact revision and semantic digest. Change the
   facts and Turnproof rejects the old approval before any effect occurs.**
4. **The conformance runner records six independent gates and a source-linked
   JSON receipt instead of relying on a completion claim.**
