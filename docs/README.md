# docs

| File | Contents |
|---|---|
| `consortium-brief.md` | **The plan, as written at the start of the day.** Track and submission gates, pitch, architecture, Flower/Hub mapping, publishing runbook, task breakdown, milestones, cut list, judge Q&A. Read this first — §0 tells you what we actually have to hand in. Not rewritten to match the build: see below. |
| `demo-script.md` | The 4-minute table demo, the 90-second cut, and the stage version. Every beat in it has been run end to end; the numbers are measured. Rehearsed twice, timed, between the 16:50 freeze and 17:30. |
| `decisions.md` | Decisions actually taken, with the reason each one went the way it did. The 12:00 packaging call is the one that reshaped the codebase. |
| `event.md` | The organisers' post: schedule, venue, Slack, required docs, shared model endpoints and keys, submission fields, judging axes. Go here before re-reading the forum thread. |

Track: **Track 1 — SuperGrid**, which is the name that goes on the submission form; "agent
harness" is how we describe what we built, not a track. Two submission gates — a published
Flower Hub app and a public open-source repo — and six scored axes. Brief §0 is the map
from each axis to the artefact that evidences it.

The working agreement — worktrees, the single `main` branch, directory ownership — is in
`CLAUDE.md` at the repo root, not here.

## The brief is the plan, not the description

`consortium-brief.md` is deliberately **not** kept in sync with the code. It is the record of
what we intended at 10:30, and rewriting it would destroy the only copy of that. For what
exists, the per-directory READMEs are the authority — each one names what landed, what did
not, and the invariants that actually hold.

Where the two diverge, and why:

| Brief says | Reality | Why |
|---|---|---|
| §6.1, §10.2, appendix: one FAB declaring `agentapp` + `serverapp` + `clientapp` | **`agentapp` only.** The federated surface runs via `run_simulation`, driven by `backend/rounds.py`. | Hub returns `422` on a mixed bundle. Only surfaces at publish time — the local CLI validates all three happily. `decisions.md`, ~12:00. |
| §5.1, appendix: the round loop lives in `server_app.py` | **`backend/protocol.py`**, parameterised by a `Grid`. Two thin surfaces call it; `backend/local_grid.py` is an in-process `Grid` for the AgentApp, which gets none. | Follows from the above. Neither surface can own a loop they both need. |
| Appendix: `backend/render.py` is the shipped text surface | **`protocol.render()`.** `render.py` was never created. | The renderer is four lines of the protocol module's output; a file for it earned nothing. |
| T13/T14: text renderer *and* an HTML skin over "the same JSON" | The page reads a **protocol event trace** (`backend/trace.py` → `state/trace.jsonl`), not a result document, and replays it on its own clock. | A result document cannot show *when* something crossed the boundary, and the argument is about the boundary. |
| §5.1, T9: `bander.py` validates every attestation on egress and counts rejections | **No bander.** Banding is in `firm_node.py`; bytes are counted in `trace.py`; nothing validates on egress and nothing is rejected. | Not built. The privacy property ended up **structural** — no field on an `Attestation` can carry record content — which is a stronger claim but not the one §7.2 scores. Do not narrate a guardrail firing. |
| §5.4, T10–T12, T14: disclosure optimiser, approval gate, SF330 assembly, three-condition baselines | **Docstring-only stubs.** `make baselines` prints nothing. | Stage four of the loop did not get built. `data/ground_truth.json` holds the three readings the baseline table would score, and the corpus rules the optimiser would need are enforced by tests — but nothing measures them in a run. |
| T4/T6: round 1 is a model matching records | Round 1 is a **structured prefilter** (`agents/search.py`) plus a model that **grades** what the prefilter admitted (`agents/matcher.py`) and may neither nominate nor veto. | The coverage matrix has to be identical with or without a model, or the round-2 beat is either pre-empted or unreliable. `decisions.md`, ~14:30. |
| R5: "target ≤ 50 model calls per full run" | **Three** in round 1 — one per firm for the whole matrix — plus one per firm per uncovered requirement in round 2. | Round trips are the cost that matters, not tokens. |
| R2: "if round 2 misses the match, edit the corpus, not the prompt" | **Inverted.** The failure we actually hit was the prompt contradicting itself; the corpora were fine. | Recorded at the top of `agents/prompts/round2_reexamine.md`. Check the prompt first — it is cheaper and it is what was wrong. |
| Milestones: 3 rounds | The loop **converges at round 2** and stops — `stopped: "converged"` in the trace. | A third identical broadcast costs time and finds nothing. `ROUNDS` is the ceiling, not the count. |

Two things the brief planned that landed *bigger* than planned: four scenarios instead of one
(`data/README.md`), and a split-screen demo driven from the page with the protocol's log in
the terminal beside it (`make stage`, `frontend/README.md`).
