# agents — the model side of a firm node

Owner: **Agent**.

One agent runs inside each firm's `ClientApp`. The agents hold **disjoint tool access**:
none can query another firm's library, and nothing here reaches outside the corpus for the
firm it is running as. `agents` imports `backend.schema` and nothing else from `backend`.

## Round 1 makes no model call

This is the thing to know before reading further, and it is the opposite of what the brief
planned (T4, T6).

Round 1 is **pure structured matching**, in `backend/firm_node.py:attest()`. Each requirement
predicate is tested against banded fields — equality, and `_min`/`_max` over an ordered band
list. A predicate key with no declared source *fails*. No prompt, no endpoint, no cache.

That is not a shortcut, it is the mechanism. The round boundary **is** the declared/prose
boundary: R4 asks for `experience: seismic-retrofit`, no record declares an `experience`
field, so round 1 cannot match it however hard it looks. Reading prose is round 2's job, and
round 2 is the only thing here that calls a model.

So the call budget is not "≤ 50 calls per full run" (brief R5). It is **one call per firm per
uncovered requirement, in round 2 only** — three calls for the default scenario's single gap,
issued concurrently because SuperGrid's per-task budget is five minutes and the shared
endpoint answered in ~240s under load.

## Modules

| Module | What it owns |
|---|---|
| `reexamine.py` | Round-2 gap-directed re-query. **Never cut this.** |
| `model.py` | Model client — `AgentSession` or raw HTTP, both behind an on-disk cache |
| `prompts/round2_reexamine.md` | The round-2 instructions, editable without touching Python |

Not built: `search.py` and `matcher.py` are docstring-only stubs, and
`prompts/round1_match.md` is a header with no prompt in it. Round 1 needed neither — see
above. Nothing imports them.

## How a model gets reached

Two paths, one interface — both speak Open Responses, so `reexamine` cannot tell them apart:

- **Published harness.** `backend/agent_app.py` passes `agent.responses.create` down through
  `make_client_app(reader)`. A `ClientApp` never sees an `AgentSession`, so handing it down
  is the only way. This is the only path that exists on SuperGrid.
- **Federated simulation.** No `AgentSession` at all, so `model.HttpReader` posts to
  `FLWR_MODEL_API_ENDPOINT` itself. Qwen takes no key — an empty `FLWR_MODEL_API_KEY` means
  *send no header*, not send an empty one.

`resolve_reader` picks in that order and always wraps the result in `CachedReader`. With no
model anywhere it returns `None`, and the harness degrades to round 1 and an open gap — the
honest outcome, not a crash.

### The cache is keyed on the exact request

`_fingerprint` is a SHA-256 of the canonicalised request, prompt text included. **Editing
`prompts/round2_reexamine.md` invalidates every cached response.** That is what you want
for correctness and it is a trap before a demo: the five entries in `.cache/model/` were
answered against the pre-`0472ae3` prompt and no longer key, so a run with no endpoint
reachable now logs `round-2 re-examination unavailable` and leaves R4 open.

Re-warm with `make traces MODEL=…` against a live endpoint after any prompt edit, and check
`.cache/model/` is non-empty before you unplug.

## Round 2 is the whole demo

Round 1 sees each requirement in isolation and every firm self-assesses compliant. Round 2
receives the **gap** — the uncovered requirement id, stated as a requirement — and never the
answer, never which record to look at. `data/scenarios.json` carries an evidence lexicon, but
that is the oracle `data/generate.py` uses to prove the cell is findable; putting it in front
of a node would be handing it the answer key.

The agent re-reads its own prose and returns `{handle: why}`. Then, in `firm_node`:

- the Section G join (`join: person_x_project`) is checked **in code**, against the record's
  same-firm `links` — a structural fact, not something the model is trusted to assert;
- `match_strength` is **0.8**, not 1.0, because this is a judgement about prose rather than
  an exact match on a declared field, and a downstream optimiser should be able to tell;
- a handle the model was not shown is discarded. A hallucinated handle is not evidence.

Failure is contained: a slow, absent, or rambling model costs the harness a closed gap, not a
crashed run — but it logs a WARNING, because a silent miss looks exactly like a correct empty
answer.

If round 2 stops finding the cell, read `prompts/round2_reexamine.md` **first**. The comment
at the top of it records why: an earlier version paired "judge the substance" with "do not
infer beyond the text", and Qwen3.5 resolved the contradiction by refusing every scenario's
evidence. The corpus was fine; the instructions were the bug. That is a live counterexample
to the brief's R2 mitigation ("edit the corpus, not the prompt") — check both, and check the
cheap one first.
