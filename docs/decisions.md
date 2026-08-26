# Decisions taken on the day

One line each: what was decided, when, and why. This is the record that stops the same
argument happening twice under time pressure.

| Time | Decision | Why |
|---|---|---|
| — | **Track 1: SuperGrid.** That is what goes on the submission form. | The forum post offers only Track 1 (SuperGrid) and Track 2 (Infrastructure); "Flower Agent Harness" is our own framing and appears nowhere the organisers wrote. Track 1 is the tighter brief and matches what we are building. |
| ~10:45 | **Flower account `i53n1` owns the publish.** `publisher = "i53n1"`, app name `consortium`, live at `flower.ai/apps/i53n1/consortium/`. | Both are immutable after the first publish. Settled before any scenario code so R0 could not bite late. |
| ~11:20 | **Attestation schema frozen** — `backend/schema.py`, `Attestation` + `Requirement` + the closed `VOCABULARY`. | Everything downstream depends on the shape. The privacy boundary is structural: no field on an `Attestation` can carry a client name, a fee, or a person's identity, so `record_bytes` is 0 by construction rather than by policy. |
| ~11:30 | **Stub app published to Hub and run on SuperGrid.** | Both submission gates provisionally cleared before writing scenario code, per brief R0. |
| **~12:00** | **The FAB declares `agentapp` only** — not `agentapp` + `serverapp` + `clientapp` in one bundle, and not the two-project fallback either. | Hub returns `422 — must contain either only 'agentapp' or exactly 'serverapp' and 'clientapp'`. The local CLI validates all three happily, so this only surfaces at publish time. This is brief §6.1 resolved, and it resolved *against* the plan's preferred option. |
| ~12:00 | Consequence of the above: **the federated surface runs through `flwr.simulation.run_simulation`**, driven by `backend/rounds.py` (`make rounds`), not `flwr run .`. | The SuperLink derives the task type from the FAB's declaration alone (`_get_app_type`), so every `flwr run .` of this project starts the harness and `--federation-config num-supernodes=N` is accepted and silently ignored. `run_simulation` takes the apps directly and does not care what the FAB declares. |
| ~12:00 | Consequence again: **the round loop moved out of `server_app.py` into `backend/protocol.py`**, parameterised by a `Grid`. `backend/local_grid.py` is an in-process `Grid` for the AgentApp, which gets none. | Neither surface owns the protocol; both call it. The AgentApp process receives only `(agent, context)` and the runtime strips `flwr` from the app's dependencies, so `run_simulation` cannot be imported there either. |
| ~13:00 | **Corpora committed — four scenarios, not one.** `healthcare-seismic` (default), `transit-tunnel`, `defence-secure-lab`, `campus-decarbonisation`. | The close is "swap the requirement set, the vocabulary and the cost function and the same harness runs somewhere else", and that claim is worth what the second, third and fourth dataset behind it are worth. No cut to two firms was needed. |
| ~13:00 | **`vocabulary.json` stays frozen against `backend/schema.py` across all four scenarios**, asserted by a test. | A scenario needing a new sector would be a schema change, not a data change. Swapping the vocabulary is a roadmap line (brief §14), not a build-day one. |
| ~14:00 | **Round 2 reads prose with a model, and gets no keyword list.** | `data/scenarios.json` carries an evidence lexicon, but that is the oracle `data/generate.py` uses to prove the cell is findable. Handing it to a node would be handing it the answer key. |
| ~14:00 | **The round-2 prompt was the bug, not the corpus.** | An earlier version paired "judge the substance, not the vocabulary" with "do not infer beyond the text", and Qwen3.5 resolved the contradiction the strict way — refusing every scenario's evidence. This inverts brief R2's mitigation: check the prompt *first*, it is cheaper and it is what was wrong. Recorded in `agents/prompts/round2_reexamine.md`. |
| ~14:30 | **Round 1 grades the shortlist with a model, but may not nominate or veto.** `corroborated` → strength 1.0, `thin` → 0.7, both above tau. | The coverage matrix must be identical with or without a model: nomination would find the Section G cell a round early and kill the round-2 beat, and a veto would put the harness below `round_one_coverage` in its own ground truth on a sampled completion. Enforced in `agents/matcher.py`, not just asked for in the prompt. |
| ~14:30 | **One round-1 call per firm for the whole matrix**, not one per requirement. | Round trips are the cost that matters, not tokens. Per requirement it was eighteen calls a run and ~2 min a firm cold; this is three calls and one wait, and one cache entry per firm per scenario so a rehearsal replays whole rather than partially. |
| ~14:30 | **The demo is a split screen, driven from the page.** `make stage` serves the UI; `POST /run` spawns the protocol with **stdout inherited** so the log lands in the terminal pane beside the browser. | Neither half is a recording of the other. `serve.py` binds `127.0.0.1` only — it spawns subprocesses on an unauthenticated POST, and conference wifi is not the place to listen on `0.0.0.0`. |

## Still open at the time of writing

- **Stage four of the loop is not built.** The disclosure optimiser (`backend/optimiser.py`),
  the approval gate (`approval.py`), SF330 assembly (`assemble.py`) and the three-condition
  baselines (`baselines.py`) are docstring-only stubs. `make baselines` runs and prints
  nothing. The demo script says how to answer for it; `backend/README.md` lists what landed
  where instead.
- **There is no bander.** Banding happens in `backend/firm_node.py` and bytes are counted in
  `backend/trace.py`, but nothing validates on egress and there is no rejection counter. The
  privacy property is structural instead of enforced — which is the stronger claim, but it is
  a different claim from the one brief §7.2 scores.

## Decisions the brief scheduled that no longer apply

- **13:00 cut to two firms and six projects each** — not needed, corpora landed on time.
- **The two-project publishing fallback** (brief §6.1) — superseded by the agentapp-only
  bundle above.

## Still to come

- **16:30** — final version published and verified from a clean shell.
- **16:50** — code freeze.
- **17:30** — demos ready. Rehearse twice against `demo-script.md`, timed.
