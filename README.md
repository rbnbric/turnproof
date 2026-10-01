# Turnproof

**Conversation is probabilistic. Meaning does not have to be.**

Turnproof is a semantic firewall and adversarial laboratory for Alexa+ add-ons.
It compiles a conversational contract into revisioned state rules, protects
effects from stale or ambiguous state, and generates multi-turn attacks against
the same contract.

The proof of concept includes two structurally different contracts:

- a household diagnosis that retains evidence and accepts corrections;
- a household handoff with a recipient, task, time window, and precondition.

Both use the same reducer, revision ledger, semantic digest, proposal boundary,
idempotent receipts, and generated laboratory.

## Run

Requires Python 3.11+.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The MCP endpoint is
`http://127.0.0.1:8000/mcp` and implements protocol version `2025-11-25` over
Streamable HTTP.

## Observatory walkthrough

1. Start the diagnosis.
2. Record “no,” then correct it to “yes.” The active meaning changes while both
   revisions remain visible.
3. Bind an action to the current revision and digest.
4. Change another piece of evidence.
5. Try the stale action. The runtime returns `STATE_CHANGED` without producing
   the simulated effect.
6. Switch to the handoff contract to demonstrate reuse.
7. Run all attacks. The browser displays the generated results from the live
   `/api/turnproof/lab` endpoint.

Append `?video=1` to run the paced, captioned submission walkthrough. The
reproducible capture utility is `scripts/record_demo.py`; its optional packages
are pinned in `requirements-video.txt`, and the narration is retained in
`scripts/demo_narration.txt`.

## Verify

```bash
python -m unittest discover -v
python scripts/run_lab.py
python scripts/verify.py
```

The current suite contains 24 direct tests and 16 generated adversarial checks
across the two contracts. The six-gate verifier retains a JSON receipt in
`evidence/latest.json`, tied to a SHA-256 digest of the tested source.

Generated checks currently cover:

- partial input and minimum clarification;
- explicit unknown values;
- correction supersession;
- mutation and effect retry idempotency;
- stale action rejection;
- concurrent stale-write rejection;
- semantic convergence when independent facts arrive in different orders.

## MCP tools

Turnproof tools:

- `start_turnproof_diagnosis`
- `start_turnproof_handoff`
- `revise_turnproof_fact`
- `review_turnproof_conversation`
- `propose_turnproof_action`
- `commit_turnproof_action`

The original diagnostic tools remain during migration so the existing Bayesian
reference engine and its safety tests continue to run.

## Trust boundary

Alexa+ owns speech recognition, conversational routing, tool selection, and its
verbal response. Turnproof begins where that probabilistic interpretation
becomes a proposed structured change.

The model may propose a tool call. Deterministic code owns validation, current
meaning, correction history, optimistic concurrency, proposal invalidation,
idempotency, and the test verdict. The browser is a clearly labelled custom
simulation; this repository does not claim a completed production Alexa+ device
session.

## License

Apache-2.0. See `LICENSE`.
