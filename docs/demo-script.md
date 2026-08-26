# Demo script

Judges come **to the table** at 17:30 and give us **3–5 minutes**. That is a conversation,
not a stage pitch, and it changes three things: we lead with the submission gate, we build
in silence for questions, and we never depend on the venue wifi.

Owner: **Viz** (T17) to build the talking points around this; **all** to rehearse it. Twice,
timed, between the 16:50 freeze and 17:30.

> **This script covers what runs.** Stage four of the loop — the disclosure optimiser and
> the human approval gate — is designed in brief §5.4 and **not built**. Every beat below
> has been executed end to end on this machine; the numbers in it are measured, not
> projected. If you find yourself about to narrate a denial-and-substitution, stop: that
> beat does not exist, and §"What we did not build" is how to answer for it.

**Round 1 grades with a model too, when one is reachable.** It grades and never re-decides —
the matrix is the same matrix either way — so on a cache-only laptop those calls miss, a grade
is never allowed to fail a round, and round 1 quietly falls back to the declared reading. That
is what the pane will show at the table, and it is what the beat sheet below narrates. Do not
promise a judge round-1 grading lines that this machine will not print.

---

## Before the judges arrive — the setup checklist

Run this at 16:50 and leave it running. Do not rebuild any of it while someone is standing
there.

- [ ] Hub app page open in a browser tab: `flower.ai/apps/i53n1/consortium/`
- [ ] Second tab: the public GitHub repo
- [ ] **`make traces MODEL=/models/Qwen3.5-397B-A17B-FP8` has been run**, against a
      reachable endpoint, *after the last prompt edit*. This is the one non-negotiable
      item — see below.
- [ ] `ls .cache/model/` is non-empty. That is what makes the demo survive the wifi.
- [ ] Terminal 1: `make watch MODEL=…` rehearsed once on this machine, this hour
- [ ] Terminal 2: `flwr chat` logged in, ready to type `@i53n1/consortium`
- [ ] Laptop on hotspot, not venue wifi
- [ ] Font size up. Two people can read a terminal over your shoulder; four cannot.

**The cache is the demo.** Round 2 is a model reading prose, and the shared Qwen endpoint
answered in ~240s under load — most of SuperGrid's five-minute task budget for one firm.
Cached, the same round lands in milliseconds. The cache is keyed on the exact request, so
**any edit to `agents/prompts/round2_reexamine.md` throws all of it away.** If you touch the
prompt after 16:00, re-warm before the freeze or you will be narrating an open gap.

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
| 0:30–1:00 | **The gate, up front.** Hub tab: "this is published — `flwr chat`, `@i53n1/consortium`, runs on SuperGrid." Second tab: the repo. Then: *"the SF330 is the example; the harness is the product."* | narrator + driver |
| 1:00–1:50 | **Round 1.** `make watch MODEL=…`. Each firm's agent searches only its own library — **structured fields only, no model call** — and returns banded attestations. Every firm self-assesses **compliant**. The joint matrix does not: **R4 red.** "No single firm could have seen this. Each one is confidently wrong." | driver narrates the matrix, narrator holds the line |
| 1:50–2:50 | **Round 2 — the beat.** The coordinator broadcasts the *gap*: the string `R4`, two bytes, and nothing else. Firm B's agent re-reads a bio it had already classified as purely structural — its projects are all *filed* as civic — and the prose says acute-care wing. It returns the handle; the coordinator checks the Section G join in code. **R4 goes green, and the run converges — 2 rounds, not 3.** "Firm B's agent only found that because it was told about a hole in *Firm A's* coverage. That is the multiplier." | narrator |
| 2:50–3:30 | **The safety ledger.** Click a requirement in the UI. `record content on the wire: 0 B` — zero by construction, not by policy: no field on an `Attestation` can carry a title, a client, a fee, or a name. **33 kB of attestations forward; 2 bytes back.** Cost-3 records were never offered, in either round. The model's own sentence never left Firm B's node — the wire got requirement vocabulary. | narrator |
| 3:30–4:00 | **Close.** Switch the scenario selector to `transit-tunnel` — same harness, different solicitation, different firm holding the gap, no re-run. "Swap the requirement set, the banding vocabulary and the cost function and the same harness runs cross-hospital cohort feasibility." Stop. | driver, then narrator |

### The beat that must not be improvised

**1:50 — round 2 closing R4.** If this does not converge, the demo has no argument. It is
also the only beat with a live dependency, which is why the cache checklist above exists.

Per brief R2 the corpus wording is the tuning parameter — but the actual failure we hit was
the *prompt*, not the corpus: an earlier version told the model to judge substance and also
not to infer, and Qwen3.5 resolved the contradiction by refusing every scenario's evidence.
Read `agents/prompts/round2_reexamine.md` before you touch `data/`. It is the cheaper check
and it is the one that was wrong.

If round 2 is genuinely dead at 16:40, run without `MODEL=` and narrate the honest version:
"round 1 completes, the gap is detected and broadcast, and re-examination needs a model we
cannot reach from this room." Detecting the gap is still a result no single firm could
produce. Do not pretend a cached result is a live round.

---

## The 90-second version

Use this when a judge arrives late, is visibly rushed, or has already spent four minutes at
the table next to ours. Cutting to it mid-demo is a legitimate move — say "let me jump to
the part that matters" rather than speeding up.

| Time | Beat |
|---|---|
| 0:00–0:15 | Three firms, one federal bid, competitors next month. Published on Hub, runs on SuperGrid. |
| 0:15–0:35 | Round 1, structured search only. Every firm self-assesses compliant. The joint matrix: **R4 red**. |
| 0:35–1:00 | Round 2. The gap goes out — two bytes. Firm B's agent reads its own prose and finds the one person who is both. Green, converged. |
| 1:00–1:20 | Ledger: 0 bytes of record content, 0 clients named, 33 kB out against 2 bytes back. |
| 1:20–1:30 | Scenario selector: same harness, four solicitations. "The SF330 is the example; the harness is the product." |

---

## What we did not build — say it before they find it

Volunteering this costs thirty seconds and buys the credibility of everything else. A judge
who greps `backend/optimiser.py` and finds a docstring after you claimed an optimiser has
stopped listening to you.

- **The disclosure optimiser and the approval gate.** Designed in brief §5.4 — greedy
  weighted set cover under the Section F cap of ten, then every disclosure routed through a
  named human. `backend/optimiser.py`, `approval.py`, `assemble.py` are docstrings. What
  makes the design credible is already in the data and enforced by the tests:
  `disclosure_cost` on every record, cost-3 excluded from the candidate set in both rounds,
  and a substitutable cost-2 record the invariant tests assert exists.
- **The three-condition baseline table.** `backend/baselines.py` is a stub and
  `make baselines` prints nothing. `data/ground_truth.json` holds the three readings the
  table would score — `declared` (what round 1 can match), `firm` (what a firm knows alone),
  `oracle` (what a centralised pool would find) — and `data/generate.py` refuses to write it
  if the gap between them ever closes. The claim "consortium matches the centralised oracle"
  is checked in the corpus, not measured in a run.
- **The bander.** There is no egress validator and no rejection counter. Do **not** say "the
  guardrail fired twice" — it does not exist. The privacy property is structural instead,
  which is the stronger claim: the schema has no field that can carry record content, so
  `record_bytes` is 0 by construction.

The honest framing: *"three of the four stages run. The fourth is where minimum disclosure
and the human gate go, and the data model already encodes what it needs."*

---

## The 3-minute stage version — only if we make the top 3

Announced at 18:45, presented immediately. Different room, different constraints: no
terminal they can read, no time for a live run, and the audience is other builders.

- **Do not run the demo live on stage.** Screenshots or a recorded terminal. A live run in
  front of 130 people on shared wifi is a coin flip we have no reason to take.
- Three slides, one idea each: (1) three competitors, one bid, nobody can check compliance
  alone; (2) the four-stage loop with round 2 highlighted and stage four marked as design;
  (3) the two-bytes-back-for-33-kB-forward ledger.
- Say the harness sentence twice — once at the start, once at the end. On stage it is the
  only thing anyone remembers.
- Ten seconds of framing if the room is UK-heavy: "US federal qualifications form —
  Section G is a person-by-project matrix." Do not explain more.

---

## Framing notes

**If they ask what a harness is.** "Everything except the SF330. A requirement set, a
banding vocabulary, and a disclosure-cost function are the three things you swap." Then show
the scenario selector — four of them ship, and they are not re-skins: the delivery method,
the client type, the certification threshold and the firm holding the gap all move. Do not
reach for the architecture diagram; brief §1.1 has the sentence.

**If they push on centralisation.** Brief §13 has the full answer. The short one: the
coordinator sees banded existence proofs, the same relationship gradients have to training
data.

**If they ask why only two rounds.** Because it converged. The loop runs to `num-rounds` *or*
until the gap closes *or* until a round returns nothing new — `stopped: "converged"` in the
trace. A third identical broadcast would only cost time.

**If they ask whether the model could just be told the answer.** The node is handed the
uncovered requirement id and its predicate, never the answer and never which record to look
at. `data/scenarios.json` does carry an evidence lexicon — that is the oracle `generate.py`
uses to prove the cell is findable, and handing it to a node would be handing it the answer
key. Returned handles the model was not shown are discarded.

**If SuperGrid is down or slow at 17:30.** Say so plainly and drive the local simulation:
"the published app is there, we are running the local federation because 130 of us are on
the same wifi." An honest fallback costs nothing. Pretending a cached result is a live
SuperGrid round costs everything if they ask one more question.
