# frontend — the process, visualised

Owner: **Viz** (T13, T14, T15).

Static HTML and vanilla JS. No framework, no build step. The backend appends protocol
events to `state/trace.jsonl` and this page replays them.

```bash
make rounds     # writes frontend/state/trace.jsonl
make ui         # serves this directory on :8000
```

Open it directly if you prefer, but `fetch` of the trace needs a server — `file://` will
show the empty state.

| File | Shows |
|---|---|
| `index.html` | Stage (coordinator + three firm nodes), coverage matrix, disclosure ledger, event log |
| `app.js` | Reads `state/trace.jsonl`, replays it on a clock, animates the packets |
| `styles.css` | Styling. Red cell / green cell is the whole visual argument. |
| `state/` | Written by the backend, gitignored. Never hand-edited. |

## The trace contract

`backend/trace.py` owns the format; this page reads it. One JSON object per line, each with
`type`, `seq`, and `t_ms` (monotonic ms from the start of the run). `run_started.version`
must equal the `SUPPORTED_VERSION` in `app.js` — on a mismatch the page says so instead of
rendering half a run. **Adding a field is safe; renaming or removing one breaks this page.**

| Event | Carries |
|---|---|
| `run_started` | `version`, `solicitation`, `as_of`, `num_rounds`, `firms`, `requirements[]` |
| `round_started` | `round`, `gap[]` |
| `broadcast` | `round`, `gap[]`, `requirements`, `bytes`, `gap_bytes`, `reads_text` |
| `reply` | `round`, `firm`, `attestations`, `bytes`, `per_requirement`, `new_requirements[]`, `handles[]` |
| `matrix` | `round`, `rows[]`, `open_gaps[]`, `closed[]` |
| `round_ended` | `round`, `open_gaps[]`, `stopped` |
| `run_ended` | `rounds_run`, `open_gaps[]`, `mandatory_gaps[]`, `compliant`, `banded_bytes`, `record_bytes` |

## Why replay rather than live tail

With no model in the loop a whole run lands in about 40ms, so a live tail is a flash. The
page drives the event list off its own clock — play/pause, `Step ›`, and 0.5–4× — so the
narrator can hold on round 2 for as long as the question takes. `t_ms` is still shown, so
the timings on screen are the measured ones, not the presentation ones.

Tick **follow** to poll the file instead and pick up a run as it happens; a trace shorter
than the one in hand means a new run started, and the page resets. That becomes the useful
mode once `agents/matcher.py` puts real model calls in each round and a round takes seconds.

## What the stage is arguing

- **The dashed perimeter around each firm never opens.** What crosses is a handle and a
  band, and the handle chips inside each card are exactly what the coordinator received —
  opaque, firm-local, no client name, no fee, no person.
- **The gap packet is the beat.** Round 2 broadcasts `R4` and nothing else. The ledger shows
  what that cost: **2 bytes back to the firms** against ~32 kB of attestations forward.
- **`record content on the wire: 0 B`** is zero by construction, not by policy — no field in
  the protocol can carry it. The approval gate (T11) is what makes it non-zero.
- A firm reply that speaks to a requirement it did not answer last round is marked
  `+R4` and its new handle chip glows. That delta is the whole "multiplier" claim.

`frontend/` is **cut candidate #1 and #2** on the brief's cut list, and it stays cut-safe:
`backend/trace.py` also prints every event to the terminal, which is what ships inside the
FAB. If this page does not land, the argument survives in the log.
