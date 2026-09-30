# Demo video — 2:35 target

## 0:00–0:15 — the problem

**Picture:** Sounding title and empty evidence trail.

**Narration:** “A household problem rarely starts with a clean error code. It starts with: ‘Alexa, my dehumidifier is running, but it stopped collecting water.’ Most assistants answer once. Sounding preserves the experiment.”

## 0:15–0:42 — open an incident

**Picture:** Select the dehumidifier scenario. Hold on the ranked causes and incident ID.

**Narration:** “Sounding opens a persistent incident, applies explicit priors, and shows what it knows. It does not jump to a repair. It calculates which safe observation would reduce the most uncertainty.”

## 0:42–1:12 — evidence changes the next question

**Picture:** Answer ‘No’ to the bucket light, then answer the airflow question. Show the percentages and information-gain value change after each answer.

**Narration:** “Every answer updates the cause ranking with Bayes' rule. The next check is selected by expected information gain, not generated from conversational confidence. The visible evidence panel is the same state exposed through the MCP tools.”

## 1:12–1:35 — persistence

**Picture:** Reload the page. Choose the retained incident and resume it.

**Narration:** “Reload the browser or come back tomorrow. The incident remains. A family member can continue without repeating the first person's checks or rewriting the symptom from memory.”

## 1:35–1:55 — safety stop

**Picture:** Start a new safety-stop demo. Hold on the stopped state.

**Narration:** “Safety is executable policy. Smoke or a burning smell stops the diagnostic flow. A model cannot talk its way around that transition or substitute an internal repair instruction.”

## 1:55–2:15 — verify the result

**Picture:** Resume the first incident, propose the bounded action, select ‘That fixed it,’ and show resolved/verified.

**Narration:** “A recommendation is not the end. Sounding asks whether the action worked, then records the incident as verified or unresolved. Failed actions remain evidence for escalation.”

## 2:15–2:35 — show the implementation receipt

**Picture:** Brief split view of `server/mcp.py`, the test output, and `evidence/latest.json` showing 4/4.

**Narration:** “The backend is a self-hosted MCP 2025-11-25 server over Streamable HTTP. Deterministic tests cover the evidence engine, safety boundary, persistent state, protocol lifecycle, and browser contract. Sounding lets Alexa handle language while the evidence remains stable, inspectable, and reproducible.”

