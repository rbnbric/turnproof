const transcript = document.querySelector('#transcript');
const starter = document.querySelector('#starter');
const answers = document.querySelector('#answers');
const causes = document.querySelector('#causes');
const incidentLabel = document.querySelector('#incident');
const statusLabel = document.querySelector('#status');
const nextLabel = document.querySelector('#next');
const resolveButton = document.querySelector('#resolve');
let incident = null;

async function tool(name, args) {
  const response = await fetch(`/api/tools/${name}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(args)
  });
  const result = await response.json();
  if (result.isError) throw new Error(result.content[0].text);
  return result.structuredContent;
}

function say(who, text) {
  const turn = document.createElement('div');
  turn.className = `turn ${who.toLowerCase()}`;
  const name = document.createElement('b'); name.textContent = who;
  const words = document.createElement('p'); words.textContent = text;
  turn.append(name, words); transcript.append(turn);
  transcript.scrollTop = transcript.scrollHeight;
}

function render(data) {
  incident = data;
  incidentLabel.textContent = data.incident_id;
  statusLabel.textContent = data.status.replace('_', ' ');
  causes.replaceChildren(...data.ranked_causes.map((cause, index) => {
    const li = document.createElement('li');
    li.innerHTML = `<span><em>${String(index + 1).padStart(2, '0')}</em>${cause.label}</span><strong>${Math.round(cause.confidence * 100)}%</strong>`;
    return li;
  }));
  nextLabel.textContent = data.next_check ? data.next_check.instruction : 'No further inspection selected.';
  answers.classList.toggle('hidden', !data.next_check || data.status !== 'investigating');
  resolveButton.classList.toggle('hidden', Object.keys(data.observations).length === 0 || data.status !== 'investigating');
}

starter.addEventListener('click', async event => {
  const button = event.target.closest('button[data-scenario]'); if (!button) return;
  starter.classList.add('hidden');
  say('You', button.dataset.symptom);
  const data = await tool('open_incident', {scenario: button.dataset.scenario, symptom: button.dataset.symptom});
  render(data);
  if (data.safety_message) say('Alexa', data.safety_message);
  else say('Alexa', `${data.next_check.prompt} ${data.next_check.instruction}`);
});

answers.addEventListener('click', async event => {
  const button = event.target.closest('button[data-answer]'); if (!button || !incident?.next_check) return;
  say('You', button.textContent);
  const data = await tool('record_observation', {
    incident_id: incident.incident_id, check_id: incident.next_check.id, result: button.dataset.answer
  });
  render(data);
  if (data.next_check) say('Alexa', `${data.next_check.prompt} ${data.next_check.instruction}`);
  else say('Alexa', 'I have enough observations to propose a bounded next action.');
});

resolveButton.addEventListener('click', async () => {
  const result = await tool('propose_resolution', {incident_id: incident.incident_id});
  say('Alexa', `The leading cause is ${result.cause.label.toLowerCase()}. ${result.action} Tell me afterward whether it worked.`);
  incident = await tool('incident_summary', {incident_id: incident.incident_id}); render(incident);
});

document.querySelector('#reset').addEventListener('click', () => location.reload());

