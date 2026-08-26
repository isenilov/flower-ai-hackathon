# backend — protocol, surfaces, and the firm node

Owner: **Flower** (transport, apps) + **Fusion** (optimiser, approval, baselines).

Everything that is *not* an LLM call lives here. The dependency runs one way: `agents`
imports `backend.schema` and nothing else from `backend`; `backend.firm_node` imports
`agents` lazily, inside the functions that need a model, so round 1 stays dependency-free.

## The shape that actually emerged

The brief (§5.1, and the appendix layout) planned one module per stage. The build
collapsed that into three load-bearing modules plus two thin surfaces, because two facts
turned up that the plan did not anticipate:

- **Hub rejects a mixed FAB.** A bundle may declare `agentapp` *or* `serverapp` +
  `clientapp`, never both. So the published app is agentapp-only, and `flwr run .` starts
  the harness rather than the federation — which is why the round loop had to be lifted out
  of `server_app.py` into `protocol.py`, where both surfaces can call it.
- **The AgentApp process gets no `Grid`.** `@app.main()` receives `(agent, context)`, and
  the runtime strips `flwr` from the app's dependencies, so `run_simulation` cannot be
  imported there. `local_grid.py` is the shim that lets the same loop run in-process.

```
                      protocol.run()          <- the round loop, one copy
                     /              \
        agent_app.py                 server_app.py
        (AgentApp, published)        (ServerApp, `make rounds`)
              |                            |
        LocalGrid                    a real Grid (Ray, one SuperNode per firm)
              \                            /
                     firm_node.make_client_app()
                      attest -> reexamine_gaps
```

## Modules

| Module | What it owns |
|---|---|
| `schema.py` | `Requirement`, `Attestation`, the closed `VOCABULARY`, `SECTION_F_CAP`. **Frozen.** |
| `protocol.py` | The round loop, gap detection, `Outcome`, and `render()` — the text surface that ships |
| `firm_node.py` | The whole node side: dual-runtime library load, banding, predicate matching, round-1 `attest`, round-2 `reexamine_gaps`, wire `encode`/`decode` |
| `local_grid.py` | In-process `Grid` over `ClientApp` instances, one `Context` per firm, nodes run concurrently |
| `agent_app.py` | The published surface — solicitation in, coverage report out. **This is what Hub runs.** |
| `server_app.py` | The federated surface — same protocol over a real grid |
| `client_app.py` | Three lines: `app = make_client_app()`. The node logic is in `firm_node.py`. |
| `rounds.py` | CLI driver for the federated surface (`make rounds`), over `run_simulation` |
| `scenarios.py` | The scenario catalogue — the only thing that reads `data/scenarios.json` on the run path |
| `trace.py` | Protocol event log: JSONL for the frontend, terminal lines, and Flower's run-event stream |

## Not built

These are docstring-only stubs. They are the brief's plan for stages three and four, and
nothing imports them — so a reader who greps for the optimiser finds a docstring, not a
bug.

| Stub | Was going to be | Where the work landed instead |
|---|---|---|
| `bander.py` | Egress validator + byte counter | Banding is `firm_node.band_project` / `band_person`; bytes are counted in `trace.py`. **There is no rejection path** — the vocabulary constrains the values at construction, but nothing validates on egress. |
| `transport.py` | `Attestation` ⇄ `RecordDict` | `firm_node.encode` / `decode` |
| `coverage.py` | Coverage matrix, gap analysis | `protocol.run`'s `covered` dict and `Outcome.open_gaps` |
| `optimiser.py` | Greedy weighted set cover under the Section F cap | **Nothing. Stage four does not exist.** |
| `approval.py` | BD approval gate, denial-and-substitute | **Nothing.** |
| `assemble.py` | SF330 Sections E / F / G | **Nothing.** `protocol.render` prints the coverage matrix, not an SF330. |
| `baselines.py` | Isolated / consortium / centralised-pool | **Nothing.** `make baselines` runs and prints nothing at all. |

`backend/render.py` from the brief's appendix was never created — the text renderer is
`protocol.render()`.

## Invariants that actually hold

- **No record content crosses the wire.** Zero by construction, not by policy: no field on
  `Attestation` can carry a title, client, fee, name, or bio. `run_ended.record_bytes` is
  therefore 0 in every trace.
- **`links` reference same-firm handles only** — `firm_node` filters on the firm prefix, and
  `tests/test_invariants.py` asserts it across the corpora.
- **Cost-3 (blocked) records never enter the candidate set**, in round 1 (`attest`) and
  round 2 (`reexamine._candidates`) alike. A refusal a second look could route around
  would not be a refusal.
- **The gap travels back to the firms, never the evidence.** Round 2's broadcast carries
  the uncovered requirement ids and nothing else — `trace.py` counts those bytes separately
  (`broadcast.gap_bytes`) because that is the whole claim.
- **A model's reasoning stays on the node.** `reexamine_gaps` logs the model's sentence at
  DEBUG and puts requirement-side vocabulary on the wire instead.

The invariant the old version of this file claimed — "nothing that leaves a firm node
bypasses `bander.py`" — is not one of them. There is no bander.
