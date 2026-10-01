const elements = Object.fromEntries([
  'contract', 'revision', 'digest', 'verdict', 'facts', 'needed', 'history', 'score', 'checks', 'trace',
  'start-diagnosis', 'answer-no', 'correct-yes', 'propose', 'cause-drift', 'commit-stale',
  'start-handoff', 'run-lab', 'reset'
].map(id => [id, document.getElementById(id)]));
elements['demo-cue'] = document.getElementById('demo-cue');
elements['demo-cue-text'] = document.getElementById('demo-cue-text');

let current = null;
let proposal = null;
let traceCounter = 0;

async function tool(name, args) {
  const response = await fetch(`/api/tools/${name}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(args)
  });
  const result = await response.json();
  if (result.isError) {
    const error = new Error(result.structuredContent?.message || result.content?.[0]?.text || 'Tool failed');
    error.code = result.structuredContent?.code || 'ERROR';
    throw error;
  }
  return result.structuredContent;
}

function addTrace(label, message, kind = '') {
  const item = document.createElement('li');
  if (kind) item.className = kind;
  const time = document.createElement('time');
  time.textContent = `${String(++traceCounter).padStart(2, '0')} / ${label}`;
  const text = document.createElement('p'); text.textContent = message;
  item.append(time, text); elements.trace.append(item);
  elements.trace.scrollTop = elements.trace.scrollHeight;
}

async function render(data) {
  current = data;
  elements.contract.textContent = data.contract_id.replaceAll('_', ' ').toUpperCase();
  elements.revision.textContent = String(data.revision).padStart(2, '0');
  elements.digest.textContent = data.state_digest.slice(7, 25).toUpperCase();
  elements.verdict.textContent = 'VALID';
  elements.verdict.dataset.state = 'valid';
  const entries = Object.entries(data.understood);
  elements.facts.replaceChildren(...(entries.length ? entries.map(([name, value]) => {
    const row = document.createElement('div');
    const term = document.createElement('dt'); term.textContent = name.replaceAll('_', ' ');
    const description = document.createElement('dd'); description.textContent = String(value);
    row.append(term, description); return row;
  }) : [Object.assign(document.createElement('div'), {className: 'empty', textContent: 'No facts committed.'})]));
  const gaps = [...data.still_needed, ...data.unknown.map(name => `${name} (unknown)` )];
  elements.needed.textContent = gaps.length ? gaps.join(' · ') : 'No required gaps';
  await renderHistory(data.conversation_id);
  updateControls();
}

async function renderHistory(conversationId) {
  const response = await fetch(`/api/turnproof/conversations/${conversationId}/history`);
  const data = await response.json();
  elements.history.replaceChildren(...(data.events?.length ? data.events.slice().reverse().map(event => {
    const item = document.createElement('li');
    const head = document.createElement('div');
    const revision = document.createElement('b'); revision.textContent = `R${String(event.revision).padStart(2, '0')}`;
    const operation = document.createElement('span'); operation.textContent = event.operation.toUpperCase();
    const field = document.createElement('code'); field.textContent = event.field.replaceAll('_', ' ');
    head.append(revision, operation, field);
    const change = document.createElement('p');
    change.textContent = `${displayValue(event.previous)} → ${displayValue(event.current)}`;
    item.append(head, change); return item;
  }) : [Object.assign(document.createElement('li'), {className: 'empty', textContent: 'No mutations yet.'})]));
}

function displayValue(value) {
  if (!value) return '∅';
  if (value.status === 'unknown') return 'UNKNOWN';
  return String(value.value);
}

function updateControls() {
  const diagnosis = current?.contract_id === 'household_diagnosis_v1';
  elements['answer-no'].disabled = !diagnosis || 'bucket_light' in current.understood;
  elements['correct-yes'].disabled = !diagnosis || current?.understood.bucket_light !== 'no';
  elements.propose.disabled = !diagnosis || current?.understood.bucket_light === undefined || Boolean(proposal);
  elements['cause-drift'].disabled = !proposal;
  elements['commit-stale'].disabled = !proposal;
}

elements['start-diagnosis'].addEventListener('click', async () => {
  proposal = null;
  const data = await tool('start_turnproof_diagnosis', {
    scenario: 'dehumidifier', symptom: 'It runs, but the bucket stays dry.'
  });
  await render(data);
  addTrace('OPEN', 'Partial diagnosis accepted. Missing facts remain visible; no defaults were invented.');
});

elements['answer-no'].addEventListener('click', async () => {
  const data = await tool('revise_turnproof_fact', {
    conversation_id: current.conversation_id, expected_revision: current.revision,
    idempotency_key: `bucket-no-${current.revision}`, field: 'bucket_light', operation: 'set', value: 'no'
  });
  await render(data); addTrace('ADD', 'bucket_light = no was added at one atomic revision.');
});

elements['correct-yes'].addEventListener('click', async () => {
  const data = await tool('revise_turnproof_fact', {
    conversation_id: current.conversation_id, expected_revision: current.revision,
    idempotency_key: `bucket-yes-${current.revision}`, field: 'bucket_light', operation: 'set', value: 'yes'
  });
  await render(data); addTrace('CORRECT', 'The active value changed from no to yes. The earlier answer remains only in the ledger.', 'attention');
});

elements.propose.addEventListener('click', async () => {
  proposal = await tool('propose_turnproof_action', {
    conversation_id: current.conversation_id, action: 'accept_resolution', parameters: {fixture: true}
  });
  addTrace('BIND', `Action bound to revision ${proposal.bound_revision} and digest ${proposal.bound_digest.slice(7, 19)}.`);
  updateControls();
});

elements['cause-drift'].addEventListener('click', async () => {
  const data = await tool('revise_turnproof_fact', {
    conversation_id: current.conversation_id, expected_revision: current.revision,
    idempotency_key: `airflow-${current.revision}`, field: 'airflow', operation: 'set', value: 'no'
  });
  await render(data); addTrace('DRIFT', 'New evidence advanced the revision and invalidated the bound action.', 'attention');
});

elements['commit-stale'].addEventListener('click', async () => {
  try {
    await tool('commit_turnproof_action', {proposal_id: proposal.proposal_id, idempotency_key: 'stale-demo'});
  } catch (error) {
    elements.verdict.textContent = error.code;
    elements.verdict.dataset.state = 'blocked';
    addTrace('BLOCK', `${error.code}: ${error.message}`, 'blocked');
  }
  proposal = null; updateControls();
});

elements['start-handoff'].addEventListener('click', async () => {
  proposal = null;
  const data = await tool('start_turnproof_handoff', {
    recipient: 'Sam', task: 'pick up the prescription', time_window: 'after work',
    precondition: 'only if the pharmacy confirms it is ready'
  });
  await render(data); addTrace('CONTRACT', 'The same reducer now enforces a structurally different delegation workflow.');
});

elements['run-lab'].addEventListener('click', async () => {
  elements.score.textContent = 'RUNNING';
  const response = await fetch('/api/turnproof/lab'); const report = await response.json();
  elements.score.textContent = `${report.passed} / ${report.total}`;
  elements.checks.replaceChildren(...report.contracts.flatMap(contract => contract.checks.map(check => {
    const row = document.createElement('div'); row.className = check.passed ? 'pass' : 'fail';
    const verdict = document.createElement('i'); verdict.textContent = check.passed ? 'PASS' : 'FAIL';
    const name = document.createElement('span'); name.textContent = check.name.replaceAll('_', ' ');
    const source = document.createElement('small'); source.textContent = contract.contract_id.replace('_v1', '');
    row.append(verdict, name, source); return row;
  })));
  addTrace('LAB', `${report.passed} of ${report.total} generated attacks passed against two compiled contracts.`, report.passed === report.total ? '' : 'blocked');
});

elements.reset.addEventListener('click', () => location.reload());

const query = new URLSearchParams(location.search);

if (query.has('lab')) {
  elements['run-lab'].click();
}

if (query.has('video')) {
  runGuidedDemo(5200, true);
} else if (query.has('demo')) {
  runGuidedDemo(120, false);
}

function cue(message) {
  elements['demo-cue'].hidden = false;
  elements['demo-cue-text'].textContent = message;
}

async function runGuidedDemo(pauseMs, videoMode) {
  const pause = (duration = pauseMs) => new Promise(resolve => setTimeout(resolve, duration));
  if (videoMode) { cue('A contract begins with partial information'); await pause(3600); }
  current = await tool('start_turnproof_diagnosis', {
    scenario: 'dehumidifier', symptom: 'It runs, but the bucket stays dry.'
  });
  await render(current); addTrace('OPEN', 'Partial diagnosis accepted without invented defaults.');
  if (videoMode) cue('Missing facts remain missing; Turnproof invents no defaults'); await pause();
  current = await tool('revise_turnproof_fact', {
    conversation_id: current.conversation_id, expected_revision: current.revision,
    idempotency_key: 'guided-no', field: 'bucket_light', operation: 'set', value: 'no'
  });
  await render(current); addTrace('ADD', 'bucket_light = no entered the active state.');
  if (videoMode) cue('The first answer becomes revision 02'); await pause();
  current = await tool('revise_turnproof_fact', {
    conversation_id: current.conversation_id, expected_revision: current.revision,
    idempotency_key: 'guided-correction', field: 'bucket_light', operation: 'set', value: 'yes'
  });
  await render(current); addTrace('CORRECT', 'Correction superseded the active value without erasing history.', 'attention');
  if (videoMode) cue('A correction replaces active meaning and preserves the ledger'); await pause();
  proposal = await tool('propose_turnproof_action', {
    conversation_id: current.conversation_id, action: 'accept_resolution', parameters: {fixture: true}
  });
  addTrace('BIND', `Action bound to revision ${proposal.bound_revision}.`);
  if (videoMode) cue('The proposed action is bound to this exact revision'); await pause();
  current = await tool('revise_turnproof_fact', {
    conversation_id: current.conversation_id, expected_revision: current.revision,
    idempotency_key: 'guided-drift', field: 'airflow', operation: 'set', value: 'no'
  });
  await render(current); addTrace('DRIFT', 'New evidence invalidated the prior action.', 'attention');
  if (videoMode) cue('New evidence advances the revision'); await pause();
  try {
    await tool('commit_turnproof_action', {proposal_id: proposal.proposal_id, idempotency_key: 'guided-stale'});
  } catch (error) {
    elements.verdict.textContent = error.code;
    elements.verdict.dataset.state = 'blocked';
    addTrace('BLOCK', `${error.code}: stale action produced no effect.`, 'blocked');
  }
  proposal = null; updateControls();
  if (videoMode) cue('STATE_CHANGED: stale approval produces no effect');
  await pause(videoMode ? 6200 : pauseMs);
  elements['run-lab'].click();
  if (videoMode) {
    cue('The same contracts generate their own adversarial checks');
    await pause(7600);
    current = await tool('start_turnproof_handoff', {
      recipient: 'Sam', task: 'pick up the prescription', time_window: 'after work',
      precondition: 'only if the pharmacy confirms it is ready'
    });
    await render(current);
    addTrace('CONTRACT', 'The same reducer now enforces a structurally different delegation workflow.');
    cue('One engine, a second structurally different contract');
    await pause(7000);
    cue('24 tests · 16 generated attacks · 6 conformance gates');
  }
}
