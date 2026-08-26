# data — corpora, solicitation, and ground truth

Owner: **Data** (T2). Critical path: committed by **13:00** or the scenario cuts to two
firms and six projects each, without debate.

| File | Contents |
|---|---|
| `vocabulary.json` | Closed sets for sector, value/recency bands, credentials, delivery, certification. Mirrors `backend/schema.py:VOCABULARY`. |
| `rfp.json` | The six typed requirements from the brief (§4) |
| `firm_a.json` | Large multidisciplinary, healthcare-heavy. ~12 projects, ~8 people. |
| `firm_b.json` | Structural specialist, seismic-heavy. **Holds the sole R4 match.** |
| `firm_c.json` | Mid-size regional, strong federal past performance. |
| `ground_truth.json` | True coverage per requirement, for scoring the three baseline conditions |
| `generate.py` | Scripted LLM generation pass. Fixed schema first, then generate. |

## Predicate keys

Requirement predicates are *requirement-side* and do not have to be vocabulary keys. A
`_min` / `_max` suffix means "this band or better" over the ordered band list in
`vocabulary.json` — `"value_band_min": "50-100M"` admits `50-100M`, `100-250M`, `250M+`.

## Engineering requirements — non-negotiable

1. **Exactly one** person across all three firms satisfies R4, and they are at Firm B.
2. That person's bio describes the hospital work in **non-obvious language** — "acute care
   wing structural upgrade", never "healthcare seismic retrofit" — so round 1 misses it and
   round 2 finds it. This is the single most important sentence in the dataset.
3. Each firm has enough surface coverage to plausibly self-assess as compliant.
4. At least one cost-2 record must be substitutable, or the denial beat fails.
5. 2–3 near-miss distractors per firm (right sector, wrong value band; right credential,
   wrong role) so the matcher has something to correctly reject.

Requirement 2 is a **tuning parameter, not fixed data**. If round 2 misses the match at
15:45, the wording here is what changes — not the prompt.

## Record shapes

A **project** record:

```json
{
  "handle": "FIRM_B::PROJ::014",
  "title": "...",                    // private — never leaves the node
  "client": "...",                   // private
  "client_type": "federal",
  "sector": "healthcare",
  "value_usd": 82000000,             // private; banded to value_band on egress
  "completed": "2021-06",            // private; banded to recency_band on egress
  "delivery": "design-build",
  "certification": "LEED-Gold",
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
  "projects": ["FIRM_B::PROJ::014"], // same-firm handles only — the Section G join
  "disclosure_cost": 0
}
```

Everything marked private is what the bander exists to keep inside the node. A record's
`disclosure_cost` of 3 means it is never offered — the firm's agent excludes it from the
candidate set entirely.
