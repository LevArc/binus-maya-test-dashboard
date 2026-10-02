const byId = id => document.getElementById(id);
let allRuns = [];
let selectedId = null;
const names = {authentication: 'Authentication', schedule: 'Class schedule', materials: 'Learning materials', run: 'Run'};
function node(tag, text, cls) { const el = document.createElement(tag); if (text !== undefined) el.textContent = text; if (cls) el.className = cls; return el; }
function latestSteps(run) { const map = new Map(); for (const step of run.steps) { if (step.name === 'authentication' && step.status === 'running' && step.detail === 'Opening the saved local Chrome profile.') continue; map.set(step.name, step); } return [...map.values()]; }
function view(run) {
  const status = run?.status || 'idle';
  const active = allRuns.some(item => ['running', 'login_required'].includes(item.status));
  byId('start').disabled = active;
  byId('run-badge').className = 'badge ' + status;
  byId('run-badge').textContent = status === 'login_required' ? 'Login required' : status === 'idle' ? 'Idle' : status;
  byId('run-status').textContent = !run ? 'Ready when you are' : ({passed:'All checks passed',failed:'Check failed',running:'Testing in progress',login_required:'Waiting for your login',interrupted:'Run interrupted'})[status] || status;
  const steps = run ? latestSteps(run) : [];
  const completed = steps.filter(step => ['schedule','materials'].includes(step.name) && ['passed','failed'].includes(step.status)).length;
  byId('progress-fill').style.width = `${completed * 50}%`;
  byId('run-message').textContent = !run ? 'Start a run to check your schedule and course materials.' : status === 'login_required' ? 'Complete login in the Chrome window. The tests resume automatically.' : status === 'passed' ? 'Both feature checks completed.' : status === 'failed' ? 'Review the failed step and its local screenshot.' : 'Following each step live.';
  byId('run-time').textContent = run ? new Date(run.started).toLocaleString() : '—';
  const list = byId('steps'); list.replaceChildren();
  if (!run) {list.append(node('p','No test run yet. Your progress will appear here.','empty'));return;}
  for (const step of steps) {
    const article = node('article',undefined,'step ' + step.status);
    const index = node('div',step.status === 'passed' ? '✓' : step.status === 'failed' ? '!' : '•','step-index');
    const body = node('div'); const top = node('div',undefined,'step-top');
    top.append(node('h3',names[step.name] || 'Run'),node('span',step.status === 'waiting' ? 'Waiting' : step.status,'step-status'));
    body.append(top,node('p',step.detail));
    if (step.count !== null && step.count !== undefined) body.append(node('small',`${step.count} items verified · ${(step.duration_ms / 1000).toFixed(2)}s`));
    if (step.screenshot && ['schedule.png','materials.png'].includes(step.screenshot)) {
      const a = node('a','View screenshot','evidence-link');
      a.href = `/api/runs/${encodeURIComponent(run.id)}/evidence/${step.screenshot}`;
      a.target = '_blank'; a.rel = 'noopener noreferrer';
      body.append(a);
    }
    if (step.excerpt) body.append(node('div',step.excerpt,'excerpt'));
    article.append(index,body);list.append(article);
  }
}
function render(runs) {
  allRuns = runs;
  if (!selectedId || !runs.some(r => r.id === selectedId)) selectedId = runs[0]?.id || null;
  view(runs.find(r => r.id === selectedId));
  const history = byId('history-list'); history.replaceChildren();
  byId('history-count').textContent = `${runs.length} ${runs.length === 1 ? 'run' : 'runs'}`;
  if (!runs.length) { history.append(node('p','Runs are saved locally until you remove them manually.','empty small'));return; }
  for (const run of runs) {
    const button = node('button',undefined,'history-item' + (run.id === selectedId ? ' selected' : ''));
    button.type = 'button'; const left = node('span'); left.append(node('strong',new Date(run.started).toLocaleString()),node('small',run.id.slice(0,8)));
    button.append(left,node('span',run.status === 'login_required' ? 'Login required' : run.status,'history-state ' + run.status));
    button.onclick = () => {selectedId = run.id;render(allRuns)};
    history.append(button);
  }
}
async function refresh() { try { const response = await fetch('/api/runs',{cache:'no-store'}); if (response.ok) render(await response.json()); } catch (_) {byId('run-message').textContent = 'Dashboard connection lost. Refresh the page.';} }
byId('start').addEventListener('click',async () => {
  byId('start').disabled = true;
  try {const response = await fetch('/api/runs',{method:'POST'}); if (!response.ok) throw new Error(response.status === 409 ? 'A run is already active.' : 'Could not start the run.'); selectedId = (await response.json()).id; await refresh();}
  catch (error) {byId('run-message').textContent = error.message; byId('start').disabled = false;}
});
refresh();
const stream = new EventSource('/api/events');
stream.onmessage = event => {try {render(JSON.parse(event.data));} catch (_) {refresh();}};
stream.onerror = () => {setTimeout(refresh,2000);};
