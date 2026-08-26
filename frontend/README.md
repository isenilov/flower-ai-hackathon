# frontend — the process, visualised

Owner: **Viz** (T13, T14, T15).

Static HTML and vanilla JS. No framework, no build step. The backend appends protocol
events to `state/trace.jsonl` and this page replays them.

```bash
make stage      # THE DEMO — split screen: log in this pane, page in the browser
make watch      # page up first, then the protocol runs into it — watch it land live
make traces     # run every scenario once, so the selector can switch offline
make rounds     # just write frontend/state/trace.jsonl
make ui         # just serve this directory on :8000, replaying whatever trace exists
```

Any of them takes `SCENARIO=<slug>`; empty uses the manifest default. `make help` lists
the slugs. All of them take `MODEL=` — without it round 2 finds nothing and every scenario
traces as non-compliant, which is why `make traces` warns when it is empty.

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
| `serve.py` | Static server, caching off, plus `POST /run` — the page's Run button |
| `state/` | Written by the backend, gitignored. Never hand-edited. |

## The split screen — `make stage`

This is the demo. Terminal pane on the left, browser on the right, and every run driven from
the page's **Run** button rather than from a second terminal.

`POST /run` spawns `python -m backend.rounds` with **stdout inherited**, so the protocol's
log lands in the same pane `serve.py` is running in while the animation plays beside it.
Neither half is a recording of the other, and a judge can look from one to the other and see
the same run — `backend/ansi.py` paints the terminal with the literal colour tokens out of
`styles.css`, so firm B is the same amber in both.

`serve.py` binds **`127.0.0.1` only**: it spawns subprocesses on an unauthenticated POST, and
conference wifi is not the place to listen on `0.0.0.0`. One run at a time; a second Run
while one is in flight is refused rather than queued.

`--quiet` (passed by `make watch`, and by every run the Run button starts) drops Flower's
six-line `run_simulation` deprecation notice and Ray's accelerator `FutureWarning` — the two
things that shout over the protocol without telling a viewer anything. It does not touch the
matrix or the SF330 table; those still print. `make stage` does not run the protocol at all —
it waits for you to press Run.

## The trace contract

`backend/trace.py` owns the format; this page reads it. One JSON object per line, each with
`type`, `seq`, and `t_ms` (monotonic ms from the start of the run). `run_started.version`
must equal the `SUPPORTED_VERSION` in `app.js` — on a mismatch the page says so instead of
rendering half a run. **Adding a field is safe; renaming or removing one breaks this page.**

| Event | Carries |
|---|---|
| `flower` | `flwr` (version), `runtime`, `transport`, `nodes` — emitted first, before `run_started`. The `Grid` class is the honest name for the wire: `InMemoryGrid` under the simulation runtime, `GrpcGrid` against a real SuperLink, `LocalGrid` inside the published harness. Same protocol, three transports. |
| `run_started` | `version`, `started_at`, `scenario{slug,title,headline,gap}`, `solicitation`, `as_of`, `num_rounds`, `firms`, `requirements[]` (each with `predicate`) |
| `round_started` | `round`, `gap[]` |
| `broadcast` | `round`, `gap[]`, `requirements`, `bytes`, `gap_bytes`, `reads_text`, `to[]`, `messages`, `message_type`, `transport` |
| `reply` | `round`, `firm`, `attestations`, `bytes`, `per_requirement`, `new_requirements[]`, `handles[]` |
| `matrix` | `round`, `rows[]` (each with `attested[]`: firm, handle, kind, `disclosure_cost`, `banded`), `open_gaps[]`, `closed[]` |
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

## Scenarios

`data/scenarios.json` is the manifest; `backend/scenarios.py` is the only thing that reads
it on the run path. Every scenario uses the same requirement ids and record shapes, so
nothing here branches per scenario.

Each run writes its trace twice — `trace.jsonl` for a following page, and
`trace-<slug>.jsonl` for the selector — plus `state/scenarios.json`, which is how the page
learns the catalogue without being able to read `data/`. A scenario the selector shows as
`not run` has no trace yet; `make traces` fills them all in.

`make reset` clears only the live trace, so the snapshots survive every later run —
`make reset-traces` is the one that drops them.

**Before the demo, run `make traces`.** The selector then switches between scenarios
instantly with no re-run and no network, which is what you want with a judge at the table.

## Reading the page

- **The narration bar** under the scenario title says what the protocol is doing right
  now, in one sentence. It is derived from the current event, not scripted, so it stays
  true on any scenario. Judges read the page cold; this is the line that lets them.
- **Click any requirement** — a coverage cell or a chip on the coordinator — for what
  satisfies it, which predicate keys are declared fields versus text-only (the round
  boundary, made explicit), and every attestation behind it with its disclosure cost. An
  uncovered requirement says what the coordinator knows, which is *only* that it is unmet.

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

`frontend/` was **cut candidate #1 and #2** on the brief's cut list and ended up neither cut
nor cut-down — it became the demo surface (brief §11). It stays cut-safe anyway:
`backend/trace.py` prints every event to the terminal, which is what ships inside the FAB. If
this page does not land, the argument survives in the log — and `make stage` shows both halves
at once precisely because the terminal half is the one that cannot fail.
