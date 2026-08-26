# slides — the deck

Owner: **Viz** (T17). Built with [Slidev](https://sli.dev). The live demo carries the
mechanism; this deck carries the **business context, the architecture, and the roadmap** —
the three things the running page cannot show.

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
| `style.css` | Auto-loaded by Slidev. Headline sizing, the `.tile` / `.num` / coverage-grid classes, and the rule that centres Mermaid. |
| `slide-top.vue` | The `n / total` slide number, bottom right. Skipped on the cover. |
| `package.json` | Slidev pinned, dev/build/export scripts. |
| `dist/`, `node_modules/` | Gitignored. |

## What kind of deck this is

**Presenter support, not a handout.** Every slide is one headline, one visual, and at most a
two-line caption. The argument lives in the presenter notes, which is where it belongs when a
person is standing next to the screen. If a slide starts growing a third line of prose, the
prose goes in the notes.

**It assumes the audience has never seen a bid.** No "joint venture", no "solicitation", no
"past performance". SF330 is named once, on slide 4, with a gloss. Say "hospital" and
"earthquake strengthening", not "healthcare sector" and "seismic retrofit".

## When to use it

**Not at the table.** At 17:30 judges get the split screen (`make stage`) — the protocol's log
beside the live page. The deck is for the three cases where a running demo is the wrong
instrument:

- the **3-minute stage version** at 18:45, if we make the top 3, where a live run on shared
  wifi is a coin flip
- a judge who wants the **problem framing** or the **roadmap** rather than the mechanism
- the rehearsal, where the appendix slide is the axis-by-axis self-check

## Structure

Thirteen slides plus an appendix. Each presenter note names the judging axis it serves, so the
deck can be checked against `docs/event.md` rather than against taste.

| # | Slide | Visual |
|---|---|---|
| 1 | Cover | the problem and the solution, two lines each |
| 2 | **One contract. Three firms. Nobody can check.** | three firms, one question, three "cannot answer" |
| 3 | **Five of six, at every firm** | the 6 × 3 coverage grid, one row red |
| 4 | The fourth row is in a paragraph, not a field | the database fields beside the bio sentence |
| 5 | The loop | four stages, stage 4 dashed because it is not built |
| 6 | Architecture | the trust boundary, three identical stacks under it |
| 7 | The coordinator sends the gap, not the answer | 2 bytes out, two "nothing here", one hit |
| 8 | What crossed the wire | four numbers, all off a real run |
| 9 | Safety by construction | four rules |
| 10 | One protocol, three wires | `LocalGrid` · `InMemoryGrid` · `GrpcGrid` |
| 11 | The form is the example. The harness is the product. | four scenarios, the gap at a different firm |
| 12 | **Roadmap** | optimiser · human gate · evaluation · win-rate prior |
| 13 | Close | the through-line |
| 14 | *Appendix:* the six axes | not presented |

Slides 1–3 are the ones that decide whether the rest lands. They state the problem before any
mechanism appears.

## Rules for editing this deck

- **Every number on slide 8 came off a real run**, out of
  `frontend/state/trace-healthcare-seismic.jsonl`.
  Round 1 attests 19 · 13 · 18; the round-2 broadcast carries `gap_bytes` 2; `banded_bytes`
  33191, which the page renders as 32.4 kB; `record_bytes` 0; converged after 2 rounds. If the
  protocol changes, re-run it and re-copy them. A stale number here is worse than no number.
- **Nothing on a slide may claim something the code does not do.** The roadmap slide exists so
  that the optimiser, the human gate, and the baselines have somewhere honest to live. The
  appendix's *Not claimed* list is the checklist — keep it in sync with
  `docs/demo-script.md`'s closing section.
- **Slide 3 shows what the run shows.** Every firm clears five rows alone and all three miss
  the fourth. Do not revive the brief's "each firm self-assesses compliant and is confidently
  wrong" — that is `ground_truth.json`'s `self_assessment` baseline, and it never executes.
- **Validate Mermaid before pushing:** `node ~/.claude/tools/mermaid-lint/validate.mjs
  docs/slides/slides.md`. Slidev renders Mermaid client-side, so a syntax error is a blank
  slide rather than a build failure.
- **Check nothing spills off the canvas.** The slide is 980 × 552, and a Mermaid diagram that
  is 40px too wide silently clips at both edges. Run `make slides`, walk every slide, and look
  at the left and right margins. Mermaid `{scale: …}` is the dial: 0.7 for a four-node `LR`
  flowchart is about the ceiling.
- **Both colour schemes.** Slidev follows the browser, and a laptop in dark mode at 18:45 is
  not a hypothetical. Anything with a hard-coded `background` needs an `html.dark` rule beside
  it.
- `docs/**` is already in `fab-exclude`, so nothing here ships inside the published app and no
  edit to this directory needs a republish.
