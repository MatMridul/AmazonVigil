// Fire TV — the 10-foot deterrence surface.
// Reacts to the REAL scenario result (level + host_state + subject), mapping to
// the UX-03 combinatorial response: standby / PIP toast / full-screen bluff.
// This visualizes exactly what the live Fire TV adapter would command.

const $ = (id) => document.getElementById(id);

async function loadScenarios() {
  const list = await (await fetch('/api/scenarios')).json();
  const sel = $('selector');
  sel.innerHTML = '';
  list.forEach((s, i) => {
    const b = document.createElement('button');
    b.textContent = s.id.replace(/_/g, ' ').toUpperCase();
    b.onclick = () => select(s.id, b);
    sel.appendChild(b);
    if (i === 0) b.classList.add('active');
  });
  if (list.length) select(list[0].id, sel.firstChild);
}

function select(id, btn) {
  document.querySelectorAll('.selector button').forEach((b) => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  render(id);
}

async function render(id) {
  const d = await (await fetch('/api/scenario/' + id)).json();
  const body = document.body;
  body.classList.remove('threat', 'dispatch', 'standby-on', 'pip-on');

  const level = d.level;
  const asleep = d.host_state === 'H_asleep';
  const deterring = (d.permitted_actuators || []).some(
    (a) => a.includes('firetv') || a.includes('boot_bridge')
  );

  // UX-03 combinatorial response, derived from the real pipeline result:
  if (level === 'L3_CRITICAL' && (d.permitted_actuators || []).length === 0) {
    // SILENT_DURESS → screen stays BLACK, no bluff (silence invariant on TV).
    body.classList.add('standby-on');
    setTensor(d, 'SILENT — screen black by duress invariant');
    return;
  }
  if (level === 'L2_SUSPICIOUS' || level === 'L3_CRITICAL') {
    // Hostile → full-screen "Home Alone" occupancy bluff (or HDMI-CEC wake if asleep).
    body.classList.add('threat');
    if (asleep) body.classList.add('dispatch'); // woke from standby
    $('bluffsub').textContent = asleep ? '▲ HDMI-CEC WAKE · DETERRENCE' : '▲ ACTIVE DETERRENCE';
    $('blufftxt').textContent = asleep
      ? '"Who\'s there? Hold on —"  (occupancy bluff)'
      : '"Hold on — I\'m coming to the door!"';
    $('audiotxt').textContent = 'footsteps + conversation @ 75%';
    setTensor(d, asleep ? 'STANDBY→WAKE · bluff audio' : 'PLAYING→bluff');
    return;
  }
  if (level === 'L1_AMBIGUOUS') {
    if (asleep) { body.classList.add('standby-on'); setTensor(d, 'STANDBY · logged, screen stays off'); }
    else { body.classList.add('pip-on'); $('piptxt').textContent = 'Visitor at front door · ' + (d.subject || ''); setTensor(d, 'PLAYING · PIP heads-up 8s'); }
    return;
  }
  // L0 safe
  if (asleep) { body.classList.add('standby-on'); setTensor(d, 'STANDBY · zero-trace'); }
  else setTensor(d, 'PLAYING · zero interruption');
}

function setTensor(d, response) {
  $('tensor').innerHTML = [
    ['POWER', d.host_state === 'H_asleep' ? 'STANDBY' : 'ON'],
    ['SUBJECT', d.subject || '—'],
    ['LEVEL', d.level],
    ['RESPONSE', response],
  ].map(([k, v]) => `<div class="tcell"><div class="tk">${k}</div><div class="tv2">${v}</div></div>`).join('');
}

loadScenarios();
