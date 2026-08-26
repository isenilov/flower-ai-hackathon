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
"past performance". SF330 appears on no slide at all — it is a ten-second gloss in slide 4's
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
| 3 | **What the database fields can prove** | the R1–R6 × 3 table: five rows ✓, R4 an amber `?` |
| 4 | **Firm B had the person all along** | the record's fields beside its bio, then the fourth row scored both ways |
| 5 | The loop | four stages, stage 4 dashed because it is not built |
| 6 | Architecture | the trust boundary, three identical stacks under it |

Slides 1–3 are the ones that decide whether the rest lands. They state the problem before any
mechanism appears. Slide 6 is the last one, so the presenter closes over it rather than on a
closing slide.

## Rules for editing this deck

- **No byte counts on a slide.** The ledger left the deck with slide 8, and that is the safer
  place for it: `banded_bytes` drifts a few hundred bytes per run because every attestation
  carries the round-1 grader's sampled note (33191 B on one run, 33807 B on the next). Quote
  "about 33 kB" out loud and let the live pane show the exact figure. If a number comes back
  onto a slide, it comes off `frontend/state/trace-healthcare-seismic.jsonl` and nowhere else.
- **Nothing on a slide may claim something the code does not do.** With the roadmap slide gone,
  the optimiser, the human gate, and the baselines have no honest home in the deck — so they
  are spoken, and slide 5's dashed stage 4 is the only place the deck admits an unbuilt piece.
  Keep that dash. `docs/demo-script.md`'s closing section is the *Not claimed* checklist.
- **Slide 3 is a field search, not an inventory, and the marks carry that.** Five rows are ✓ at
  every firm; R4 is an amber `?`, never a red ✗, because a predicate that admits no record has
  not established that no record exists. The row ids are `data/rfp.json`'s own R1–R6, in that
  order, so R4 on the slide is R4 in the log and on the live page. Firm B holds the person the
  whole time: `agents/search.py` is a structured predicate and `agents/matcher.py` may only
  grade what it admits, so a record filed `sector: civic` never reaches a model in round 1. Put
  a red ✗ back on that row and slide 4 reads as a contradiction — that is the bug this deck
  already had once. The legend and slide 4's two-way strip are the fix; keep both.
- Do not revive the brief's "each firm self-assesses compliant and is confidently wrong" —
  that is `ground_truth.json`'s `self_assessment` baseline, and it never executes.
- **Validate Mermaid before pushing:** `node ~/.claude/tools/mermaid-lint/validate.mjs
  docs/slides/slides.md`. Slidev renders Mermaid client-side, so a syntax error is a blank
  slide rather than a build failure.
- **Check nothing spills off the canvas.** The slide is 980 × 552, and a Mermaid diagram that
  is 40px too wide silently clips at both edges. Run `make slides`, walk every slide, and look
  at the left and right margins. Mermaid `{scale: …}` is the dial: 0.7 for a four-node `LR`
  flowchart is about the ceiling. Slide 3's table has ~9px of vertical headroom, so a seventh
  row or a bigger `.rq` font needs the row-gap and cell padding trimmed to pay for it.
- **Both colour schemes.** Slidev follows the browser, and a laptop in dark mode at 18:45 is
  not a hypothetical. Anything with a hard-coded `background` needs an `html.dark` rule beside
  it.
- `docs/**` is already in `fab-exclude`, so nothing here ships inside the published app and no
  edit to this directory needs a republish.
