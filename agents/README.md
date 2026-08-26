# agents — the per-firm matcher

Owner: **Agent**.

One matcher agent runs inside each firm's `ClientApp`. The agents hold **disjoint tool
access**: none can query another firm's library, and nothing here reaches outside
`data/firm_<x>.json` for the firm it is running as.

| Module | Task | What it owns |
|---|---|---|
| `search.py` | T4 | Structured predicate prefilter over banded fields |
| `matcher.py` | T6 | Round-1 matching and attestation emission |
| `reexamine.py` | T8 | Round-2 gap-directed re-query — **never cut this** |
| `model.py` | — | Model client, plus the on-disk response cache that survives venue wifi |
| `prompts/` | T6, T8 | Prompt text, versioned separately from the code that sends it |

## Call budget

Naive matching is 60 records × 6 requirements. Prefilter on banded fields in `search.py`
and invoke the model only on the shortlist, and only for free-text bios — target ≤ 50
calls per full run.

## Round 2 is the whole demo

Round 1 sees each requirement in isolation. Round 2 receives the *gap*, not the answer:
"R4 uncovered — need one individual with both healthcare and seismic retrofit evidence."
The agent re-queries its own library with a question it did not know to ask, and emits a
`links` entry joining a person to a project.

If round 2 misses the match by 15:45, edit the corpus wording in `data/`, not the prompt.
