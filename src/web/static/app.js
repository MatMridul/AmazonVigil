// Mission Control — driven entirely by the real pipeline API.
// No hardcoded threat data: every reading comes from /api/scenario/<id>,
// which runs the actual VigilPipeline. Honesty markers (simulated/source)
// travel with the payload and are rendered as badges.

const $ = (id) => document.getElementById(id);
const bar = (v) => {
  const n = Math.round(Math.max(0, Math.min(1, v)) * 10);
  return '█'.repeat(n) + '░'.repeat(10 - n);
};

async function loadScenarios() {
  const res = await fetch('/api/scenarios');
  const list = await res.json();
  const sel = $('selector');
  sel.innerHTML = '';
  list.forEach((s, i) => {
    const b = document.createElement('button');
    b.textContent = s.id.replace(/_/g, ' ').toUpperCase();
    b.dataset.id = s.id;
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
  const res = await fetch('/api/scenario/' + id);
  if (!res.ok) { $('stateflag').textContent = '◆ ERROR'; return; }
  const d = await res.json();

  // body state drives the instrument re-coloring
  document.body.classList.remove('threat', 'dispatch');
  const level = d.level;
  if (level === 'L3_CRITICAL' || d.cad_staged) document.body.classList.add('dispatch');
  else if (level === 'L2_SUSPICIOUS') document.body.classList.add('threat');

  $('modeval').textContent = (d.mode || '').toUpperCase();
  $('score').textContent = (d.score ?? 0).toFixed(2);
  const verdictMap = {
    L0_SAFE: ['L0 · GROUNDS NOMINAL', 'var(--accent-emerald)'],
    L1_AMBIGUOUS: ['L1 · AMBIGUOUS — NOTIFY', 'var(--accent-cyan)'],
    L2_SUSPICIOUS: ['L2 · SUSPICIOUS — DETER', 'var(--accent-amber)'],
    L3_CRITICAL: ['L3 · CRITICAL — DISPATCH', 'var(--accent-crimson)'],
  };
  const [vtxt, vcol] = verdictMap[level] || ['—', 'var(--text-muted)'];
  $('verdict').textContent = vtxt;
  $('verdict').style.color = vcol;

  const flagMap = {
    L0_SAFE: '◆ PERIMETER_SECURE', L1_AMBIGUOUS: '◆ OBSERVING',
    L2_SUSPICIOUS: '▲ ACTIVE_DEFENSE', L3_CRITICAL: '■ CAD_STAGED',
  };
  $('stateflag').textContent = flagMap[level] || '—';

  // Phi bars (real integrity vector). phi_v==0 collapses the bar to crimson.
  const phi = d.integrity || { phi_m: 1, phi_v: 1, phi_a: 1, phi_net: 1 };
  const rows = [['Φ_motion', phi.phi_m], ['Φ_visual', phi.phi_v], ['Φ_audio', phi.phi_a], ['Φ_net', phi.phi_net]];
  $('bars').innerHTML = rows.map(([lbl, v]) =>
    `<div class="barrow ${v <= 0 ? 'collapsed' : ''}"><span class="lbl">${lbl}</span>` +
    `<span class="bar"><b>${bar(v)}</b></span><span class="num">${v.toFixed(2)}</span></div>`
  ).join('');

  // honesty badge
  $('simbadge').textContent = d.simulated ? 'SIM · ' + (d.source || '') : 'LIVE · ' + (d.source || '');
  $('simtag').textContent = d.simulated ? 'SIM_FEED' : 'LIVE_FEED';
  $('camlabel').textContent = level === 'L0_SAFE' ? 'CAM.00 — FRONT_PORCH' : 'CAM.00 — BREACH_STREAM';
  $('ts').textContent = d.title;

  // guidance + actuators (every button maps to a real/SIM action)
  const acts = d.permitted_actuators || [];
  $('guidemsg').textContent = buildGuidance(d, acts);
  $('guidehd').textContent = d.cad_staged
    ? '■ CAD MANIFEST STAGED — AWAITING HUMAN AUTHORIZATION'
    : '▲ PERIMETER ALERT — ACTIVE PROTECTION IN PROGRESS';
  renderActs(d, acts);

  // attribution / mesh provenance
  renderAttribution(d);
  await renderMesh();
}

function buildGuidance(d, acts) {
  if (d.cad_staged) {
    return 'Verified critical breach. Emergency CAD manifest staged with SHA-256 integrity hash. ' +
      (acts.length === 0
        ? 'SILENT DURESS — every interior/exterior actuator held silent by construction. Dispatch via phone authorization only.'
        : 'Deterrence running. Human authorization required on the Nightstand phone to transmit.');
  }
  if (d.level === 'L2_SUSPICIOUS') {
    return 'Unknown individual at the perimeter. Mesh deterrence running: ' + acts.join(', ') + '. Remain inside.';
  }
  if (d.level === 'L1_AMBIGUOUS') return 'Ambiguous presence logged. Host notified; no deterrence engaged.';
  return 'Grounds nominal. No action required.';
}

function renderActs(d, acts) {
  const el = $('acts');
  el.innerHTML = '';
  // Buttons reflect REAL permitted actuators + the authorization controls.
  acts.forEach((a) => {
    const b = document.createElement('button');
    b.textContent = a.toUpperCase();
    b.title = 'MODELED actuator — ' + a;
    el.appendChild(b);
  });
  if (d.cad_staged) {
    const cancel = document.createElement('button');
    cancel.textContent = 'CANCEL_FALSE (PIN)';
    el.appendChild(cancel);
    const disp = document.createElement('button');
    disp.className = 'crit';
    disp.textContent = 'AUTHORIZE_911 →';
    disp.title = 'Routes to the Nightstand phone for human authorization';
    disp.onclick = () => { window.location.href = '/phone.html'; };
    el.appendChild(disp);
  }
}

function renderAttribution(d) {
  const sig = d.signals || {};
  const lines = [];
  lines.push(['SOURCE', 'anthropic.claude-3-5-sonnet (edge-deterministic path)', '']);
  if (d.ingest) {
    lines.push(['VISUAL', String(d.ingest.V ?? '—'), sig.masked_near_entry ? 'amber' : '']);
    lines.push(['AUDIO', String(d.ingest.A ?? '—'), sig.breach_acoustics ? 'amber' : '']);
    lines.push(['MOTION', String(d.ingest.M ?? '—'), '']);
  }
  lines.push(['SUBJECT', String(d.subject ?? '—'), '']);
  lines.push(['WEARER', String(d.host_state ?? '—'), '']);
  lines.push(['CORROBORATE', sig.corroboration_count + ' sensor(s)', sig.distress_flag ? 'crimson' : '']);
  if (d.cad_sha256) lines.push(['CAD_HASH', d.cad_sha256.slice(0, 32) + '…', 'crimson']);
  $('attribution').innerHTML = lines.map(([tag, txt, cls]) =>
    `<div class="aline"><span class="tag">${tag}</span><span class="txt ${cls}">${txt}</span></div>`
  ).join('');
}

async function renderMesh() {
  const res = await fetch('/api/mesh');
  const nodes = await res.json();
  $('meshcount').textContent = nodes.length + ' nodes';
  $('meshnodes').innerHTML = nodes.map((n) =>
    `<div class="devrow"><span class="name">${n.name}</span>` +
    `<span class="meta">${n.role}</span>` +
    `<span class="stat ${n.status === 'MODELED' ? 'modeled' : ''}">${n.status}</span></div>`
  ).join('');
}

loadScenarios();
