# agents — the model side of a firm node

Owner: **Agent**.

One agent runs inside each firm's `ClientApp`. The agents hold **disjoint tool access**:
none can query another firm's library, and nothing here reaches outside the corpus for the
firm it is running as. `agents` imports `backend.schema` and nothing else from `backend`.

| Module | What it owns |
|---|---|
| `search.py` | Structured predicate prefilter. Decides *what to ask about*; calls no model. |
| `matcher.py` | Round 1 — grades the shortlist the prefilter admitted |
| `reexamine.py` | Round 2 — gap-directed re-query. **Never cut this.** |
| `model.py` | Model client — `AgentSession` or raw HTTP, both behind an on-disk cache |
| `prompts/` | Both prompts, editable without touching Python |

## Both rounds start at the prefilter

`search.py` is the shared front half, and it is deliberately the *only* place that decides
what a node is allowed to look at: the right half of the library for the requirement's
section, and blocked (cost-3) records excluded. Round 1 grades what it admits; round 2
re-reads what it turned down. Keeping that in one module is what stops the two rounds
drifting apart on eligibility.

`shortlist()` matches declared fields only — equality, and `_min`/`_max` over an ordered
band list. **A predicate key with no banded source fails.** That is the round boundary and
it is the whole mechanism of the demo: R4 wants `experience: seismic-retrofit`, no record
declares an `experience` field, so round 1 cannot reach it however hard it looks. The
Section G cell survives round 1 because the filing says civic and only the bio says
hospital.

## Round 1 grades; it never re-decides

Round 1 does call a model, and it is important to be exact about what the call can and
cannot do. It asks one question: **does this record's own prose bear its filing out?**
Answers are `corroborated` (`match_strength` 1.0) or `thin` (0.7), plus a note.

It cannot add a record and it cannot drop one:

- **No nomination.** The model sees only what the predicate already matched, and a handle
  it was not shown is discarded in `_read`. A round-1 call that could nominate would find
  the Section G cell a round early and there would be no round-2 beat left.
- **No veto.** `thin` is a grade, not a rejection. Both strengths clear the optimiser's
  default tau of 0.6, so a `thin` record stays in the candidate set. Round 1's coverage is
  pinned to `round_one_coverage` in `data/ground_truth.json`, and a model that could drop a
  declared match would put the harness below its own oracle on a sampled completion.

Both are enforced in `matcher.py`, not merely asked for in the prompt. **The coverage matrix
is byte-identical with or without a model in round 1** — verify it by running `make rounds`
twice, with and without `MODEL=`, and diffing the matrix. What the model adds is annotation:
strengths and notes that tell a downstream optimiser which filings are thin.

Every failure path lands on `matcher.DECLARED` — the declared match at full strength,
nothing added. A model that is slow, absent, or talking nonsense costs the harness its
annotations and nothing else. It logs a WARNING when that happens, because a silent degrade
to declared-only looks exactly like a model that agreed with every filing, and those are not
the same claim.

## The call budget

Not "≤ 50 calls per full run" (brief R5), and not one per record either:

| Round | Calls | Why |
|---|---|---|
| 1 | **one per firm** — the whole matrix in a single request | Round trips are the cost that matters, not tokens. Per requirement it was eighteen calls a run and ~2 min a firm cold; this is three calls and one wait — and one cache entry per firm per scenario, so a rehearsal replays whole instead of partially. |
| 2 | **one per firm per uncovered requirement** | Three calls for the default scenario's single gap, issued concurrently — SuperGrid's per-task budget is five minutes and the shared endpoint answered in ~240s under load. |

Round 1 has its own `GRADING_BUDGET` of 120s, well below `model.DEFAULT_TIMEOUT` of 280s:
round 2 is the beat and the call allowed to take its time, a grade is not worth a missed
round. Whatever misses the budget is left running into the cache, so the next run of that
scenario gets it for free.

## How a model gets reached

Two paths, one interface — both speak Open Responses, so neither round can tell them apart:

- **Published harness.** `backend/agent_app.py` passes `agent.responses.create` down through
  `make_client_app(reader)`. A `ClientApp` never sees an `AgentSession`, so handing it down
  is the only way. This is the only path that exists on SuperGrid.
- **Federated simulation.** No `AgentSession` at all, so `model.HttpReader` posts to
  `FLWR_MODEL_API_ENDPOINT` itself. Qwen takes no key — an empty `FLWR_MODEL_API_KEY` means
  *send no header*, not send an empty one.

`resolve_reader` picks in that order and always wraps the result in `CachedReader`. With no
model anywhere it returns `None`, and the harness degrades to declared matching and an open
gap — the honest outcome, not a crash.

### The cache is keyed on the exact request

`_fingerprint` is a SHA-256 of the canonicalised request, prompt text included. **Editing
either prompt invalidates every cached response for that round.** That is right for
correctness and it is a trap before a demo: an unreachable endpoint then means round 2 logs
`round-2 re-examination unavailable` and R4 stays red.

Re-warm with `make traces MODEL=…` against a live endpoint after any prompt edit, and check
`make doctor`'s `cache` line is non-zero before you unplug. `CachedReader.cached()` is asked
*before* the call precisely so a replay can be reported as a replay — a sub-millisecond
answer with no explanation reads as a model that was never consulted.

## Round 2 is the whole demo

Round 1 sees each requirement in isolation and every firm self-assesses compliant. Round 2
receives the **gap** — the uncovered requirement id and its predicate, stated as a
requirement — and never the answer, never which record to look at. `data/scenarios.json`
carries an evidence lexicon, but that is the oracle `data/generate.py` uses to prove the
cell is findable; putting it in front of a node would be handing it the answer key.

The agent re-reads its own prose and returns `{handle: why}`. Then, in `firm_node`:

- the Section G join (`join: person_x_project`) is checked **in code**, against the record's
  same-firm `links` — a structural fact, not something the model is trusted to assert;
- `match_strength` is **0.8** — above tau, below a declared match — because this is a
  judgement about prose rather than an exact match on a declared field;
- a handle the model was not shown is discarded. A hallucinated handle is not evidence.

The model's sentence stays on the node in both rounds. It is prose derived from a bio, and
the claim this harness makes is that no record content crosses before authorisation — so the
wire gets a float and requirement-side field names, and the clause goes to the local log.
Ray forwards a SuperNode's stdout to the driver with the actor's pid attached, which is why
`reexamine` logs there rather than at the coordinator: it is visible proof that the prose was
read on the firm's own node and only a verdict left it.

## If round 2 stops finding the cell

Read `prompts/round2_reexamine.md` **first**, before touching `data/`. The comment at the top
of it records why: an earlier version paired "judge the substance" with "do not infer beyond
the text", and Qwen3.5 resolved the contradiction by refusing every scenario's evidence — its
own reasoning read *"no record explicitly describes both … without inference"*. Every
scenario's evidence was present in the bios the whole time; the instructions were the bug.

That is a live counterexample to the brief's R2 mitigation ("if it misses by 15:45, edit the
corpus, not the prompt"). Check both — and check the prompt first, because it is the cheaper
one and it is the one that was wrong.
