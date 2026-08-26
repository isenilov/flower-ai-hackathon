# backend — coordinator, firm node, and fusion

Owner: **Flower** (transport, apps) + **Fusion** (optimiser, approval, baselines).

Everything that is *not* an LLM call lives here. The agents package (`agents/`) is
called from `client_app.py`; it never imports from `backend` except `schema`.

| Module | Task | What it owns |
|---|---|---|
| `schema.py` | T1 | `Requirement`, `Attestation`, the closed vocabulary. **Frozen 11:20.** |
| `bander.py` | T9 | Egress validator — rejects anything outside the vocabulary — and the outbound byte counter |
| `transport.py` | T5 | `Attestation` ⇄ `RecordDict`, both directions |
| `server_app.py` | T3, T7 | Coordinator: RFP decomposition, round loop, gap broadcast |
| `client_app.py` | T3, T6 | Firm node: dispatch to the matcher agent, run the approval gate |
| `coverage.py` | T7 | Coverage matrix and gap analysis |
| `optimiser.py` | T10 | Greedy weighted set cover under the Section F cap of 10 |
| `approval.py` | T11 | BD approval gate and the denial-and-substitute re-run |
| `assemble.py` | T14 | SF330 Sections E / F / G |
| `baselines.py` | T12 | Isolated / consortium / centralised-pool harness |

## Invariants

- Nothing that leaves a firm node bypasses `bander.py`. Every outbound `Attestation`
  is validated there, and every byte is counted there.
- The bander **rejects** an unknown key; it never silently drops or sanitises one.
- `links` may only reference same-firm handles — a firm cannot assert facts about
  another firm.
- Cost-3 (blocked) handles are excluded from the optimiser's candidate set entirely.
