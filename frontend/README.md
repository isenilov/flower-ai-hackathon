# frontend — the process, visualised

Owner: **Viz** (T13, T14, T15).

Static HTML and vanilla JS. No framework, no build step. The backend appends protocol
events to `state/trace.jsonl` and this page replays them.

```bash
make watch      # page up first, then the protocol runs into it — watch it land live
make rounds     # just write frontend/state/trace.jsonl
make ui         # just serve this directory on :8000, replaying whatever trace exists
```

`make rounds && make ui` is the wrong order to watch anything: the protocol finishes before
the page can exist, so you only ever get the replay. `make watch` serves first and runs the
protocol into the open page.

Opening `index.html` directly does not work — `fetch` of the trace needs a server, so
`file://` shows the empty state. `serve.py` is that server; it strips the request's
`If-Modified-Since` so an edited `app.js` is never answered with a 304.

| File | Shows |
|---|---|
| `index.html` | Stage (coordinator + three firm nodes), coverage matrix, disclosure ledger, event log |
| `app.js` | Reads `state/trace.jsonl`, replays it on a clock, animates the packets |
| `styles.css` | Styling. Red cell / green cell is the whole visual argument. |
| `serve.py` | Static server with caching off, so a mid-rehearsal edit actually shows |
| `state/` | Written by the backend, gitignored. Never hand-edited. |

## The trace contract

`backend/trace.py` owns the format; this page reads it. One JSON object per line, each with
`type`, `seq`, and `t_ms` (monotonic ms from the start of the run). `run_started.version`
must equal the `SUPPORTED_VERSION` in `app.js` — on a mismatch the page says so instead of
rendering half a run. **Adding a field is safe; renaming or removing one breaks this page.**

| Event | Carries |
|---|---|
| `run_started` | `version`, `started_at`, `solicitation`, `as_of`, `num_rounds`, `firms`, `requirements[]` |
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

**follow** is on by default and polls the file, so a run started after the page opened
lands on screen as it happens — that is what `make watch` relies on. A changed
`run_started.started_at` means the backend truncated the file and began again, so the page
starts over rather than splicing two runs together. Untick it to pin the page to one trace.

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
