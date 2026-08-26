# Demo script

Judges come **to the table** at 17:30 and give us **3–5 minutes**. That is a conversation,
not a stage pitch, and it changes three things: we lead with the submission gate, we build
in silence for questions, and we never depend on the venue wifi.

Owner: **Viz** (T17) to build the talking points around this; **all** to rehearse it. Twice,
timed, between the 16:50 freeze and 17:30.

---

## Before the judges arrive — the setup checklist

Run this at 16:50 and leave it running. Do not rebuild any of it while someone is standing
there.

- [ ] Hub app page open in a browser tab: `flower.ai/apps/<account>/consortium/`
- [ ] Second tab: the public GitHub repo
- [ ] Terminal 1: `make demo` **already run once** to warm caches, then reset — the run they
      watch must be a fresh one that has definitely worked on this machine, this hour
- [ ] Terminal 2: `flwr chat` logged in, ready to type `@<publisher>/consortium`
- [ ] The three-condition baseline table (§7.1) printed or on screen — this is the artefact
      judges linger on, and it must not require a re-run to show
- [ ] Laptop on hotspot, not venue wifi
- [ ] Font size up. Two people can read a terminal over your shoulder; four cannot.

**Who talks.** One narrator, one driver. The narrator never touches the keyboard and the
driver never explains — the single most common way a table demo runs to seven minutes is
two people both narrating.

---

## The 4-minute run

Four minutes into a five-minute slot. The remaining minute is theirs, and §13 of the brief
is where the marks actually are.

| Time | Beat | Who |
|---|---|---|
| 0:00–0:30 | **The problem.** "Three architecture firms bid one federal hospital as a joint venture. Next month they compete. To submit, they must prove *together* that the team covers every requirement — without any of them exposing their client list, their fees, or their roster. Today that is done by emailing spreadsheets." | narrator |
| 0:30–1:00 | **The gate, up front.** Hub tab: "this is published — `flwr chat`, `@<publisher>/consortium`, runs on SuperGrid." Second tab: the repo. Then: *"the SF330 is the example; the harness is the product."* | narrator + driver |
| 1:00–1:45 | **Round 1.** `make rounds`. Each firm's agent searches only its own library and returns banded attestations. Every firm self-assesses **compliant**. The joint coverage matrix does not: **R4 red.** "No single firm could have seen this. Each one is confidently wrong." | driver narrates the matrix, narrator holds the line |
| 1:45–2:30 | **Round 2 — the beat.** The coordinator broadcasts the *gap*, not the answer. Firm B's agent re-reads a bio it had already classified as purely structural, finds an acute-care wing retrofit in the project history, and emits the Section G link. Cell turns green. "Firm B's agent only found that because it was told about a hole in *Firm A's* coverage. That is the multiplier." | narrator |
| 2:30–3:15 | **Round 3 — minimum disclosure.** Optimiser requests **9 of 40** records. BD lead **denies** one competitively sensitive project. Optimiser re-runs and substitutes live. "The refusal is honoured by re-planning, not routed around." | driver |
| 3:15–3:45 | **The safety ledger.** 0 raw bytes out before authorisation · 0 confidential clients named · 9 of 9 disclosures human-approved · 2 attestations rejected by the bander. "The guardrail fired twice during that run. It rejects rather than sanitises." | narrator |
| 3:45–4:00 | **Close.** "Compliance matched the centralised oracle at a fifth of the disclosure. Swap the requirement set, the vocabulary and the cost function and the same harness runs cross-hospital cohort feasibility." Stop. | narrator |

### The two beats that must not be improvised

**2:30 — the denial and substitution.** This is the moment that gets the reaction. Script
which record is denied, know what the optimiser substitutes, and have run it end to end at
least twice on this machine. If it is flaky at 16:40, cut to the single-pass optimiser and
narrate the substitution as a design property instead of showing it.

**1:45 — round 2 closing R4.** If this does not converge, the demo has no argument. Per the
brief's R2 risk, the corpus wording is the tuning parameter, not the prompt.

---

## The 90-second version

Use this when a judge arrives late, is visibly rushed, or has already spent four minutes at
the table next to ours. Cutting to it mid-demo is a legitimate move — say "let me jump to
the part that matters" rather than speeding up.

| Time | Beat |
|---|---|
| 0:00–0:15 | Three firms, one federal bid, competitors next month. Published on Hub, runs on SuperGrid. |
| 0:15–0:35 | Round 1. Every firm self-assesses compliant. The joint matrix: **R4 red**. |
| 0:35–0:55 | Round 2. Gap broadcast; Firm B's agent finds the one person who is both. Green. |
| 0:55–1:15 | Round 3. 9 of 40 disclosed, one denial, live substitution. |
| 1:15–1:30 | Ledger: 0 bytes, 0 names, 9 of 9 approved. "The SF330 is the example; the harness is the product." |

---

## The 3-minute stage version — only if we make the top 3

Announced at 18:45, presented immediately. Different room, different constraints: no
terminal they can read, no time for a live run, and the audience is other builders.

- **Do not run the demo live on stage.** Screenshots or a recorded terminal. A live run in
  front of 130 people on shared wifi is a coin flip we have no reason to take.
- Three slides, one idea each: (1) three competitors, one bid, nobody can check compliance
  alone; (2) the four-stage loop with round 2 highlighted; (3) the three-condition table.
- Say the harness sentence twice — once at the start, once at the end. On stage it is the
  only thing anyone remembers.
- Ten seconds of framing if the room is UK-heavy: "US federal qualifications form —
  Section G is a person-by-project matrix." Do not explain more.

---

## Framing notes

**If they ask what a harness is.** "Everything except the SF330. A requirement set, a
banding vocabulary, and a disclosure-cost function are the three things you swap." Do not
reach for the architecture diagram — brief §1.1 has the sentence, use it.

**If they push on centralisation.** Brief §13 has the full answer. The short one: the
coordinator sees banded existence proofs, the same relationship gradients have to training
data.

**If SuperGrid is down or slow at 17:30.** Say so plainly and drive the local simulation:
"the published app is there, we are running the local federation because 130 of us are on
the same wifi." An honest fallback costs nothing. Pretending a cached result is a live
SuperGrid round costs everything if they ask one more question.
