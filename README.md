# Consortium — a collaborative disclosure harness for Flower Agents

**Collaborative Agent Hackathon — Flower Labs, University of Cambridge, Wed 26 Aug 2026**
**Track: Flower Agent Harness**

Consortium is a harness for agents that are not allowed to pool their data. Parties that
must jointly prove a property none of them can verify alone exchange **attestations** —
banded, anonymised evidence that a matching record exists — rather than records. The
coordinator finds the gap, broadcasts it so each agent re-queries its *own* data with a
question it did not know to ask, then solves for the minimum set of disclosures that closes
the gap and routes each one through a human owner.

```
attest  ->  detect gap  ->  re-examine locally against the gap  ->  minimise disclosure, gate on a human
```

Three things are domain-specific and pluggable: a requirement set, a closed banding
vocabulary, and a disclosure-cost function.

## The reference application

Three architecture and engineering firms bid one federal healthcare project as a joint
venture, and compete against each other on the next three. To produce a compliant SF330
they must establish together that the team covers every requirement in the solicitation —
without any firm exposing its client relationships, contract values, or full roster.

*Three firms discover their joint bid is non-compliant, fix it, and assemble the SF330 —
while each firm releases nine records out of forty and never names its confidential
clients.*

The SF330 is the example; the harness is the product.

## Run it

From Flower Hub, on SuperGrid:

```bash
flwr login supergrid
flwr chat                 # then: @<publisher>/consortium <solicitation>
```

Locally, as a three-node federated simulation:

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
| `frontend/` | Viz | Coverage matrix, disclosure ledger, SF330 render — local demo skin |
| `docs/` | all | Brief, demo script, decisions |
| `tests/` | all | Invariants on the schema and the corpora |

Each directory has a README naming the modules, their owning task, and the invariants
that hold there.

`frontend/` is a local skin over the JSON the backend writes. Flower Hub accepts only
`.py`, `.toml`, `.md`, `.yaml`, `.json` and `.jsonl`, so HTML, CSS and JS are excluded from
the published app — the shipped output surface is the text renderer in `backend/render.py`.
See brief §10.3.

## Working in this repo

Read **`CLAUDE.md`** before your first commit. Two rules decide whether four people on one
branch works: every task runs in its own **git worktree**, and `main` is the **only**
branch on `origin`.

The plan — submission gates, pitch, architecture, Hub publishing runbook, task breakdown,
milestones, cut list, judge Q&A — is `docs/consortium-brief.md`. Start at §0: it maps each
scored axis to the artefact that evidences it, and names the two gates that are pass/fail.
