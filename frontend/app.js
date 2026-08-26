// Reads the append-only event trace the backend writes and replays it as a paced
// animation. Replay rather than raw tail: with no model in the loop a whole run lands in
// well under a second, so the narrator needs a clock of their own. `follow` re-reads the
// file and plays new events as they arrive, which is what happens once each round makes
// real model calls.

const LIVE_TRACE = 'state/trace.jsonl';
const INDEX_URL = 'state/scenarios.json';
const SUPPORTED_VERSION = 1;
const POLL_MS = 400;

// Beat durations at 1x, in ms. The stage is legible or it is decoration.
const BEAT = {
  flower: 700,
  run_started: 1400,
  round_started: 1500,
  broadcast: 1600,
  reply: 900,
  matrix: 2200,
  round_ended: 700,
  run_ended: 1400,
};

const FIRM_TONES = ['var(--firm-a)', 'var(--firm-b)', 'var(--firm-c)'];

// Predicate keys a firm can answer from its declared fields. Anything else has no banded
// source, so round 1 cannot match it at all and round 2 must read a narrative or a bio.
// This mirrors VOCABULARY in backend/schema.py plus the requirement-side `role`.
const DECLARED_KEYS = new Set([
  'sector', 'delivery', 'client_type', 'certification',
  'value_band', 'recency_band', 'credentials', 'role',
]);

const COST_LABEL = ['free', 'NDA-limited', 'sensitive', 'blocked'];

const el = (id) => document.getElementById(id);

const dom = {
  scenarioTitle: el('scenarioTitle'),
  scenarioHeadline: el('scenarioHeadline'),
  scenarioPick: el('scenarioPick'),
  narration: el('narration'),
  narrStep: el('narrStep'),
  narrText: el('narrText'),
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
  run: el('run'),
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
  detail: el('detail'),
  detailBody: el('detailBody'),
  detailClose: el('detailClose'),
};

const state = {
  url: LIVE_TRACE,
  events: [],
  cursor: 0,
  round: 1,
  playing: false,
  speed: 1,
  timer: null,
  built: false,
  firms: new Map(),   // firm name -> lane
  cells: new Map(),   // requirement id -> { node, met, need }
  reqs: new Map(),    // requirement id -> metadata from run_started
  rows: new Map(),    // requirement id -> latest matrix row
  reqChips: new Map(),
  raw: '',
  ref: null,
};

// ------------------------------------------------------------------ utilities

const bytes = (n) => (n < 1024 ? `${n} B` : `${(n / 1024).toFixed(1)} kB`);

const shortHandle = (h) => h.replace(/^FIRM_[A-Z]::/, '');

const shortFirm = (f) => f.replace(/^FIRM_/, 'Firm ');

const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));

function centre(node) {
  const box = node.getBoundingClientRect();
  const frame = dom.stage.getBoundingClientRect();
  return { x: box.left - frame.left + box.width / 2, y: box.top - frame.top + box.height / 2 };
}

function toneOf(firm) {
  return state.firms.get(firm)?.tone || 'var(--accent)';
}

// ------------------------------------------------------------------- building

function build(event) {
  const scenario = event.scenario || {};
  dom.scenarioTitle.textContent = scenario.title || event.solicitation;
  dom.scenarioHeadline.textContent = scenario.headline || '';
  if (scenario.slug && dom.scenarioPick.value !== scenario.slug) {
    // Keep the selector honest about which trace is on screen, including in live mode.
    const match = [...dom.scenarioPick.options].find((o) => o.value === scenario.slug);
    if (match && state.url !== LIVE_TRACE) dom.scenarioPick.value = scenario.slug;
  }

  dom.empty.hidden = true;
  dom.stage.hidden = false;
  dom.panels.hidden = false;
  dom.log.hidden = false;

  dom.reqStrip.innerHTML = '';
  dom.matrix.innerHTML = '';
  state.reqChips.clear();
  state.cells.clear();
  state.reqs.clear();
  state.rows.clear();

  for (const req of event.requirements) {
    state.reqs.set(req.id, req);

    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = req.id;
    chip.title = `${req.id} — ${req.description}`;
    chip.onclick = () => openDetail(req.id);
    dom.reqStrip.append(chip);
    state.reqChips.set(req.id, chip);

    const cell = document.createElement('div');
    cell.className = req.kind === 'MANDATORY' ? 'cell' : 'cell weighted';
    cell.title = `${req.description} — click for detail`;
    cell.innerHTML =
      `<div class="rid">${req.id}</div>` +
      `<div class="cnt">0 / ${req.min_count}</div>` +
      `<div class="kind">${req.kind === 'MANDATORY' ? 'must' : 'weighted'}</div>`;
    cell.onclick = () => openDetail(req.id);
    dom.matrix.append(cell);
    state.cells.set(req.id, { node: cell, met: false, need: req.min_count });
  }

  // Firm lanes are created from `run_started`'s node list so the stage has its shape
  // before any reply names a firm; the labels are filled in as the replies arrive.
  dom.firms.innerHTML = '';
  state.firms.clear();
  event.firms.forEach((placeholder, index) => lane(placeholder, index));

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

// ----------------------------------------------------------------- narration

// One plain-English sentence per beat, so a judge reading the page cold knows what the
// protocol is doing right now without anybody narrating it.
function narrate(event) {
  const n = (step, text, tone = '') => ({ step, text, tone });

  switch (event.type) {
    case 'run_started':
      return n('setup',
        `The solicitation is decomposed into <b>${event.requirements.length} typed requirements</b>. ` +
        `Three firms will bid it as one joint venture. They compete next month, so none of them ` +
        `may see another's client list, fees, or roster.`);

    case 'round_started':
      return event.gap.length
        ? n(`round ${event.round}`,
            `The consortium cannot evidence <b>${event.gap.join(', ')}</b>. The coordinator asks ` +
            `again — and this time each firm may read its own narratives and bios, not just its ` +
            `declared fields.`, 'gap')
        : n(`round ${event.round}`,
            `Blind attestation. Every firm searches <b>only its own library</b>, and none of them ` +
            `knows what the others hold.`);

    case 'broadcast':
      return event.gap.length
        ? n('broadcast',
            `Out goes the <b>gap and nothing else</b>: <code>${event.gap.join(',')}</code>, ` +
            `<b>${bytes(event.gap_bytes)}</b>. The firms are told there is a hole — never who has ` +
            `what, never the answer.`, 'gap')
        : n('broadcast',
            `All ${event.requirements} requirements go to all three firms, <b>${bytes(event.bytes)}</b>. ` +
            `Round 1 matches <b>declared fields only</b> — the reading each firm already had.`);

    case 'reply': {
      const who = shortFirm(event.firm);
      if (event.round > 1 && event.new_requirements.length) {
        return n('found',
          `<b>${who}</b> re-read its own library and found <b>${event.new_requirements.join(', ')}</b> — ` +
          `evidence that no structured search reached, because the fields never said so.`, 'win');
      }
      if (event.round > 1) {
        return n('reply', `<b>${who}</b> re-examined and found nothing new.`);
      }
      return n('reply',
        `<b>${who}</b> answers with <b>${event.attestations} attestations</b> — banded existence ` +
        `proofs, <b>${bytes(event.bytes)}</b>. Not one record left the building.`);
    }

    case 'matrix': {
      const missing = event.rows.filter((r) => !r.met && r.kind === 'MANDATORY').map((r) => r.id);
      if (event.closed?.length) {
        return n('closed',
          `<b>${event.closed.join(', ')} closed.</b> That firm only looked because it was told about ` +
          `a hole in <i>somebody else's</i> coverage. That is the multiplier.`, 'win');
      }
      if (missing.length && event.round === 1) {
        return n('gap found',
          `Joint coverage says <b>${missing.join(', ')} is uncovered</b> — while every firm's own ` +
          `self-assessment reads compliant. No single firm could have seen this.`, 'gap');
      }
      if (missing.length) {
        return n('still open',
          `<b>${missing.join(', ')}</b> is still uncovered after re-examination.`, 'gap');
      }
      return n('covered', `Every mandatory requirement is evidenced.`, 'win');
    }

    case 'round_ended':
      if (event.stopped === 'converged') {
        return n('converged', `Nothing left open — the protocol stops early rather than asking again.`, 'win');
      }
      if (event.stopped === 'no-new-evidence') {
        return n('stopped',
          `Re-examination returned nothing new, so another identical broadcast would only cost ` +
          `time. The protocol stops.`, 'gap');
      }
      return n(`round ${event.round}`, `Round ${event.round} closed. Carrying the gap into the next one.`);

    case 'run_ended':
      return event.compliant
        ? n('done',
            `Bid is <b>compliant</b> after ${event.rounds_run} rounds. ` +
            `<b>${bytes(event.banded_bytes)}</b> of banded attestations crossed the wire and ` +
            `<b>${event.record_bytes} bytes</b> of record content.`, 'win')
        : n('done',
            `Bid is <b>non-compliant</b> — <b>${event.mandatory_gaps.join(', ')}</b> unmet after ` +
            `${event.rounds_run} rounds. ${bytes(event.banded_bytes)} of attestations crossed; ` +
            `<b>${event.record_bytes} bytes</b> of record content did.`, 'gap');
  }
  return null;
}

function showNarration(event) {
  const line = narrate(event);
  if (!line) return;
  dom.narrStep.textContent = line.step;
  dom.narrText.innerHTML = line.text;
  dom.narration.className = `narration ${line.tone}`;
}

// ---------------------------------------------------------- requirement detail

function openDetail(rid) {
  const req = state.reqs.get(rid);
  if (!req) return;
  const row = state.rows.get(rid);
  const met = row?.met ?? false;
  const have = row?.have ?? 0;

  const parts = [
    `<div class="d-head">`,
    `<span class="d-rid ${met ? 'met' : 'miss'}">${req.id}</span>`,
    `<span class="d-badge ${req.kind === 'MANDATORY' ? 'must' : ''}">`,
    `${req.kind === 'MANDATORY' ? 'mandatory' : `weighted ${req.weight}`}</span>`,
    `<span class="d-badge">SF330 section ${req.section}</span>`,
    `<span class="d-badge ${met ? 'ok' : 'must'}">${have} of ${req.min_count} needed</span>`,
    `</div>`,
    `<p class="d-desc">${esc(req.description)}</p>`,
  ];

  parts.push(`<div class="d-section"><h3>What satisfies it</h3><div class="d-pred">`);
  for (const [key, value] of Object.entries(req.predicate)) {
    if (key === 'join') {
      parts.push(
        `<div><span class="k">join</span><span class="v">${esc(value)}</span>` +
        `<span class="note">the person must be booked to one of that firm's own projects</span></div>`);
      continue;
    }
    const field = key.replace(/_(min|max)$/, '');
    const bound = key.endsWith('_min') ? 'at least ' : key.endsWith('_max') ? 'at most ' : '';
    const declared = DECLARED_KEYS.has(field);
    parts.push(
      `<div><span class="k">${esc(field)}</span>` +
      `<span class="v">${bound}${esc(value)}</span>` +
      `<span class="note">${declared
        ? 'declared field — matchable in round 1'
        : 'no declared field carries this — only a narrative or bio can, which is round 2'}</span></div>`);
  }
  parts.push(`</div></div>`);

  parts.push(`<div class="d-section"><h3>Attested by</h3>`);
  const attested = row?.attested || [];
  if (!attested.length) {
    parts.push(
      `<p class="d-empty">Nothing yet. The coordinator knows this requirement is unmet and ` +
      `<em>nothing else</em> — not which firm is close, not what is missing from whose library.</p></div>`);
  } else {
    const byFirm = new Map();
    for (const a of attested) {
      if (!byFirm.has(a.firm)) byFirm.set(a.firm, []);
      byFirm.get(a.firm).push(a);
    }
    for (const [firm, items] of [...byFirm].sort()) {
      parts.push(
        `<div class="d-firm" style="--tone:${toneOf(firm)}">` +
        `<div class="d-firm-name">${shortFirm(firm)} — ${items.length}</div><div class="d-rows">`);
      for (const a of items) {
        const bands = Object.entries(a.banded).map(([k, v]) => `${k}=${v}`).join('  ');
        parts.push(
          `<div class="d-row"><span class="h">${esc(shortHandle(a.handle))}</span>` +
          `<span class="bands">${esc(bands)}</span>` +
          `<span class="cost c${a.disclosure_cost}">${COST_LABEL[a.disclosure_cost] || a.disclosure_cost}</span></div>`);
      }
      parts.push(`</div></div>`);
    }
    parts.push(
      `<p class="d-empty" style="margin-top:12px">Handles are opaque and firm-local. These bands ` +
      `are the whole of what crossed — no client, no fee, no name.</p></div>`);
  }

  dom.detailBody.innerHTML = parts.join('');
  dom.detail.showModal();
}

dom.detailClose.onclick = () => dom.detail.close();
dom.detail.onclick = (e) => { if (e.target === dom.detail) dom.detail.close(); };

// --------------------------------------------------------------------- apply

function apply(event) {
  logLine(event);
  showNarration(event);

  switch (event.type) {
    case 'run_started': {
      if (event.version !== SUPPORTED_VERSION) {
        dom.scenarioTitle.textContent =
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
      state.round = event.round;
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
      for (const chip of state.reqChips.values()) chip.classList.remove('live');
      for (const id of event.gap) state.reqChips.get(id)?.classList.add('live');

      const isGap = event.gap.length > 0;
      const label = isGap
        ? `gap ${event.gap.join(',')} · ${bytes(event.gap_bytes)}`
        : `RFP · ${bytes(event.bytes)}`;
      if (isGap) dom.mGap.textContent = bytes(event.gap_bytes);

      for (const entry of state.firms.values()) {
        entry.wire?.classList.add('hot');
        entry.card.classList.add('searching');
        fly(dom.coordinator, entry.card, {
          label, kind: isGap ? 'gap' : '', ms: (BEAT.broadcast / state.speed) * 0.7,
        });
      }
      break;
    }

    case 'reply': {
      const entry = laneFor(event.firm);
      const fresh = event.new_requirements.length > 0 && event.round > 1;
      entry.wire?.classList.remove('hot');
      entry.card.classList.remove('searching');
      if (fresh) entry.card.classList.add('found');
      entry.stateEl.textContent = event.round > 1
        ? (fresh ? `found ${event.new_requirements.join(',')}` : 'nothing new')
        : `${event.attestations} attested`;
      entry.countEl.textContent = event.attestations;
      entry.bytesEl.textContent = bytes(event.bytes);

      for (const handle of event.handles) {
        if (entry.handles.has(handle)) continue;
        entry.handles.add(handle);
        const chip = document.createElement('span');
        chip.className = fresh ? 'h fresh' : 'h';
        chip.textContent = shortHandle(handle);
        entry.handlesEl.append(chip);
      }

      fly(entry.card, dom.coordinator, {
        label: `${event.attestations} attestations · ${bytes(event.bytes)}`,
        tone: entry.tone,
        kind: fresh ? 'win' : 'reply',
        ms: (BEAT.reply / state.speed) * 0.8,
      });
      break;
    }

    case 'matrix': {
      dom.coordinator.classList.remove('busy');
      dom.coordinatorState.textContent = 'coverage recomputed';
      for (const row of event.rows) {
        state.rows.set(row.id, row);
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
  if (event.closed?.length) {
    dom.verdict.innerHTML =
      `<span class="good">${event.closed.join(', ')} closed</span> ` +
      `<span class="why">— re-examination found it after the gap was broadcast</span>`;
    return;
  }
  dom.verdict.innerHTML = mandatory.length
    ? `<span class="bad">NON-COMPLIANT</span> <span class="why">— mandatory gap: ${mandatory.join(', ')}. ` +
      `No single firm's own assessment shows this.</span>`
    : `<span class="good">COMPLIANT</span> <span class="why">— every mandatory requirement evidenced.</span>`;
}

function logLine(event) {
  const label = describe(event);
  if (!label) return;
  const li = document.createElement('li');
  li.innerHTML = `<span class="t">${event.t_ms.toFixed(1)}ms</span><span>${label}</span>`;
  if (event.type === 'broadcast' && event.gap?.length) li.className = 'key';
  if (event.type === 'reply' && event.new_requirements?.length && event.round > 1) li.className = 'win';
  if (event.type === 'matrix' && event.closed?.length) li.className = 'win';
  dom.logList.append(li);
  dom.logList.scrollTop = dom.logList.scrollHeight;
}

function describe(e) {
  switch (e.type) {
    case 'flower': return `flwr ${e.flwr} · ${e.runtime} · ${e.transport} · ${e.nodes} SuperNodes`;
    case 'run_started': return `trace v${e.version} · ${e.requirements.length} requirements · ${e.firms.length} firms`;
    case 'round_started': return `round ${e.round} — gap ${e.gap.join(',') || '—'}`;
    case 'broadcast': return `${e.transport ? `${e.transport}.send_and_receive · ` : ''}coordinator → all firms · ${bytes(e.bytes)}${e.gap.length ? ` · gap ${bytes(e.gap_bytes)}` : ''}`;
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
  state.timer = setTimeout(advance, (BEAT[event.type] ?? 600) / state.speed);
}

function play() {
  if (state.cursor >= state.events.length) reset();
  state.playing = true;
  dom.play.textContent = 'Pause';
  advance();
}

// Following a live run, not replaying one: carry on from wherever the cursor got to. A
// round-2 model call takes tens of seconds, so the page runs out of events long before the
// run ends — going through `play()` there would reset the cursor and restart the animation
// from round 1 every time a new batch landed.
function resume() {
  if (state.cursor >= state.events.length) return;
  state.playing = true;
  dom.play.textContent = 'Pause';
  advance();
}

function stop() {
  state.playing = false;
  clearTimeout(state.timer);
  const drained = state.cursor >= state.events.length;
  dom.play.textContent = drained ? 'Replay' : 'Play';

  const last = state.events[state.cursor - 1];
  if (drained && last && last.type !== 'run_ended' && dom.follow.checked) {
    dom.narrStep.textContent = 'thinking';
    dom.narrText.innerHTML =
      'Each firm is re-reading its own prose with its own model. Nothing has been sent to ' +
      'the coordinator, and nothing will be but a banded attestation.';
    dom.narration.className = 'narration waiting';
  }
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

// ------------------------------------------------------------------ starting a run
//
// `serve.py` spawns the protocol with stdout inherited, so pressing Run fills the terminal
// pane beside the page. The page's own job is only to go back to following the live trace,
// which the run truncates and rewrites.

const RUN_POLL_MS = 700;

function showRun({ running, exit }) {
  const failed = !running && exit != null && exit !== 0;
  dom.run.classList.toggle('busy', !!running);
  dom.run.classList.toggle('failed', failed);
  dom.run.disabled = !!running;
  dom.run.innerHTML = running ? 'Running…' : (failed ? 'Run failed' : 'Run ▸');
}

async function runState() {
  try {
    const res = await fetch('/run', { cache: 'no-store' });
    return res.ok ? await res.json() : null;
  } catch {
    return null;   // served as plain files, with no `serve.py` behind them
  }
}

async function watchRun() {
  const info = await runState();
  if (!info) return;
  showRun(info);
  if (info.running) setTimeout(watchRun, RUN_POLL_MS);
}

dom.run.onclick = async () => {
  const slug = dom.scenarioPick.value;

  // Point the page at the live trace before the run truncates it. Starting a run while
  // pinned to a stored scenario would leave the animation on the wrong file.
  dom.scenarioPick.value = '';
  dom.follow.checked = true;
  state.url = LIVE_TRACE;
  state.raw = '';
  state.ref = null;
  reset();

  showRun({ running: true });
  const res = await fetch(`/run?scenario=${encodeURIComponent(slug)}`, { method: 'POST' });
  // 409 means a run is already going, which the poll renders on its own.
  if (!res.ok && res.status !== 409) {
    showRun({ running: false, exit: 1 });
    return;
  }
  watchRun();
  poll();
};

dom.play.onclick = () => (state.playing ? stop() : play());
dom.step.onclick = () => { stop(); advance(); };
dom.restart.onclick = () => { reset(); play(); };
dom.speed.onchange = () => { state.speed = Number(dom.speed.value); };

// ---------------------------------------------------------------- the trace

function parse(text) {
  return text
    .split('\n')
    .filter((line) => line.trim())
    .map((line) => { try { return JSON.parse(line); } catch { return null; } })
    .filter(Boolean);
}

async function load({ autoplay }) {
  let text;
  try {
    const res = await fetch(`${state.url}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(res.status);
    text = await res.text();
  } catch {
    return false;
  }

  if (text === state.raw) return true;
  state.raw = text;
  const events = parse(text);
  if (!events.length) return false;

  // `started_at` is the run's identity. A different one means the backend truncated the
  // file and began again, so the page starts over rather than splicing two runs together.
  // Found by field rather than taken from events[0]: the first event is whatever the round
  // loop happens to emit first, and only `run_started` carries the stamp.
  const ref = events.find((e) => e.started_at)?.started_at;
  const restarted = ref !== state.ref || events.length < state.events.length;
  state.ref = ref;
  state.events = events;
  if (restarted) reset();
  if (autoplay && !state.playing) (restarted ? play : resume)();
  return true;
}

async function poll() {
  await load({ autoplay: true });
  if (dom.follow.checked && state.url === LIVE_TRACE) setTimeout(poll, POLL_MS);
}

dom.follow.onchange = () => { if (dom.follow.checked) poll(); };

// ------------------------------------------------------------------ scenarios

async function loadScenarios() {
  let index;
  try {
    const res = await fetch(`${INDEX_URL}?t=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) return;
    index = await res.json();
  } catch {
    return;
  }

  dom.scenarioPick.innerHTML = '<option value="">live run</option>';
  for (const scenario of index.scenarios) {
    const option = document.createElement('option');
    option.value = scenario.slug;
    option.textContent = scenario.available ? scenario.slug : `${scenario.slug} — not run`;
    option.disabled = !scenario.available;
    option.title = scenario.title;
    dom.scenarioPick.append(option);
  }
}

dom.scenarioPick.onchange = () => {
  const slug = dom.scenarioPick.value;
  // Switching to a stored scenario pins the page to that trace; following only ever makes
  // sense against the live one, which is the file the next run truncates.
  state.url = slug ? `state/trace-${slug}.jsonl` : LIVE_TRACE;
  state.raw = '';
  state.ref = null;
  dom.follow.checked = !slug;
  reset();
  if (slug) load({ autoplay: true });
  else poll();
};

// Polling a static file is free, so following is the default: it makes `make watch` fill
// the page as the rounds land, and picks up any later run without a reload.
loadScenarios().then(() => (dom.follow.checked ? poll() : load({ autoplay: true })));
watchRun();
