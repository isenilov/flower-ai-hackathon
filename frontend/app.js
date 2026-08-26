// Reads the append-only event trace the backend writes and replays it as a paced
// animation. Replay rather than raw tail: with no model in the loop a whole run lands in
// well under a second, so the narrator needs a clock of their own. `follow` re-reads the
// file and plays new events as they arrive, which is what happens once each round makes
// real model calls.

const TRACE_URL = 'state/trace.jsonl';
const SUPPORTED_VERSION = 1;
const POLL_MS = 400;

// Beat durations at 1x, in ms. The stage is legible or it is decoration.
const BEAT = {
  run_started: 900,
  round_started: 750,
  broadcast: 1150,
  reply: 850,
  matrix: 1300,
  round_ended: 420,
  run_ended: 1100,
};

const FIRM_TONES = ['var(--firm-a)', 'var(--firm-b)', 'var(--firm-c)'];

const el = (id) => document.getElementById(id);

const dom = {
  solicitation: el('solicitation'),
  empty: el('empty'),
  stage: el('stage'),
  panels: el('panels'),
  log: el('log'),
  logList: el('logList'),
  wires: el('wires'),
  coordinator: el('coordinator'),
  coordinatorState: el('coordinatorState'),
  reqStrip: el('reqStrip'),
  firms: el('firms'),
  roundBanner: el('roundBanner'),
  matrix: el('matrix'),
  verdict: el('verdict'),
  clock: el('clock'),
  play: el('play'),
  step: el('step'),
  restart: el('restart'),
  speed: el('speed'),
  follow: el('follow'),
  mBanded: el('mBanded'),
  mRecords: el('mRecords'),
  mGap: el('mGap'),
  mRounds: el('mRounds'),
  ledgerNote: el('ledgerNote'),
};

const state = {
  events: [],
  cursor: 0,
  playing: false,
  speed: 1,
  timer: null,
  built: false,
  firms: new Map(),      // firm name -> { tone, card, handles: Set, lane index }
  cells: new Map(),      // requirement id -> { node, met }
  reqChips: new Map(),
  raw: '',
};

// ------------------------------------------------------------------ utilities

const bytes = (n) => (n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} kB`);

const shortHandle = (h) => h.replace(/^FIRM_[A-Z]::/, '');

const shortFirm = (f) => f.replace(/^FIRM_/, 'Firm ');

function centre(node) {
  const box = node.getBoundingClientRect();
  const frame = dom.stage.getBoundingClientRect();
  return { x: box.left - frame.left + box.width / 2, y: box.top - frame.top + box.height / 2 };
}

// ------------------------------------------------------------------- building

function build(event) {
  dom.solicitation.innerHTML = `Solicitation: <strong>${event.solicitation}</strong>`;
  dom.empty.hidden = true;
  dom.stage.hidden = false;
  dom.panels.hidden = false;
  dom.log.hidden = false;

  dom.reqStrip.innerHTML = '';
  state.reqChips.clear();
  dom.matrix.innerHTML = '';
  state.cells.clear();

  for (const req of event.requirements) {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = req.id;
    dom.reqStrip.append(chip);
    state.reqChips.set(req.id, chip);

    const cell = document.createElement('div');
    cell.className = 'cell';
    cell.title = req.description;
    cell.innerHTML =
      `<div class="rid">${req.id}</div>` +
      `<div class="cnt">0 / ${req.min_count}</div>` +
      `<div class="kind">${req.kind === 'MANDATORY' ? 'must' : 'weighted'}</div>`;
    if (req.kind !== 'MANDATORY') cell.classList.add('weighted');
    dom.matrix.append(cell);
    state.cells.set(req.id, { node: cell, met: false, need: req.min_count });
  }

  // Firm lanes are created from `run_started`'s node list so the stage has its shape
  // before any reply names a firm; the labels are filled in as the replies arrive.
  dom.firms.innerHTML = '';
  state.firms.clear();
  event.firms.forEach((placeholder, index) => {
    lane(placeholder, index);
  });

  state.built = true;
  requestAnimationFrame(drawWires);
}

function lane(name, index) {
  const card = document.createElement('div');
  card.className = 'firm';
  card.style.setProperty('--tone', FIRM_TONES[index % FIRM_TONES.length]);
  card.innerHTML =
    `<div class="firm-head">` +
    `<span class="firm-name"></span><span class="firm-state">waiting</span></div>` +
    `<div class="boundary">private library</div>` +
    `<div class="handles"></div>` +
    `<div class="firm-foot"><span>attested <b class="n">0</b></span>` +
    `<span>on wire <b class="b">0 B</b></span></div>`;
  card.querySelector('.firm-name').textContent = name.startsWith('node ') ? '—' : shortFirm(name);
  dom.firms.append(card);

  const entry = {
    card,
    tone: FIRM_TONES[index % FIRM_TONES.length],
    handles: new Set(),
    nameEl: card.querySelector('.firm-name'),
    stateEl: card.querySelector('.firm-state'),
    handlesEl: card.querySelector('.handles'),
    countEl: card.querySelector('.n'),
    bytesEl: card.querySelector('.b'),
  };
  state.firms.set(name, entry);
  return entry;
}

// A reply is the first thing that names its firm. Adopt the next unnamed lane rather than
// adding a fourth card, so the stage keeps one lane per SuperNode.
function laneFor(firm) {
  if (state.firms.has(firm)) return state.firms.get(firm);

  for (const [key, entry] of state.firms) {
    if (key.startsWith('node ')) {
      state.firms.delete(key);
      state.firms.set(firm, entry);
      entry.nameEl.textContent = shortFirm(firm);
      return entry;
    }
  }
  return lane(firm, state.firms.size);
}

function drawWires() {
  if (!state.built || dom.stage.hidden) return;
  const frame = dom.stage.getBoundingClientRect();
  dom.wires.setAttribute('viewBox', `0 0 ${frame.width} ${frame.height}`);
  dom.wires.innerHTML = '';

  const from = centre(dom.coordinator);
  from.y += dom.coordinator.getBoundingClientRect().height / 2 - 2;

  for (const entry of state.firms.values()) {
    const to = centre(entry.card);
    to.y -= entry.card.getBoundingClientRect().height / 2 - 2;
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const midY = (from.y + to.y) / 2;
    path.setAttribute('d', `M ${from.x} ${from.y} C ${from.x} ${midY}, ${to.x} ${midY}, ${to.x} ${to.y}`);
    dom.wires.append(path);
    entry.wire = path;
  }
}

window.addEventListener('resize', drawWires);

// ------------------------------------------------------------------- packets

function fly(fromNode, toNode, { label, tone, kind, ms }) {
  const a = centre(fromNode);
  const b = centre(toNode);
  const packet = document.createElement('div');
  packet.className = `packet ${kind || ''}`;
  if (tone) packet.style.setProperty('--tone', tone);
  packet.textContent = label;
  dom.stage.append(packet);

  // A shallow S through the midpoint, so several packets in flight stay distinguishable.
  const mid = { x: (a.x + b.x) / 2 + (b.x - a.x) * 0.12, y: (a.y + b.y) / 2 };
  const start = performance.now();

  return new Promise((resolve) => {
    const tick = (now) => {
      const t = Math.min((now - start) / ms, 1);
      const e = t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;
      const x = (1 - e) ** 2 * a.x + 2 * (1 - e) * e * mid.x + e ** 2 * b.x;
      const y = (1 - e) ** 2 * a.y + 2 * (1 - e) * e * mid.y + e ** 2 * b.y;
      packet.style.left = `${x}px`;
      packet.style.top = `${y}px`;
      packet.style.opacity = t < 0.1 ? t / 0.1 : t > 0.85 ? (1 - t) / 0.15 : 1;
      if (t < 1) requestAnimationFrame(tick);
      else { packet.remove(); resolve(); }
    };
    requestAnimationFrame(tick);
  });
}

// --------------------------------------------------------------------- apply

function apply(event) {
  logLine(event);

  switch (event.type) {
    case 'run_started': {
      if (event.version !== SUPPORTED_VERSION) {
        dom.solicitation.textContent =
          `Trace format v${event.version}; this page reads v${SUPPORTED_VERSION}. Reload the frontend.`;
        return;
      }
      build(event);
      dom.coordinatorState.textContent = `${event.requirements.length} requirements decomposed`;
      dom.mRounds.textContent = `0 of ${event.num_rounds}`;
      break;
    }

    case 'round_started': {
      const gap = event.gap.length;
      dom.roundBanner.classList.add('on');
      dom.roundBanner.classList.toggle('gap', gap > 0);
      dom.roundBanner.querySelector('span').textContent = gap
        ? `Round ${event.round} — re-examine against ${event.gap.join(', ')}`
        : `Round ${event.round} — blind attestation`;
      dom.mRounds.textContent = `${event.round} of ${state.events[0]?.num_rounds ?? event.round}`;
      for (const entry of state.firms.values()) {
        entry.card.classList.remove('found');
        entry.stateEl.textContent = gap ? 'reading bios' : 'declared fields only';
      }
      break;
    }

    case 'broadcast': {
      dom.coordinator.classList.add('busy');
      dom.coordinatorState.textContent = event.gap.length
        ? `broadcasting the gap: ${event.gap.join(', ')}`
        : `broadcasting ${event.requirements} requirements`;
      for (const id of event.gap) state.reqChips.get(id)?.classList.add('live');

      const isGap = event.gap.length > 0;
      const label = isGap ? `gap ${event.gap.join(',')} · ${bytes(event.gap_bytes)}` : `RFP · ${bytes(event.bytes)}`;
      if (isGap) dom.mGap.textContent = bytes(event.gap_bytes);

      for (const entry of state.firms.values()) {
        entry.wire?.classList.add('hot');
        entry.card.classList.add('searching');
        fly(dom.coordinator, entry.card, {
          label, kind: isGap ? 'gap' : '', ms: BEAT.broadcast / state.speed * 0.75,
        });
      }
      break;
    }

    case 'reply': {
      const entry = laneFor(event.firm);
      const fresh = event.new_requirements.length > 0;
      entry.wire?.classList.remove('hot');
      entry.card.classList.remove('searching');
      if (fresh) entry.card.classList.add('found');
      entry.stateEl.textContent = fresh
        ? `+${event.new_requirements.join(',')}`
        : 'nothing new';
      entry.countEl.textContent = event.attestations;
      entry.bytesEl.textContent = bytes(event.bytes);

      for (const handle of event.handles) {
        if (entry.handles.has(handle)) continue;
        entry.handles.add(handle);
        const chip = document.createElement('span');
        chip.className = fresh && state.round > 1 ? 'h fresh' : 'h';
        chip.textContent = shortHandle(handle);
        entry.handlesEl.append(chip);
      }

      fly(entry.card, dom.coordinator, {
        label: `${event.attestations} attestations · ${bytes(event.bytes)}`,
        tone: entry.tone,
        kind: fresh && state.round > 1 ? 'win' : 'reply',
        ms: BEAT.reply / state.speed * 0.8,
      });
      break;
    }

    case 'matrix': {
      dom.coordinator.classList.remove('busy');
      dom.coordinatorState.textContent = 'coverage recomputed';
      for (const row of event.rows) {
        const cell = state.cells.get(row.id);
        if (!cell) continue;
        cell.node.querySelector('.cnt').textContent = `${row.have} / ${row.need}`;
        cell.node.classList.toggle('met', row.met);
        cell.node.classList.toggle('miss', !row.met);
        if (row.met && !cell.met) {
          cell.node.classList.add('turned');
          setTimeout(() => cell.node.classList.remove('turned'), 1000 / state.speed);
        }
        cell.met = row.met;
      }
      renderVerdict(event);
      break;
    }

    case 'round_ended': {
      state.round = event.round + 1;
      for (const entry of state.firms.values()) entry.card.classList.remove('found');
      break;
    }

    case 'run_ended': {
      dom.roundBanner.classList.remove('on');
      dom.coordinator.classList.remove('busy');
      dom.coordinatorState.textContent = event.compliant ? 'bid is compliant' : 'bid is non-compliant';
      dom.mBanded.textContent = bytes(event.banded_bytes);
      dom.mRecords.textContent = `${event.record_bytes} B`;
      dom.mRounds.textContent = `${event.rounds_run}`;
      if (dom.mGap.textContent === '—') dom.mGap.textContent = 'not needed';
      dom.ledgerNote.textContent =
        'Record content is zero by construction, not by policy — the protocol has no field ' +
        'that can carry it. The approval gate is what makes it non-zero, per released handle.';
      break;
    }
  }
}

function renderVerdict(event) {
  const mandatory = event.rows.filter((r) => !r.met && r.kind === 'MANDATORY').map((r) => r.id);
  const closed = event.closed || [];
  if (closed.length) {
    dom.verdict.innerHTML =
      `<span class="good">${closed.join(', ')} closed</span> ` +
      `<span class="why">— re-examination found it after the gap was broadcast</span>`;
    return;
  }
  dom.verdict.innerHTML = mandatory.length
    ? `<span class="bad">NON-COMPLIANT</span> <span class="why">— mandatory gap: ${mandatory.join(', ')}. ` +
      `No single firm's own assessment shows this.</span>`
    : `<span class="good">COMPLIANT</span> <span class="why">— every mandatory requirement evidenced.</span>`;
}

function logLine(event) {
  const li = document.createElement('li');
  const label = describe(event);
  if (!label) return;
  li.innerHTML = `<span class="t">${event.t_ms.toFixed(1)}ms</span><span>${label}</span>`;
  if (event.type === 'broadcast' && event.gap?.length) li.className = 'key';
  if (event.type === 'reply' && event.new_requirements?.length && state.round > 1) li.className = 'win';
  if (event.type === 'matrix' && event.closed?.length) li.className = 'win';
  dom.logList.append(li);
  dom.logList.scrollTop = dom.logList.scrollHeight;
}

function describe(e) {
  switch (e.type) {
    case 'run_started': return `trace v${e.version} · ${e.requirements.length} requirements · ${e.firms.length} firms`;
    case 'round_started': return `round ${e.round} — gap ${e.gap.join(',') || '—'}`;
    case 'broadcast': return `coordinator → all firms · ${bytes(e.bytes)}${e.gap.length ? ` · gap ${bytes(e.gap_bytes)}` : ''}`;
    case 'reply': return `${e.firm} → coordinator · ${e.attestations} attestations · ${bytes(e.bytes)}${e.new_requirements.length ? ` · new ${e.new_requirements.join(',')}` : ''}`;
    case 'matrix': return `matrix · open ${e.open_gaps.join(',') || 'none'}${e.closed?.length ? ` · closed ${e.closed.join(',')}` : ''}`;
    case 'round_ended': return e.stopped ? `round ${e.round} ended — ${e.stopped}` : '';
    case 'run_ended': return `run ended · ${e.rounds_run} rounds · ${bytes(e.banded_bytes)} banded · ${e.record_bytes} B records`;
    default: return '';
  }
}

// ------------------------------------------------------------------ playback

function advance() {
  if (state.cursor >= state.events.length) {
    stop();
    return;
  }
  const event = state.events[state.cursor++];
  apply(event);
  dom.clock.textContent = `${event.t_ms.toFixed(1)}ms`;

  if (!state.playing) return;
  const wait = (BEAT[event.type] ?? 500) / state.speed;
  state.timer = setTimeout(advance, wait);
}

function play() {
  if (state.cursor >= state.events.length) reset();
  state.playing = true;
  dom.play.textContent = 'Pause';
  advance();
}

function stop() {
  state.playing = false;
  clearTimeout(state.timer);
  dom.play.textContent = state.cursor >= state.events.length ? 'Replay' : 'Play';
}

function reset() {
  stop();
  state.cursor = 0;
  state.round = 1;
  state.built = false;
  dom.logList.innerHTML = '';
  dom.verdict.innerHTML = '';
  dom.roundBanner.classList.remove('on', 'gap');
  for (const key of ['mBanded', 'mRecords', 'mGap', 'mRounds']) dom[key].textContent = '—';
  dom.ledgerNote.textContent = '';
  dom.stage.querySelectorAll('.packet').forEach((p) => p.remove());
}

dom.play.onclick = () => (state.playing ? stop() : play());
dom.step.onclick = () => { stop(); advance(); };
dom.restart.onclick = () => { reset(); play(); };
dom.speed.onchange = () => { state.speed = Number(dom.speed.value); };

// ---------------------------------------------------------------- the trace

function parse(text) {
  return text
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => {
      try { return JSON.parse(line); } catch { return null; }
    })
    .filter(Boolean);
}

async function load({ autoplay }) {
  let text;
  try {
    const res = await fetch(`${TRACE_URL}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(res.status);
    text = await res.text();
  } catch {
    return false;
  }

  if (text === state.raw) return true;
  state.raw = text;
  const events = parse(text);
  if (!events.length) return false;

  // A shorter trace than we hold means a fresh run started — begin again.
  const restarted = events.length < state.events.length || events[0]?.t_ms !== state.events[0]?.t_ms;
  state.events = events;
  if (restarted) reset();
  if (autoplay && !state.playing) play();
  return true;
}

async function poll() {
  await load({ autoplay: true });
  if (dom.follow.checked) setTimeout(poll, POLL_MS);
}

dom.follow.onchange = () => { if (dom.follow.checked) poll(); };

load({ autoplay: false }).then((ok) => {
  if (!ok) return;
  reset();
  play();
});
