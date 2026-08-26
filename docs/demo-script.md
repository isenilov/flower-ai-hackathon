# Demo script

Judges come **to the table** at 17:30 and give us **3–5 minutes**. That is a conversation,
not a stage pitch, and it changes three things: we lead with the submission gate, we build
in silence for questions, and we never depend on the venue wifi.

Owner: **Viz** (T17); **all** to rehearse it. Twice, timed, between the 16:50 freeze and 17:30.

Everything below is what the code in this repo actually does, verified by running it. Where a
beat from the brief is not built, it is named as roadmap rather than narrated as a feature;
see §*What we do not claim* at the end. That section is not modesty, it is the reason nothing
in the first four minutes can be contradicted by a follow-up question.

---

## The shape of the demo

**Split screen, one machine.** `make stage` puts the protocol log in the left-hand terminal
pane and the page in the right-hand browser. Every run is started from the page's **Run**
button: `frontend/serve.py` spawns `backend.rounds` with stdout inherited, so the log lands
in the pane while the animation plays in the browser. Neither half is a recording of the
other, and that is the point. Say it once, early.

The left pane is where **Flower** is visible: `flwr 1.34.0 · run_simulation · InMemoryGrid ·
3 SuperNodes, one process each`, then `InMemoryGrid.send_and_receive · 3 × Message(QUERY)`
per round. The right pane is where the *argument* is visible: the dashed firm perimeters,
the coverage matrix, the byte ledger.

A full run replays in about **20 seconds** at 1×. That is deliberate: the narrator paces it
with `Step ›` and holds on round 2 for as long as the question takes.

**Round 1 grades with a model too, when one is reachable.** It grades and never re-decides,
and the matrix is the same matrix either way. So on a cache-only laptop those calls miss, a
grade is never allowed to fail a round, and round 1 quietly falls back to the declared
reading. That is what the pane will show at the table, and it is what the beat sheet below
narrates. Do not promise a judge round-1 grading lines that this machine will not print.

---

## Before the judges arrive — the setup checklist

Run this at 16:50 and leave it running. Do not rebuild any of it while someone is standing
there.

- [ ] **`make doctor`, and read four lines of it.** `model` must name a model, `endpoint`
      must be set, `cache` must be non-zero, and `traces` must say `4 of 4`. Those four
      decide whether round 2 has anything to find. Everything else in `doctor` is scenery.
- [ ] **`make traces`** — one run per scenario, so the selector switches offline with a judge
      at the table. It warns loudly if `MODEL` is empty; heed it, or all four scenarios trace
      as NON-COMPLIANT and the selector shows a judge four broken bids.
- [ ] **`.cache/model` must exist in the checkout you are demoing from.** It is gitignored,
      so it lives on exactly one laptop: the one that made the calls. A fresh clone, a
      worktree, or a teammate's machine has an empty cache, and with no endpoint reachable
      `resolve_reader` returns `None`, round 2 finds nothing, and the bid ends
      NON-COMPLIANT. This is the single most likely way the demo dies. Check it, do not
      assume it.
- [ ] `make stage` running, terminal pane left, browser right, both readable from a metre away
- [ ] Second browser tab: the Hub app page, `flower.ai/apps/i53n1/consortium/`
- [ ] Third tab: the public GitHub repo
- [ ] One rehearsed run already done on this machine, this hour, then `make stage` again so
      the run they watch starts from nothing
- [ ] Laptop on hotspot, not venue wifi
- [ ] Font size up in both panes. Two people can read a terminal over your shoulder; four cannot.

**Who talks.** One narrator, one driver. The narrator never touches the keyboard and the
driver never explains. The single most common way a table demo runs to seven minutes is two
people both narrating.

---

## The 4-minute run

Four minutes into a five-minute slot. The remaining minute is theirs, and §13 of the brief is
where the marks actually are.

| Time | Beat | Who |
|---|---|---|
| 0:00–0:30 | **The problem.** "Three architecture firms are bidding one government hospital together, because the job is too big for any one of them. Next month they compete against each other. To submit, they have to prove *as a team* that they cover every requirement, and none of them will show the others its client list, its fees or its staff. Today that proof is assembled by emailing spreadsheets." | narrator |
| 0:30–0:55 | **The gate, up front.** Hub tab: "this is published — `flwr chat`, `@i53n1/consortium`." Repo tab. Then: *"the SF330 is the example; the harness is the product."* Back to the stage screen. | narrator + driver |
| 0:55–1:10 | **Set the screen.** "Left pane is the protocol's own log — that is Flower: `InMemoryGrid`, three SuperNodes, one process each. Right is the same run as a picture. I start it from the page." Press **Run**. | driver |
| 1:10–1:50 | **Round 1 — blind attestation.** Six typed requirements go out, 1.4 kB. Each firm searches **only its own library** and answers with banded existence proofs — 19, 13 and 18 attestations. "Not one record left a building. What crossed is a handle and a band." Matrix fills: **R1, R2, R3, R5, R6 green. R4 red.** | driver narrates the panes, narrator holds the line |
| 1:50–2:10 | **Why R4 is invisible.** Click **R4** on the page. "Every other requirement is answered from a database field. R4 needs one person who has done both a hospital and an earthquake-strengthening job, named on both projects. No firm's fields say that about anybody. Each firm covers five of six on its own, and not one of them can reach this one." | narrator |
| 2:10–2:55 | **Round 2 — the beat.** "The coordinator broadcasts the *gap*, not the answer." Left pane: `(gap R4 = 2 B)`. Then all three nodes, each on its own actor pid: `firm A gap R4 - re-reading 8 records`, `firm C ... nothing here evidences it`, and **`firm B  R4 <- FIRM_B::PERSON::007 - prose details seismic base isolation and strengthening on an acute care wing upgrade`**. Cell turns green. "Firm B had that filed as civic work. Only the bio says the building was a hospital. And Firm B only re-read its bios because it was told about a hole in *somebody else's* coverage." | narrator |
| 2:55–3:20 | **The ledger.** Right pane: **about 33 kB banded forward, 2 bytes back, 0 B of record content, 2 rounds.** Read the kB figure off the pane rather than off this page — it drifts a few hundred bytes per run. "Zero is by construction: the protocol has no field that can carry a record. And the model's reasoning stayed on the firm's node; what crossed the wire was requirement-side vocabulary." | driver |
| 3:20–3:45 | **It is a harness.** Scenario selector — switch to **transit-tunnel**, then **defence-secure-lab**. "Same code, same protocol, no branches. A transit tunnel, a secure lab, a campus energy retrofit. The gap sits at a **different firm** in each one, and the harness does not know which." | driver |
| 3:45–4:00 | **Close.** "Three pluggable pieces: a requirement list, a banding vocabulary, a cost per disclosure. Swap those and the same loop runs for hospitals sizing a trial cohort without sharing patients. Next is the disclosure optimiser and the human approval gate: the half we designed and did not build today." Stop. | narrator |

### The two beats that must not be improvised

**2:10 — round 2 closing R4.** If this does not converge, the demo has no argument. It is
also the beat that depends on the model cache, so the pre-flight check above is not optional.
Per the brief's R2 risk, the corpus wording is the tuning parameter, not the prompt, but at
17:30 neither is a live option, so verify at 16:50 instead.

**3:20 — the scenario switch.** This is what turns "an app" into "a harness" in a judge's
head, and it costs eight seconds. Know which two scenarios you switch to, and know that the
gap is at Firm C in transit-tunnel and Firm A in defence-secure-lab — a judge who spots that
the answer moves has understood the whole thing, and you want to be ready to confirm it.

---

## The 90-second version

Use this when a judge arrives late, is visibly rushed, or has already spent four minutes at
the table next to ours. Cutting to it mid-demo is a legitimate move: say "let me jump to the
part that matters" rather than speeding up.

| Time | Beat |
|---|---|
| 0:00–0:15 | Three firms, one government bid, competitors next month. Published on Hub as `@i53n1/consortium`. |
| 0:15–0:40 | Round 1. Every firm answers from its own library only: banded yes/no answers, no records. Joint matrix: **R4 red**, and no firm's fields can reach it. |
| 0:40–1:05 | Round 2. The **gap** goes back — 2 bytes. All three re-read their own prose; Firm B finds the one person who is both, filed as civic work. Green. |
| 1:05–1:20 | Ledger: about 33 kB banded forward, 2 B back, **0 B of record content**, by construction. |
| 1:20–1:30 | Scenario selector: four solicitations, same code, gap at a different firm each time. "The SF330 is the example; the harness is the product." |

---

## The 3-minute stage version — only if we make the top 3

Announced at 18:45, presented immediately. Different room, different constraints: no terminal
they can read, no time for a live run, and the audience is other builders.

- **Do not run the demo live on stage.** Use the deck (`docs/slides/`, `make slides`) and a
  recorded run. A live run in front of 130 people on shared wifi is a coin flip we have no
  reason to take.
- The deck is built for exactly this. Fourteen slides: the problem as a picture, the coverage
  grid, the row that lives in a paragraph, the loop, the architecture, round 2, the byte
  ledger, safety, Flower, four scenarios, the roadmap. Every slide carries a presenter note
  naming the axis it serves.
- Say the harness sentence twice, once at the start and once at the end. On stage it is the
  only thing anyone remembers.
- Assume nobody in the room has seen a bid. The deck says "hospital" and "earthquake
  strengthening" rather than "healthcare sector" and "seismic retrofit", and it names SF330
  once, glossed. Keep the spoken version at that level too.

---

## Framing notes

**If they ask what a harness is.** "Everything except the form. A requirement list, a banding
vocabulary, and a cost per disclosure are the three things you swap." Then use the scenario
selector rather than the architecture diagram; brief §1.1 has the sentence.

**If they push on centralisation.** Brief §13 has the full answer. The short one: the
coordinator sees banded yes/no answers, the same relationship gradients have to training data.

**If they ask whether it really runs on SuperGrid.** It is published at
`flower.ai/apps/i53n1/consortium` and invoked from `flwr chat`. The published surface is an
`AgentApp` running the same `backend.protocol.run` over `LocalGrid`; the federated surface
runs it over `InMemoryGrid` under the simulation runtime, and over `GrpcGrid` against a real
SuperLink. The left pane names which one is carrying the messages, so we never have to imply
a SuperLink we are not using. We drive the table demo locally because 130 people are on the
same wifi, not because the deployment path is a mock.

**If SuperGrid is down or slow at 17:30.** Say so plainly and drive the local run. An honest
fallback costs nothing. Pretending a cached result is a live SuperGrid round costs everything
if they ask one more question.

**If the model endpoint is down at 17:30.** Nothing changes: the run replays from
`.cache/model` and the left pane prints `(from cache)` on every re-examination. Say that out
loud rather than hoping nobody reads it: "those are cached responses, and the pane says so."
A judge who spots an unmentioned `(from cache)` is a judge who stops believing the rest.

---

## What we do not claim

Round 3 is designed and not built. `backend/optimiser.py`, `approval.py`, `assemble.py` and
`baselines.py` are docstrings. So none of the following is in the demo, and none of it may be
narrated as if it runs:

- a disclosure count ("9 of 40"), a denial, or a live substitution
- a human approval gate, or "9 of 9 approved"
- an assembled SF330
- the three-condition baseline table, including the centralised-pool row
- a bander rejection count. The closed vocabulary is enforced in `backend/schema.py` and
  `firm_node.py` bands every field before it leaves, but there is no instrumented counter,
  so do not offer a number

Two of these are worth saying out loud as roadmap, because a judge asking "then what?" is
asking the right question: **the disclosure optimiser** (greedy weighted set cover over
disclosure cost, under the Section F cap of ten) and **the per-record human gate**, where a
denial makes the optimiser re-plan rather than get routed around. Brief §5.4 and §7.2 have
the design; the deck's roadmap slide has the one-line version.

One claim in the brief does not survive contact with the data, and the correction is
stronger than the original. The brief says each firm "self-assesses **compliant**" in round 1
and is "confidently wrong". It does not: each firm covers R1, R2, R3, R5 and R6 on its own,
and **no** firm can reach R4, because R4 is a Section G join that no firm's declared fields
describe. So do not say "confidently wrong". Say: **"Each firm covers five of six on its own.
R4 is invisible to structured search at every one of them, and it takes the joint matrix to
license the one local re-read that finds it."** That is what the run shows, and it is a
better argument for the protocol than the version we planned.

> The page's round-1 narration still says "every firm's own self-assessment reads compliant".
> That is the same overclaim. Flagged to the Viz owner: `frontend/app.js`, `narrate()`, the
> `matrix` case.
