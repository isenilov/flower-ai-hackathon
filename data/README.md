# data — corpora, solicitations, and ground truth

Owner: **Data** (T2). Critical path: committed by **13:00** or the scenario cuts to two
firms and six projects each, without debate.

Four scenarios ship. The default is the one the demo runs and the one the brief describes;
the other three exist because the close is *"swap the requirement set, the vocabulary and
the cost function and the same harness runs somewhere else"* — and a claim like that is
worth what the second, third and fourth dataset behind it are worth.

| File | Contents |
|---|---|
| `vocabulary.json` | Closed sets for sector, value/recency bands, credentials, delivery, certification. Mirrors `backend/schema.py:VOCABULARY`. **Shared by every scenario.** |
| `scenarios.json` | The manifest: one entry per scenario — path, firm profiles, the engineered gap, and the evidence lexicon |
| `rfp.json` | Default scenario: the six typed requirements from the brief (§4) |
| `firm_a.json` | Large multidisciplinary, healthcare-heavy. 13 projects, 8 people. |
| `firm_b.json` | Structural specialist, seismic-heavy. **Holds the sole R4 match.** |
| `firm_c.json` | Mid-size regional, strong federal past performance. |
| `ground_truth.json` | Derived. True coverage per requirement, for scoring the three baseline conditions |
| `generate.py` | The build pass: derives ground truth, and refuses to write it if the gap is gone |
| `scenarios/<slug>/` | An alternate scenario — same five filenames, its own solicitation and firms |

## The four scenarios

`make data` builds and checks all of them. `uv run python data/generate.py <slug>` does one.

| Slug | Solicitation | The Section G cell | Held by |
|---|---|---|---|
| `healthcare-seismic` *(default, at `data/`)* | Federal healthcare facility, seismic zone, design-build | healthcare **and** seismic retrofit | Firm B |
| `transit-tunnel` | Underground station box and running tunnel extension, CM-at-risk | transport **and** soft-ground tunnelling | Firm C |
| `defence-secure-lab` | Secure research laboratory on an active installation, design-build | defence **and** biocontainment | Firm A |
| `campus-decarbonisation` | Campus decarbonisation and deep energy retrofit, IPD | education **and** district energy | Firm B |

They are deliberately not re-skins. The delivery method, the client type, the certification
threshold, the weighted requirements and the firm holding the gap all move, and the three
non-default scenarios run heavier on cost-3 records so the *refusal is honoured* beat has
more to bite on. What does **not** move is `vocabulary.json` — it is frozen against
`backend/schema.py` and one test asserts they are identical, so a scenario that needed a new
sector would be a schema change, not a data change. Swapping the vocabulary is a roadmap
line (brief §14), not a build-day one.

The default scenario stays at `data/` rather than moving under `scenarios/` alongside the
others. It is asymmetric and it is deliberate: those paths are named in the brief, in
`tests/test_invariants.py`, and in `backend/scenarios.py`, which resolves the default by
falling back to `data/` rather than to a `scenarios/` subdirectory.

## Deriving ground truth — `generate.py`

The corpora are hand-authored JSON and stay that way; the R4 bio wording is a tuning
parameter and needs to be editable at 15:45 without running a generator. What `generate.py`
does is the part that must never drift by hand: it evaluates every typed predicate in a
scenario's `rfp.json` against that scenario's three corpora and writes `ground_truth.json`
from the result.

It reads the same corpora three ways, and the whole scenario lives in the gaps between them:

| Reading | Sees | Is |
|---|---|---|
| `declared` | structured fields only | what a round-1 agent's prefilter can match |
| `firm` | + free text, for **disciplines** but never to re-file a sector | what a firm knows about itself, alone |
| `oracle` | + free text, for everything | what a centralised pool with a perfect reader would find |

`coverage` in `ground_truth.json` is the oracle reading. `round_one_coverage` is the
declared one. The only requirement where they differ is the gap. `self_assessment` is the
firm reading with one word removed from the Section G predicate — `join` — which is the
entire difference between the isolated condition and the truth, and the reason all three
firms cite two different people for one cell and call it covered.

**`round_one_coverage` is a contract, not just a record.** `agents/matcher.py` grades round-1
matches with a model, and it is pinned to this reading: grading may annotate a match but may
neither add one nor drop one, because a model that could nominate would find the Section G
cell a round early and one that could veto would put the harness below its own oracle on a
sampled completion. Run `make rounds` with and without `MODEL=` and the matrix is identical —
that is this number holding.

The evidence lexicon lives in `scenarios.json`, not in the Python. It is a list of words per
tag, matched on word boundaries against project narratives and person bios. Boundaries are
not fussiness: substring matching makes "ward" fire on "awarded" and the uniqueness check on
the Section G cell becomes quietly meaningless.

**`generate.py` fails rather than writes.** Every rule below is checked before anything is
written, each with the reason it exists in the failure text. `tests/test_scenarios.py` runs
the same pass over every scenario, so `make check` catches a corpus edit that closed the gap
before the stage does.

## Predicate keys

Requirement predicates are *requirement-side* and do not have to be vocabulary keys. A
`_min` / `_max` suffix means "this band or better" over the ordered band list in
`vocabulary.json` — `"value_band_min": "50-100M"` admits `50-100M`, `100-250M`, `250M+`.

Two things that are not obvious from the file:

- **`certification` is the exception.** Its list in `vocabulary.json` is a closed set, not a
  rank — `"none"` is last there but ranks below every award. `certification_min` uses the
  order pinned in `generate.py`, not the list order.
- **`as_of` in each `rfp.json` fixes the reference date** for `recency_band`. Without it the
  bands drift with the wall clock and a project silently ages out of R1 between rehearsal
  and demo.

For a `PERSON`, `role` and `credentials` are record fields, and `sector` / `experience`
resolve against the evidence tags — the sectors of the projects they are booked to, plus
whatever their bio says. That is what makes the Section G cell hideable: the bio is the only
place it can live.

## Engineering requirements — non-negotiable

1. **Exactly one** person across all three firms satisfies the Section G requirement, and
   they are at the firm named in `scenarios.json`.
2. That person's bio describes the hidden half in **non-obvious language** — "acute care
   wing structural upgrade", never "healthcare seismic retrofit" — so round 1 misses it and
   round 2 finds it. This is the single most important sentence in the dataset.
3. Their linked projects must not *declare* the hidden half either. If one does, a
   structured round-1 search reaches them and there is no gap left to broadcast.
4. No firm can join the cell from its own library, even reading its own bios — otherwise
   "no single firm could have seen this" is not true.
5. Each firm has enough surface coverage to self-assess as compliant on every MANDATORY
   requirement. Note what this does and does not license: it holds for the `self_assessment`
   reading, which drops `join` from the Section G predicate. On the actual run path no firm
   reaches R4 at all — each covers five of six. Say that, not "confidently wrong"
   (`docs/demo-script.md`).
6. At least one cost-2 record must be substitutable, or the denial beat fails.
7. At least one cost-3 record must be one that *would* have matched, or "the refusal is
   honoured" is a claim about a candidate set that never excluded anything.
8. 2–3 near-miss distractors per firm (right sector, wrong value band; right credential,
   wrong role) so the matcher has something to correctly reject.
9. Keep each `data/**/*.json` under 1 MB — the Hub upload rejects a larger file (§10.3).

Requirement 2 is a **tuning parameter, not fixed data**. If round 2 misses the match at
15:45, the wording here is what changes — not the prompt. Retune the bio, run `make data`,
and the pass tells you within a second whether round 1 can still miss it and round 2 still
find it.

## Record shapes

A **project** record:

```json
{
  "handle": "FIRM_B::PROJ::005",
  "title": "...",                    // private — never leaves the node
  "client": "...",                   // private
  "client_type": "municipal",
  "sector": "civic",
  "value_usd": 58000000,             // private; banded to value_band on egress
  "completed": "2022-11",            // private; banded to recency_band on egress
  "delivery": "design-bid-build",
  "certification": "none",
  "narrative": "...",                // free text, searched by the matcher
  "disclosure_cost": 1               // 0 free | 1 NDA-limited | 2 sensitive | 3 blocked
}
```

A **person** record:

```json
{
  "handle": "FIRM_B::PERSON::007",
  "name": "...",                     // private — never leaves the node
  "role": "structural-lead",
  "credentials": ["SE", "PE"],
  "bio": "...",                      // free text; this is where the R4 match hides
  "projects": ["FIRM_B::PROJ::005"], // same-firm handles only — the Section G join
  "disclosure_cost": 1
}
```

Each firm file also carries a `profile` string — one line on who the firm is and why it is
blind to the cell. It is for the UI and the narrator, and nothing reads it as data.

Everything marked private stays inside the node — structurally, because no field on an
`Attestation` can carry it, rather than because something strips it on the way out. (Brief
§5.1's `bander.py` was never built; see `backend/README.md`.) A record's `disclosure_cost` of
3 means it is never offered — `agents/search.py` excludes it from the candidate set in both
rounds.

## Adding a scenario

1. `data/scenarios/<slug>/` with `rfp.json`, `firm_a.json`, `firm_b.json`, `firm_c.json`.
   Six requirements, ids `R1`–`R6`, `R1`–`R4` MANDATORY, `R4` the Section G cell — the
   coverage matrix and the optimiser are written against those ids.
2. An entry in `data/scenarios.json` with the path, the gap (requirement, firm, the two
   tags), and a lexicon for each tag.
3. `uv run python data/generate.py <slug>` until it stops printing failures. It will tell
   you which of the rules above the corpus is breaking and why that rule is there.
4. `make check`. The new scenario is picked up by `tests/test_scenarios.py` automatically.
