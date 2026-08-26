# frontend — coverage matrix, disclosure ledger, SF330

Owner: **Viz** (T13, T14, T15).

Static HTML and vanilla JS. No framework, no build step, no server — the backend writes
run state as JSON into `frontend/state/` and the page reads it. Open `index.html`
directly, or `python -m http.server` from this directory if the browser objects to
`file://` fetches.

| File | Task | Shows |
|---|---|---|
| `index.html` | T13, T14 | Coverage matrix per round, disclosure ledger, assembled SF330 |
| `app.js` | T13 | Loads `state/*.json`, renders the three panels |
| `styles.css` | T13 | Styling. Red cell / green cell is the whole visual argument. |
| `state/` | — | Written by the backend, gitignored. Never hand-edited. |

## The three beats this has to land

1. **Round 1** — matrix fills in, **R4 red**, while each firm's own self-assessment reads
   compliant.
2. **Round 2** — gap broadcast, Firm B surfaces the match, the cell turns green.
3. **Round 3** — ledger: 9 of 40 records released, one denial substituted, 0 confidential
   clients named, raw library bytes transmitted before approval **0**.

`frontend/` is **cut candidate #1 and #2** on the brief's cut list. If it is not landing
by 16:00, fall back to a printed table and protect the evaluation instead.
