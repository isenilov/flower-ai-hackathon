# Consortium — Federated Bid Assembly

**Collaborative Agent Hackathon — Flower Labs, University of Cambridge, Wed 26 Aug 2026**

Three architecture and engineering firms bid one federal healthcare project as a joint
venture, and compete against each other on the next three. To produce a compliant SF330
they must establish together that the team covers every requirement in the solicitation —
without any firm exposing its client relationships, contract values, or full roster.

Consortium puts an agent next to each firm's private library. The agents establish
compliance by exchanging **attestations** — banded, anonymised evidence that a matching
record exists — never the records. A coordinator computes the minimum set of disclosures
that makes the bid compliant, each firm's BD lead approves their own releases individually,
and only then does real content flow into the document.

*Three firms discover their joint bid is non-compliant, fix it, and assemble the SF330 —
while each firm releases three records out of forty and never names its confidential
clients.*

## Run it

```bash
make setup     # install dependencies
make doctor    # verify the environment against the brief's §9.1 / §9.2 checklist
make demo      # clean state -> three rounds -> baselines -> UI
```

`make` on its own lists everything. During the build the two you want are `make rounds`
(the federated protocol, streaming) and `make check` (lint + invariant tests) before you
push.

The simulation runs **three** supernodes because three firms is the scenario — Flower 1.34
defaults to two, so `make rounds` passes the count explicitly. Override it, the round count,
or the UI port on the command line: `make rounds SUPERNODES=2 ROUNDS=1`.

## Layout

| Directory | Owner | Contents |
|---|---|---|
| `data/` | Data | Solicitation, per-firm corpora, closed vocabulary, ground truth |
| `backend/` | Flower + Fusion | Coordinator, firm node, transport, bander, optimiser, assembly, baselines |
| `agents/` | Agent | Per-firm matcher, local search, round-2 re-examination, prompts |
| `frontend/` | Viz | Coverage matrix, disclosure ledger, SF330 render |
| `docs/` | all | Brief, demo script, decisions |
| `tests/` | all | Invariants on the schema and the corpora |

Each directory has a README naming the modules, their owning task, and the invariants
that hold there.

## Working in this repo

Read **`CLAUDE.md`** before your first commit. Two rules decide whether four people on one
branch works: every task runs in its own **git worktree**, and `main` is the **only**
branch on `origin`.

The plan — pitch, architecture, scenario, task breakdown, milestones, cut list, judge Q&A —
is `docs/consortium-brief.md`.
