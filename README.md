# Consortium — a collaborative disclosure harness for Flower Agents

**Collaborative Agent Hackathon — Flower Labs, University of Cambridge, Wed 26 Aug 2026**
**Track 1: SuperGrid**

Consortium is a harness for agents that are not allowed to pool their data. Parties that
must jointly prove a property none of them can verify alone exchange **attestations** —
banded, anonymised evidence that a matching record exists — rather than records. The
coordinator finds the gap and broadcasts it, so each agent re-queries its *own* data with a
question it did not know to ask.

```
attest  ->  detect gap  ->  re-examine locally against the gap  ->  [minimise disclosure, gate on a human]
```

The first three stages run. The fourth — the disclosure optimiser and the human approval
gate — is designed (see the brief, §5.4) and **not built**; the stubs in `backend/` say so.
What ships is the part that carries the argument: no single party could have found the gap,
and closing it cost 2 bytes travelling back to the firms.

Three things are domain-specific and pluggable: a requirement set, a closed banding
vocabulary, and a disclosure-cost function. Four scenarios ship against the same harness.

## The reference application

Three architecture and engineering firms bid one federal healthcare project as a joint
venture, and compete against each other on the next three. To produce a compliant SF330
they must establish together that the team covers every requirement in the solicitation —
without any firm exposing its client relationships, contract values, or full roster.

*Three firms discover their joint bid is non-compliant, and fix it — while never naming a
confidential client and never putting a single byte of record content on the wire.*

The SF330 is the example; the harness is the product.

## Run it

From Flower Hub, on SuperGrid:

```bash
flwr login supergrid
flwr chat                 # then: @i53n1/consortium <solicitation>
```

Locally, as a three-node federated simulation:

```bash
make setup                                    # install dependencies
make doctor                                   # environment, FAB build, model, cache, traces
make stage  MODEL=/models/Qwen3.5-397B-A17B-FP8   # the demo: log in this pane, page in the browser
```

`make` on its own lists everything. `make stage` is the demo — it serves the page and waits;
press **Run** there and the protocol's log lands in the terminal pane beside it, so neither
half is a recording of the other. During a build the two you want are `make rounds` (the
federated protocol, streaming to the terminal) and `make check` (lint + invariant tests)
before you push.

### Round 2 needs a model

`MODEL=` is what enables round-2 re-examination, because round 2 is a model reading prose.
Without it the run is honest rather than broken: round 1 completes, R4 stays red, and the
harness reports the bid non-compliant.

Round 1 calls a model too, but only to **grade** what its structured prefilter already
matched — it may neither nominate a record nor veto one, so the coverage matrix is identical
with or without a model. Run `make rounds` both ways and diff it. The shared endpoints are in
`docs/event.md`:

```bash
export FLWR_MODEL_API_ENDPOINT='http://129.212.182.232:8001/v1/responses'
unset FLWR_MODEL_API_KEY                      # Qwen takes no key — an empty one fails
make rounds MODEL=/models/Qwen3.5-397B-A17B-FP8
```

Responses are cached under `.cache/model/`, keyed on the exact request. **Editing either
prompt invalidates the cache for that round** — re-warm with `make traces MODEL=…` while an
endpoint is reachable, or the demo falls back to an open gap. Warm each scenario twice:
round-1 grading has a 120s budget and times out on a cold cache against the shared endpoint,
leaving the call to finish into the cache for the next run. `make doctor` reports what is
cached.

The simulation runs **three** supernodes because three firms is the scenario — Flower 1.34
defaults to two, so `make rounds` passes the count explicitly. Override the count, the
rounds, the scenario, or the UI port on the command line:

```bash
make rounds SUPERNODES=2 ROUNDS=1 SCENARIO=transit-tunnel
```

`make help` lists the scenario slugs. `make traces` runs every scenario once so the UI's
selector can switch between them with no re-run and no network.

## Layout

| Directory | Owner | Contents |
|---|---|---|
| `data/` | Data | Four solicitations, per-firm corpora, closed vocabulary, derived ground truth |
| `backend/` | Flower + Fusion | Protocol loop, firm node, both app surfaces, scenarios, event trace |
| `agents/` | Agent | Round-2 re-examination, model client and cache, prompts |
| `frontend/` | Viz | Coverage matrix, disclosure ledger, event replay — local demo skin |
| `docs/` | all | Brief, demo script, decisions, the organisers' post |
| `tests/` | all | Invariants on the schema and the corpora |

Each directory has a README naming what it holds, what is **not** built, and the invariants
that actually hold there. `backend/` and `agents/` are the two importable packages, and the
dependency runs one way: `agents` imports `backend.schema` and nothing else from `backend`.

### One protocol, two surfaces

`backend/protocol.py` owns the round loop and neither surface owns it:

- **`backend/agent_app.py`** — the `AgentApp` published to Hub and driven from `flwr chat`.
  It has no `Grid`, so the loop runs over `backend/local_grid.py`, one `Context` per firm.
- **`backend/server_app.py`** — the `ServerApp`, same loop over a real grid, one SuperNode
  per firm. Driven by `make rounds`.

The published FAB declares `agentapp` **only**: Hub rejects a bundle carrying both
surfaces (`422`), and the SuperLink derives the task type from that declaration alone — so
`flwr run .` starts the harness, and the federated surface goes through
`flwr.simulation.run_simulation` instead. `docs/decisions.md` records that call.

`frontend/` is a local skin over the JSON the backend writes. Hub accepts only `.py`,
`.toml`, `.md`, `.yaml`, `.json` and `.jsonl`, so HTML, CSS and JS are excluded from the
published app — the shipped output surface is `protocol.render()`, which prints the
coverage matrix as text. See brief §10.3.

## Working in this repo

Read **`CLAUDE.md`** before your first commit. Two rules decide whether four people on one
branch works: every task runs in its own **git worktree**, and `main` is the **only**
branch on `origin`.

The plan — submission gates, pitch, architecture, Hub publishing runbook, task breakdown,
milestones, cut list, judge Q&A — is `docs/consortium-brief.md`. It is the plan **as
written at the start of the day** and has not been rewritten to match what got built;
`docs/README.md` lists where the two diverge, and the per-directory READMEs are the
authority on what exists.
