// Nightstand Phone — the human crisis surface.
// Renders the real CAD manifest (SHA-256 from the pipeline) and wires the two
// authorization controls: TRANSMIT (staged send) and CANCEL-WITH-PIN, which
// calls the REAL /api/disarm endpoint (verify_disarm_pin). The 10s countdown
// mirrors the CadStaging cancel buffer.

const $ = (id) => document.getElementById(id);
let countdownTimer = null;

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
  document.body.classList.remove('threat', 'dispatch');
  if (d.cad_staged || d.level === 'L3_CRITICAL') document.body.classList.add('dispatch');
  else if (d.level === 'L2_SUSPICIOUS') document.body.classList.add('threat');

  const level = d.level;
  if (level === 'L0_SAFE') {
    $('csub').textContent = 'VIGIL · PERIMETER SECURE';
    $('ctitle').textContent = 'All quiet';
    $('cmsg').textContent = 'Grounds nominal. Sleep well — Vigil is watching.';
  } else if (level === 'L1_AMBIGUOUS') {
    $('csub').textContent = 'VIGIL · OBSERVING';
    $('ctitle').textContent = 'Someone at the perimeter';
    $('cmsg').textContent = 'Ambiguous presence logged. No action needed from you — we are watching.';
  } else if (level === 'L2_SUSPICIOUS') {
    $('csub').textContent = 'VIGIL · ACTIVE PROTECTION';
    $('ctitle').textContent = 'Unknown individual at the door';
    $('cmsg').textContent = 'Deterrence is running. Stay inside and stay calm — Vigil is handling it.';
  } else {
    $('csub').textContent = d.permitted_actuators.length === 0 ? 'VIGIL · SILENT DURESS' : 'VIGIL · CRITICAL';
    $('ctitle').textContent = 'Emergency dispatch staged';
    $('cmsg').textContent = d.permitted_actuators.length === 0
      ? 'Silent duress detected. Everything is quiet by design. Authorize dispatch only when safe.'
      : 'Verified breach. Review the manifest and authorize if this is a real emergency.';
  }

  // real CAD manifest
  $('cad_id').textContent = d.scenario_id;
  $('cad_hash').textContent = d.cad_sha256 ? d.cad_sha256.slice(0, 24) + '…' : '—';

  if (d.cad_staged) startCountdown();
  else stopCountdown();
  resetAuthControls();
}

function startCountdown() {
  stopCountdown();
  let t = 10;
  const el = $('countdown');
  el.className = 'countdown';
  el.textContent = t;
  countdownTimer = setInterval(() => {
    t -= 1;
    if (t <= 0) {
      el.textContent = 'SEND WINDOW OPEN';
      el.className = 'countdown sent';
      clearInterval(countdownTimer);
      countdownTimer = null;
    } else {
      el.textContent = t;
    }
  }, 1000);
}

function stopCountdown() {
  if (countdownTimer) { clearInterval(countdownTimer); countdownTimer = null; }
}

function resetAuthControls() {
  $('pinwrap').classList.remove('show');
  $('pin').value = '';
}

$('transmit').onclick = () => {
  stopCountdown();
  const el = $('countdown');
  el.textContent = '911 MANIFEST TRANSMITTED';
  el.className = 'countdown sent';
};

$('cancelbtn').onclick = () => { $('pinwrap').classList.add('show'); $('pin').focus(); };

$('pinsubmit').onclick = async () => {
  const pin = $('pin').value;
  // REAL verification through the server's verify_disarm_pin path.
  const res = await (await fetch('/api/disarm', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pin }),
  })).json();
  const el = $('countdown');
  if (res.disarmed) {
    stopCountdown();
    el.textContent = 'DISARMED — DISPATCH ABORTED';
    el.className = 'countdown disarmed';
    $('pinwrap').classList.remove('show');
  } else {
    $('pin').value = '';
    $('pin').placeholder = 'WRONG';
  }
};

// live clock on the lock screen
function tick() {
  const now = new Date();
  $('clock').textContent = now.getHours() + ':' + String(now.getMinutes()).padStart(2, '0');
}
tick();
setInterval(tick, 10000);
loadScenarios();
