# slides — the deck

Owner: **Viz** (T17). Built with [Slidev](https://sli.dev). Six slides. The live demo carries
the mechanism; this deck carries the **business context and the architecture** — the two things
the running page cannot show.

```bash
make slides          # dev server on :3030, opens a browser, hot-reloads slides.md
make slides-build    # static bundle in docs/slides/dist/ — no node process at the table
```

The first run installs Slidev into `docs/slides/node_modules` and needs the network.
**Do that before 16:50** — a deck that first downloads its own toolchain at 17:29 is not a
deck. Nothing is added to `uv.lock`, so nobody has to re-run `uv sync`.

| File | Contents |
|---|---|
| `slides.md` | The deck. One `---` per slide, presenter notes in the trailing HTML comment. |
| `style.css` | Auto-loaded by Slidev. Headline sizing, the `.tile` and coverage-grid classes, and the rule that centres Mermaid. |
| `slide-top.vue` | The `n / total` slide number, bottom right. Skipped on the cover. |
| `package.json` | Slidev pinned, dev/build/export scripts. |
| `dist/`, `node_modules/` | Gitignored. |

## What kind of deck this is

**Presenter support, not a handout.** Every slide is one headline, one visual, and at most a
two-line caption. The argument lives in the presenter notes, which is where it belongs when a
person is standing next to the screen. If a slide starts growing a third line of prose, the
prose goes in the notes.

**It assumes the audience has never seen a bid.** No "joint venture", no "solicitation", no
"past performance". SF330 appears on no slide at all — it is a ten-second gloss in slide 5's
presenter note. Say "hospital" and "earthquake strengthening", not "healthcare sector" and
"seismic retrofit".

## When to use it

**Not at the table.** At 17:30 judges get the split screen (`make stage`) — the protocol's log
beside the live page. The deck is for the two cases where a running demo is the wrong
instrument:

- the **3-minute stage version** at 18:45, if we make the top 3, where a live run on shared
  wifi is a coin flip
- a judge who wants the **problem framing** rather than the mechanism

What it no longer covers, because slides 7–14 were cut: the byte ledger, safety by
construction, the three `Grid`s, the four scenarios, the roadmap, and the axis-by-axis
self-check. Those are spoken beats now — `docs/demo-script.md` says where each one's evidence
lives.

## Structure

Six slides. Each presenter note names the judging axis it serves, so the deck can be checked
against `docs/event.md` rather than against taste.

| # | Slide | Visual |
|---|---|---|
| 1 | Cover | the problem and the solution, two lines each |
| 2 | **One contract. Three firms. Nobody can check.** | three firms, one question, three "cannot answer" |
| 3 | Architecture | the trust boundary, three identical stacks under it |
| 4 | **What the database fields can prove** | R1–R6 × three firms plus the joint column: no firm's column complete, R4 an amber `?` |
| 5 | **Firm B had the person all along** | the record's fields beside its bio, then the fourth row scored both ways |
| 6 | The loop | four stages, stage 4 dashed because it is not built |

Slides 1, 2 and 4 are the ones that decide whether the rest lands — they state the problem, and
slide 3's architecture is the only mechanism among them. Slide 6 is the last one, so the
presenter closes over it rather than on a closing slide.

## Rules for editing this deck

- **No byte counts on a slide.** The ledger left the deck with slide 8, and that is the safer
  place for it: `banded_bytes` drifts a few hundred bytes per run because every attestation
  carries the round-1 grader's sampled note, so it moves between runs (31.2 kB on the run that
  followed the corpus differentiation, ~33 kB before it). Quote "about 31 kB" out loud and let
  the live pane show the exact figure. If a number comes back
  onto a slide, it comes off `frontend/state/trace-healthcare-seismic.jsonl` and nowhere else.
- **Nothing on a slide may claim something the code does not do.** With the roadmap slide gone,
  the optimiser, the human gate, and the baselines have no honest home in the deck — so they
  are spoken, and slide 6's dashed stage 4 is the only place the deck admits an unbuilt piece.
  Keep that dash. `docs/demo-script.md`'s closing section is the *Not claimed* checklist.
- **Slide 4's three marks are three different claims, and R4 is the only `?`.** A green ✓ means
  the fields prove it and a red ✗ means the fields rule it out — both are settled either way,
  and `data/ground_truth.json`'s `coverage` (the oracle, reading every paragraph) agrees with
  `round_one_coverage` on all five. R4 is the amber `?` because a predicate that admits no
  record has not established that no record exists: `agents/search.py` is a structured predicate
  and `agents/matcher.py` may only grade what it admits, so Firm B's `sector: civic` record
  never reaches a model in round 1 — Firm B holds the person the whole time. **Put a red ✗ on
  R4 and slide 5 reads as a contradiction** — that is the bug this deck already had once. The
  legend and slide 5's strip are the fix; keep both.
- **Every mark on slide 4 comes off `data/ground_truth.json`, and it is read per firm, not
  jointly.** Round 1 gives A 7/3 on R1 and 0 on R5; B 2/3 on R1 and 0 on R3; C 0 on R3 and 0 on
  R5. The row ids are `data/rfp.json`'s own R1–R6 in that order, so R4 here is R4 in the log.
  The joint column is derived — one firm's tick makes the team's tick.
- **No firm's column may be complete, and the joint column must be.** That is the slide's whole
  argument and `data/generate.py` enforces it, gated on `"alone": "short"` in
  `data/scenarios.json`. Edit a corpus so a firm clears everything alone, or so a requirement
  stops closing jointly, and `make data` fails rather than letting the slide quietly become
  false. The counts in the row labels ("**Three** hospital projects…") are the `min_count`s the
  crosses depend on — drop them and Firm B's ✗ on R1 looks arbitrary.
- Do not revive the brief's "each firm self-assesses compliant and is confidently wrong" — the
  corpora now say the opposite outright, and `docs/demo-script.md` carries the line to use.
- **Validate Mermaid before pushing:** `node ~/.claude/tools/mermaid-lint/validate.mjs
  docs/slides/slides.md`. Slidev renders Mermaid client-side, so a syntax error is a blank
  slide rather than a build failure.
- **Check nothing spills off the canvas.** The slide is 980 × 552, and a Mermaid diagram that
  is 40px too wide silently clips at both edges. Run `make slides`, walk every slide, and look
  at the left and right margins. Mermaid `{scale: …}` is the dial: 0.7 for a four-node `LR`
  flowchart is about the ceiling. Slide 4's table has ~9px of vertical headroom and its
  right-hand chip is flush with the margin, so a seventh row, a wider mark column, or a bigger
  `.rq` font has to be paid for out of the row gap and cell padding.
- **Both colour schemes.** Slidev follows the browser, and a laptop in dark mode at 18:45 is
  not a hypothetical. Anything with a hard-coded `background` needs an `html.dark` rule beside
  it.
- `docs/**` is already in `fab-exclude`, so nothing here ships inside the published app and no
  edit to this directory needs a republish.
