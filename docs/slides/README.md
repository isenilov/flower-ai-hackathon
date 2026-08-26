# slides — the deck

Owner: **Viz** (T17). Built with [Slidev](https://sli.dev). The live demo carries the
mechanism; this deck carries the **business context, the architecture, and the roadmap** —
the three things the running frontend cannot show.

```bash
make slides          # dev server on :3030, opens a browser, hot-reloads slides.md
make slides-build    # static bundle in docs/slides/dist/ — no node process at the table
```

Both go through `npx`, so nothing is added to `uv.lock` and nobody has to re-run `uv sync`.
The first `npx` needs the network; after that it is cached. **Do that before 16:50** — a deck
that first downloads its own toolchain at 17:29 is not a deck.

| File | Contents |
|---|---|
| `slides.md` | The deck. One `---` per slide, presenter notes in the trailing HTML comment. |
| `package.json` | Slidev pinned, dev/build/export scripts. Not installed by default. |
| `dist/` | Built output, gitignored. |

## When to use it

**Not at the table.** At 17:30 judges get the split screen (`make stage`) — the protocol's log
beside the live page. The deck is for the three cases where a running demo is the wrong
instrument:

- the **3-minute stage version** at 18:45, if we make the top 3, where a live run on shared
  wifi is a coin flip
- a judge who wants the **problem framing** or the **roadmap** rather than the mechanism
- the rehearsal, where the appendix slide is the axis-by-axis self-check

## Structure

Twelve slides plus an appendix. Each slide's presenter note names the judging axis it serves,
so the deck can be checked against `docs/event.md` rather than against taste.

1. Cover — the one-liner and the Hub handle
2. **The business problem** — joint ventures, competitors next month, spreadsheets
3. **Why nobody can just check** — the matrix cell, and the design constraint
4. The four-stage loop — stage 4 drawn dashed, because it is not built
5. **Architecture** — the trust boundary, and what crosses it
6. Round 2 — the multiplier, with the real log lines
7. What actually ran — every number copied off a real run
8. Safety and oversight
9. Flower and SuperGrid — one protocol, three `Grid`s
10. Four scenarios — the harness claim
11. **Roadmap** — the optimiser, the human gate, the evaluation, the win-rate prior
12. Close
13. *Appendix:* the six axes → the artefact that evidences each. Not presented.

## Rules for editing this deck

- **Every number on slide 7 came off a real run.** If the protocol changes, re-run it and
  re-copy them. A stale number here is worse than no number.
- **Nothing on a slide may claim something the code does not do.** The roadmap slide exists so
  that the optimiser, the human gate, and the baselines have somewhere honest to live. The
  appendix's *Not claimed* list is the checklist — keep it in sync with
  `docs/demo-script.md`'s closing section.
- **Validate Mermaid before pushing:** `node ~/.claude/tools/mermaid-lint/validate.mjs
  docs/slides/slides.md`. Slidev renders Mermaid natively, so a syntax error is a blank slide
  rather than a build failure — it will not fail loudly on its own.
- `docs/**` is already in `fab-exclude`, so nothing here ships inside the published app and no
  edit to this directory needs a republish.
