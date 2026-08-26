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
| ~15:00 | **`make publish` publishes a staged tree, not the repo root.** `publish-stage.sh` copies `README.md`, `LICENSE`, `pyproject.toml`, `agents/`, `backend/` and `data/` into a directory named for the app, drops `fab-exclude` from the staged `pyproject.toml`, and publishes that. | **`flwr app publish` never reads `fab-exclude`** — only `flwr build` does (`flwr/cli/build.py`). Publish filters on the extension allowlist, `.flwr/`, `__pycache__` and `.gitignore`, so 0.1.0–0.3.0 all shipped `docs/`, `tests/`, `frontend/`, `CLAUDE.md` and the deck's 358 KB `package-lock.json`: 71 files, 832 KB against the staged 55 files, 312 KB. The staged `fab-exclude` has to go because `flwr build` raises on an exclude pattern that matches no file, and Hub builds the FAB server-side. |
| ~15:45 | **`make grid` runs the federated surface on SuperGrid, one SuperNode per firm**, from a staged second app declaring `serverapp` + `clientapp` (`grid-stage.sh`). | A run is not a publish. Hub rejects a mixed bundle, but `flwr run <dir>` uploads a FAB the SuperLink builds without ever consulting Hub — so the two surfaces can be two app *directories* even though they cannot be two *components* of one. This reopens what the 12:00 decision closed: `run_simulation` is no longer the only way to get per-node isolation. The proof it is real rather than nominal is `flwr ls --format json` — `clientapp-seconds: 8.2` for this, `0.0` for the agentapp, which does all three firms' work in one task. |
| ~15:45 | **`SUPERLINK` defaults to `supergrid`, and both SuperGrid targets pass `--federation @i53n1/workspace`.** | An empty `SUPERLINK` resolves to whatever `~/.flwr/config.toml` calls `default`, which is `local`. `make harness` therefore never reached SuperGrid at all, and nothing it ran appeared in the federation's runs tab — which is the thing a judge is shown. `@i53n1/personal` is deployment-runtime with zero SuperNodes registered, so the simulation-runtime `workspace` federation is the only one that can stand the nodes up. |
| ~15:45 | **On SuperGrid a firm node reaches its model through the endpoint SuperGrid injects, not one we pass it.** `GRID_MODEL` follows `HARNESS_MODEL`, so both SuperGrid targets ask for the same id. | SuperGrid does not route to the organisers' endpoints — a node posting to one gets `403 Forbidden`, keyless Qwen included. It injects its own `FLWR_MODEL_API_ENDPOINT` instead, which from inside a ClientApp is an in-cluster key proxy holding the key itself, so nothing has to carry one there. That proxy has its own id namespace, independently confirming what `docs/event.md` records: it answers `openai/gpt-5.5`, and also `glm-5.2`, `minimax-m3` and `gpt-oss-120b`, while `glm-5.2-fp8` — correct for a direct call, and what `.env` holds — is refused with `400 {"detail":"glm-5.2-fp8 is not a valid model ID"}`. `HttpReader` now raises with the response body attached, which is the only reason that sentence is quotable rather than a bare 400. |
| ~16:00 | **`client-resources-num-cpus = 1` on the federation, so three firms get three ClientAppActors.** | At the default of 2, the container's CPU budget fitted two actors for three SuperNodes and Ray multiplexed them: two firms shared a process and answered one after the other. Visible in the log as the same `(ClientAppActor pid=…)` in front of two different firms — and misleading, because the pid is a pooled worker, not a node. Isolation is by `Context` either way, but round 2 has every firm waiting on a model, and serialising two of those spends a five-minute task budget that three in parallel fit inside. |

| ~16:15 | **The trace rides home in the run's own log, so the page follows a SuperGrid run.** A fourth sink in `backend/trace.py` behind `trace-to-log`, read back by `python -m backend.trace` at the far end of `make grid`'s pipe. `make grid-watch` is the split screen for it. | The JSONL sink is written inside the container and discarded with it, so the page was following a file nothing wrote. Of the sinks, only the log crosses the boundary — `--stream` already carries the whole run — so the events travel as JSON behind a sentinel and are rebuilt into the same two paths at this end. The page cannot tell a remote run from a local one, which is the point: no second renderer, and no bridge process to babysit. Recovering zero events is a non-zero exit, because a page silently following an empty file is the failure nobody notices until the demo. |

## Still open at the time of writing

- **`SUPERNODES` above 3 silently repeats firms.** `load_library` maps a node to a corpus
  with `FIRMS[partition_id % 3]`, so `make grid SUPERNODES=6` gives two firm A's, two B's and
  two C's rather than an error. Pre-existing, and it applies to `make rounds` the same way.

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
- **The two-project fallback for *publishing*** (brief §6.1) — still superseded for that, but
  it came back at 15:45 for *running*: see `grid-stage.sh`. Hub rejects a mixed bundle;
  `flwr run` never asks Hub. The original note, kept because the publishing half still holds:
- **The two-project publishing fallback** (brief §6.1) — superseded by the agentapp-only
  bundle above.

## Still to come

- **16:30** — final version published and verified from a clean shell.
- **16:50** — code freeze.
- **17:30** — demos ready. Rehearse twice against `demo-script.md`, timed.
