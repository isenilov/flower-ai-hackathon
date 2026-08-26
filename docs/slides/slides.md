---
theme: default
title: Consortium
titleTemplate: '%s'
info: |
  Collaborative Agent Hackathon — Flower Labs, University of Cambridge, 26 Aug 2026.
  Track 1: SuperGrid. Published as @i53n1/consortium.
author: Consortium
class: text-center
transition: slide-left
drawings:
  persist: false
fonts:
  sans: Inter
  mono: JetBrains Mono
---

# Consortium

<div class="mt-6 text-2xl leading-relaxed">
Three firms have to prove their joint bid qualifies.<br>
None of them will show the others their data.
</div>

<div class="mt-10 text-lg opacity-80">
This is the protocol that settles it. No record moves.
</div>

<div class="mt-14 text-sm opacity-50">
Track 1 — SuperGrid &nbsp;·&nbsp; <code>flwr chat</code> → <code>@i53n1/consortium</code>
</div>

<!--
Read the two lines and stop. Everything else is on the next slide as a picture.

The through-line, said here and again at the end: the bidding form is the example, the
harness is the product.
-->

---
layout: center
class: text-left
---

# One contract. Three firms. Nobody can check.

```mermaid {scale: 0.82}
flowchart BT
    a["<b>Firm A</b><br/>sees only its own<br/>clients · fees · staff"]
    b["<b>Firm B</b><br/>sees only its own<br/>clients · fees · staff"]
    c["<b>Firm C</b><br/>sees only its own<br/>clients · fees · staff"]
    q["<b>Together, does this team meet every requirement in the contract?</b>"]

    a -. "cannot answer" .-> q
    b -. "cannot answer" .-> q
    c -. "cannot answer" .-> q

    style q fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    style a fill:#f3f4f6,stroke:#9ca3af,color:#374151
    style b fill:#f3f4f6,stroke:#9ca3af,color:#374151
    style c fill:#f3f4f6,stroke:#9ca3af,color:#374151
```

<div class="cap mt-2">

Work too big for one firm gets bid by three. The client wants one proof that the
**whole team** qualifies. They compete against each other next month, and today that proof is
assembled by emailing spreadsheets.

</div>

<!--
Impact axis, and the slide that has to land. Say it in the judge's own language: a hospital,
a tunnel, an airport - too big for one firm, so three of them bid it as a team.

The tension in one sentence: to prove the team qualifies they would each have to hand over the
client list, the fee history and the staff roster they are about to compete with.

Do not say "joint venture", "solicitation" or "SF330" yet. None of those words earn anything
in the first minute.
-->

---
layout: center
class: text-left
---

# What the database fields can prove

<div class="text-xs opacity-55 mt-1">every firm searching its own records, matched on declared fields only</div>

<div class="grid grid-cols-[20rem_4.5rem_4.5rem_4.5rem] gap-x-3 gap-y-1 text-sm mt-3">

<div></div>
<div class="text-center text-xs font-bold opacity-60">Firm A</div>
<div class="text-center text-xs font-bold opacity-60">Firm B</div>
<div class="text-center text-xs font-bold opacity-60">Firm C</div>

<div>Hospital projects over $50m</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div>

<div>Design-build, federal client</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div>

<div>Project manager with hospital work</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div>

<div class="font-bold">One person: hospital <i>and</i> earthquake retrofit</div>
<div class="maybe">?</div><div class="maybe">?</div><div class="maybe">?</div>

<div>Chartered structural lead</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div>

<div>Green-certified projects</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div>

</div>

<div class="flex gap-6 mt-3 text-xs opacity-70">
<div><span class="ok px-2">✓</span> &nbsp;the fields settle it</div>
<div><span class="maybe px-2">?</span> &nbsp;the fields cannot say either way</div>
</div>

<div v-click class="cap mt-3">

Five rows are settled by the fields at every firm. The fourth one the fields cannot answer, so
the coordinator records it as an open gap. **An open gap is not the same as nobody having it.**

</div>

<!--
This is the design constraint, and the corpora are built backwards from it.

Say "on the fields alone" out loud. The grid is what a structured search returns, NOT what the
firms hold, and the next slide turns on that difference. A judge who reads this grid as
"nobody has such a person" will think round 2 contradicts it.

Careful with the wording in the other direction too: it is NOT "each firm thinks it is fine
and is wrong". Verified off the run - round 1 has have=0 on that row, and every firm alone
clears the other five.
-->

---
layout: center
class: text-left
---

# Firm B had the person all along

<div class="text-xs opacity-55 mt-1">one record at Firm B, read two ways</div>

<div class="grid grid-cols-2 gap-6 mt-3">
<div>

### on file — what round 1 matched

```text
person   FIRM_B::PERSON::007
role     structural lead
sector   civic        <- not healthcare
```

<div class="mt-2 text-xs opacity-70">The predicate needs <code>sector=healthcare</code>. This record fails it, so round 1 never even offers it to a model.</div>

</div>
<div v-click>

### in prose — what round 2 read

<div class="tile">
"… <b style="display:inline">seismic</b> base isolation and strengthening on an
<b style="display:inline">acute care wing</b> upgrade …"
</div>

<div class="mt-2 text-xs opacity-70">A hospital wing, filed as civic work by a firm that saw a concrete frame and a city client.</div>

</div>
</div>

<div v-click class="mt-5">

<div class="text-xs opacity-55 mb-1">the fourth row, both ways</div>

<div class="grid grid-cols-[13rem_4.5rem_4.5rem_4.5rem] gap-x-3 gap-y-1 text-sm">
<div></div>
<div class="text-center text-xs font-bold opacity-60">Firm A</div>
<div class="text-center text-xs font-bold opacity-60">Firm B</div>
<div class="text-center text-xs font-bold opacity-60">Firm C</div>

<div>matched on fields</div>
<div class="maybe">?</div><div class="maybe">?</div><div class="maybe">?</div>

<div>read in the bios</div>
<div class="no">✗</div><div class="ok">✓</div><div class="no">✗</div>
</div>

</div>

<!--
This slide is the answer to "wait, you said nobody had one". Firm B held the person the whole
time. `agents/search.py` is a structured predicate over declared banded fields, and
`agents/matcher.py` grades what that prefilter admits without being allowed to add to it, so a
record filed `sector: civic` never reaches a model in round 1. In the trace it is one field:
round 1 broadcasts `reads_text: false`, round 2 broadcasts `reads_text: true`.

Why round 1 does not just read everything: cost. Matching six predicates over a library is
cheap; reading every paragraph against every requirement is the expensive half, and the joint
grid is what licenses spending it on exactly one requirement.

Two glosses for anyone outside construction, ten seconds: seismic means earthquake, and a
retrofit is strengthening a building that already stands. The fourth row is SF330 Section G,
the person-by-project grid on the US federal form every bid team files.
-->

---
layout: center
class: text-left
---

# The loop

```mermaid {scale: 0.7}
flowchart LR
    ask["<b>1 · ask</b><br/>each agent matches its own<br/>records on declared fields"]
    compare["<b>2 · compare</b><br/>build the team grid,<br/>find the empty row"]
    reread["<b>3 · re-read</b><br/>send the gap back, agents<br/>re-read the prose they filed"]
    release["<b>4 · release</b><br/>disclose the least you can,<br/>a human approves each"]

    ask --> compare --> reread --> release
    reread -. "still open" .-> compare

    style ask fill:#e0f2fe,stroke:#0369a1,color:#0c4a6e
    style compare fill:#e0f2fe,stroke:#0369a1,color:#0c4a6e
    style reread fill:#dcfce7,stroke:#15803d,color:#14532d
    style release fill:#f3f4f6,stroke:#9ca3af,color:#4b5563,stroke-dasharray: 5 3
```

<div class="cap mt-3">

Stages 1–3 run today. Stage 4 is the dashed box: designed, specified, not built.
Nothing in the loop is about construction. The domain enters through three pluggable pieces: a
requirement list, a fixed vocabulary, and a cost per disclosure.

</div>

<!--
Innovation axis, and the answer to "isn't this just federated retrieval?" Retrieval settles
what exists. This settles what to reveal, and it broadcasts the question rather than the
answer.

Be straight about the dashed box. A judge who catches an overclaim stops believing the rest.
-->

---
layout: center
class: text-left
---

# Architecture

<div class="coordinator">
<b>Coordinator</b>builds the team grid &nbsp;·&nbsp; names the gap &nbsp;·&nbsp; never sees a record
</div>

<div class="flex justify-center gap-14 my-2 text-xs opacity-70">
<div>↓ &nbsp;the requirements, and the gap</div>
<div>↑ &nbsp;banded answers, nothing else</div>
</div>

<div class="boundary">trust boundary</div>

<div class="grid grid-cols-3 gap-4 mt-3">

<div class="firm">
<b>Firm A · SuperNode</b>
<div class="step">private library<div class="opacity-60">projects · people · clients · fees</div></div>
<div class="arrow">↓</div>
<div class="step">agent: match · re-read</div>
<div class="arrow">↓</div>
<div class="step">band to a fixed vocabulary</div>
</div>

<div class="firm">
<b>Firm B · SuperNode</b>
<div class="step">private library<div class="opacity-60">projects · people · clients · fees</div></div>
<div class="arrow">↓</div>
<div class="step">agent: match · re-read</div>
<div class="arrow">↓</div>
<div class="step">band to a fixed vocabulary</div>
</div>

<div class="firm">
<b>Firm C · SuperNode</b>
<div class="step">private library<div class="opacity-60">projects · people · clients · fees</div></div>
<div class="arrow">↓</div>
<div class="step">agent: match · re-read</div>
<div class="arrow">↓</div>
<div class="step">band to a fixed vocabulary</div>
</div>

</div>

<div class="cap mt-4">

Three identical stacks, on purpose. A library never leaves its own node. What crosses the
boundary is a handle and a band: `FIRM_B::PERSON::007`, `sector=civic`, `value=50-100M`. The
message has no field that could carry a name, a client or a fee.

</div>

<style>
.coordinator {
  background: #e0f2fe;
  color: #0c4a6e;
  border: 1px solid #7dd3fc;
  border-radius: 0.4rem;
  padding: 0.55rem;
  text-align: center;
  font-size: 0.78rem;
}
.coordinator b { display: block; font-size: 0.9rem; }
.boundary {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  font-size: 0.6rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.5;
}
.boundary::before, .boundary::after {
  content: "";
  flex: 1;
  border-top: 2px dashed currentColor;
}
.firm {
  border: 1px solid #d9a441;
  background: #fffbeb;
  border-radius: 0.4rem;
  padding: 0.5rem;
  text-align: center;
  color: #78350f;
}
html.dark .firm { background: #241d12; border-color: #a16207; color: #fcd34d; }
.firm b { display: block; font-size: 0.76rem; margin-bottom: 0.35rem; }
.step {
  background: #fef3c7;
  border-radius: 0.25rem;
  padding: 0.22rem 0.3rem;
  font-size: 0.66rem;
  line-height: 1.3;
}
html.dark .step { background: #3d3218; color: #fde68a; }
.arrow { font-size: 0.6rem; opacity: 0.5; line-height: 1.3; }
</style>

<!--
Use of Flower, plus Safety. The three firm stacks are drawn identically on purpose - that is
the harness claim as a picture.

If they push on centralisation: the coordinator sees banded yes/no answers, the same
relationship that gradients have to training data.
-->

---
layout: center
class: text-left
---

# The coordinator sends the gap, not the answer

```mermaid {scale: 0.72}
flowchart LR
    c["<b>Coordinator</b><br/>sends <b>R4</b><br/><i>2 bytes</i>"]
    a["Firm A<br/>reads the bios<br/>its fields ruled out"]
    b["Firm B<br/>reads the bios<br/>its fields ruled out"]
    x["Firm C<br/>reads the bios<br/>its fields ruled out"]
    ra["nothing here"]
    rb["<b>PERSON::007</b><br/>found in a paragraph"]
    rx["nothing here"]

    c ==> a --> ra
    c ==> b --> rb
    c ==> x --> rx

    style c fill:#e0f2fe,stroke:#0369a1,color:#0c4a6e
    style rb fill:#dcfce7,stroke:#15803d,color:#14532d
    style ra fill:#f3f4f6,stroke:#9ca3af,color:#4b5563
    style rx fill:#f3f4f6,stroke:#9ca3af,color:#4b5563
    style a fill:#fff,stroke:#6b7280,color:#374151
    style b fill:#fff,stroke:#374151,color:#111827
    style x fill:#fff,stroke:#6b7280,color:#374151
```

<div class="cap mt-3">

Round 1 matched fields. Round 2 reads paragraphs, for the one requirement the grid proved
nobody covered. Firm B's agent went looking only because it was told about a hole in
**somebody else's** coverage.

</div>

<!--
The beat. Hold here for as long as the question takes.

Slide 4 already gave away that Firm B holds the person, deliberately - a judge who is still
confused about that cannot hear this slide. So the beat here is not "Firm B has it", it is
that *nobody told Firm B where to look*. The coordinator does not know which firm has the
hole, and Firm B's agent re-read its own bios on the strength of two bytes about somebody
else's coverage. Say that, not the result.

If they ask why round 1 does not read everything: cost. `agents/search.py` is a cheap
structured predicate over six requirements; reading every paragraph against every requirement
is the expensive half, and the joint grid is what licenses spending it on exactly one.

The line the log actually prints:
  firm B  R4 <- FIRM_B::PERSON::007 - prose details seismic base isolation
          and strengthening on an acute care wing upgrade

Two bytes is the literal payload: the string "R4". Not which firm has the hole, not what would
fill it. The model reads Firm B's bios on Firm B's node; the sentence it reasons over never
leaves. In the trace this is one field: round 1 broadcasts `reads_text: false`, round 2
broadcasts `reads_text: true`.
-->

---
layout: center
class: text-left
---

# What crossed the wire

<div class="grid grid-cols-4 gap-4 mt-6 text-center">
<div><div class="num">2</div><div class="numlabel">rounds to converge</div></div>
<div><div class="num">2 B</div><div class="numlabel">the gap, broadcast back</div></div>
<div><div class="num">≈33 kB</div><div class="numlabel">banded answers, forward</div></div>
<div><div class="num text-green-600">0 B</div><div class="numlabel">record content, either way</div></div>
</div>

<div class="cap mt-8">

Zero is structural: the message format has no field that can carry a record. Nothing is
disclosed until a human releases a handle.

</div>

<div v-click class="cap mt-4">

Model answers are cached on disk, so a rehearsed run replays exactly and a dead endpoint costs
nothing. Two invariant tests guard the vocabulary and the engineered gap.

</div>

<!--
Technical execution axis. Every number here was read off a real run: round 1 attests 19, 13
and 18; the round-2 broadcast carries gap_bytes 2; record_bytes 0; converged after 2 rounds.

The banded total is approximate on purpose. It drifts a few hundred bytes between runs because
each attestation carries the round-1 grader's note, and that text is a sampled completion -
33191 B on one run, 33807 B on the next, which the page prints as 32.4 and 33.0 kB. Quote "about
33 kB" and let the pane show the exact figure; do not read a decimal off this slide.

If a judge wants to see it again, press Run.
-->

---
layout: center
class: text-left
---

# Safety by construction

<div class="grid grid-cols-2 gap-4 mt-4">

<div class="tile"><b>A fixed vocabulary on the way out</b>
Exact fees and dates become ranges before anything leaves the node.</div>

<div class="tile"><b>Reject, never scrub</b>
An unknown field is an error. A filter that quietly deletes teaches an agent that leaky output
is fine.</div>

<div class="tile"><b>Reading stays home</b>
The model reads a firm's own paragraphs on the firm's own node.</div>

<div class="tile"><b>A refusal cannot be walked around</b>
Blocked records never enter the candidate set, so nothing downstream can pick one.</div>

</div>

<div v-click class="cap mt-5">

No firm can assert anything about another firm. And the coordinator can prove the team
qualifies, or does not, **before a single record is disclosed**.

</div>

<!--
A scored axis, not a compliance chore: the organisers weight transparency, reliability and
supervision, and say agent performance is not the deciding factor. So raise it deliberately.

Do not offer a rejection count or an approval count. Nothing counts them, and the human gate
is roadmap.
-->

---
layout: center
class: text-left
---

# One protocol, three wires

<div class="grid grid-cols-3 gap-4 mt-5">
<div class="tile"><b><code>LocalGrid</code></b>The published <b style="display:inline">AgentApp</b>, in process. What a judge gets from <code>flwr chat</code>.</div>
<div class="tile"><b><code>InMemoryGrid</code></b>Simulation runtime. Three SuperNodes, real per-node data isolation. The table demo.</div>
<div class="tile"><b><code>GrpcGrid</code></b>A real SuperLink. Same <code>send_and_receive</code>, same <code>Message(QUERY)</code>.</div>
</div>

<div class="cap mt-6">

No code changes between them, and the demo's log names which one is carrying the messages.
A node knows whether it is simulated or real from its own `node_config`, and no coordinator
gets to redirect that.

</div>

<div class="cap mt-4">

Published: **`flower.ai/apps/i53n1/consortium`** &nbsp;·&nbsp; `flwr chat` → `@i53n1/consortium`

</div>

<!--
Use of Flower axis. The honest answer to "does it really run on SuperGrid": it is published
and invokable. We drive the table demo locally because 130 people share the wifi, not because
the deployment path is a mock.

Every model call goes through agent.responses.create, the Open Responses shape.
-->

---
layout: center
class: text-left
---

# The form is the example. The harness is the product.

<div class="grid grid-cols-2 gap-4 mt-4">

<div class="tile"><b><span class="float-right">Firm B</span>Hospital in an earthquake zone</b>
A hospital wing filed as civic work</div>

<div class="tile"><b><span class="float-right">Firm C</span>Transit station and tunnel</b>
A bore under a live platform, billed as a relief conduit</div>

<div class="tile"><b><span class="float-right">Firm A</span>Secure research laboratory</b>
A containment suite booked to the client who paid for it</div>

<div class="tile"><b><span class="float-right">Firm B</span>Campus energy retrofit</b>
An energy centre bought by the city, serving the university</div>

</div>

<div v-click class="cap mt-5">

Same protocol, same code, no per-scenario branches. The hidden row moves, and the harness does
not know where. Swap the three pluggable pieces and the loop runs for hospitals sizing a trial
cohort without sharing patients, or banks checking one name against each other's alerts.

</div>

<!--
Innovation and Impact together. This is the slide that turns "an app" into "a harness".

At the table, use the live scenario selector instead - it costs eight seconds and lands harder
than the tiles do.
-->

---
layout: center
class: text-left
---

# Roadmap

<div class="grid grid-cols-2 gap-4 mt-5">

<div class="tile" style="border-left: 4px solid #60a5fa">
<b>1 · Disclose as little as possible</b>
Clear every requirement at the lowest total disclosure cost.</div>

<div class="tile" style="border-left: 4px solid #60a5fa">
<b>2 · A named human approves each record</b>
A refusal makes the plan find the next-cheapest substitute.</div>

<div class="tile" style="border-left: 4px solid #9ca3af">
<b>3 · Measure it against a central pool</b>
Match what one pooled database finds, at a fraction of the disclosure.</div>

<div class="tile" style="border-left: 4px solid #22c55e">
<b>4 · Learn from who actually wins</b>
A shared win-rate model over past bids, with no bid history exposed.</div>

</div>

<!--
Items 1-3 are today's cut list, in order.

1 is greedy weighted set cover, inside the form's limit of ten example projects: deterministic
and explainable. 2 routes each request to a named owner at the firm that holds the record, and
the refusal is honoured rather than routed around. 3 is the claim to try to break.

Item 4 is the one to say out loud if there is time for exactly one: every finished bid is a
labelled example of which evidence won, so firms can federate a win-rate prior over
requirement-to-evidence matching. Federated learning in a market where nobody will ever pool
the data. That is why the harness is worth more than the demo.
-->

---
layout: center
class: text-center
---

# The form is the example. The harness is the product.

<div class="mt-8 text-xl opacity-85">
ask &nbsp;→&nbsp; find what nobody covers &nbsp;→&nbsp; re-read locally against it &nbsp;→&nbsp; release the least you can
</div>

<div class="mt-12 text-lg">
A protocol for agents that are not allowed to pool their data.
</div>

<div class="mt-14 text-sm opacity-50">
<code>@i53n1/consortium</code> &nbsp;·&nbsp; Apache-2.0 &nbsp;·&nbsp; Track 1 — SuperGrid
</div>

<!--
Stop talking. Four minutes of a five-minute slot, and the questions are where the marks are.
-->

---
layout: center
class: text-left
---

# Appendix — the six axes

<div class="text-xs">

| Axis | What evidences it | Slide |
|---|---|---|
| **Impact** | Teams of firms bid public work by emailing spreadsheets; this is the missing primitive | 2, 12 |
| **Innovation** | Broadcast the *gap*, not the answer, so an agent answers a question it could not ask | 5, 7 |
| **Use of Flower** | Real `AgentApp` on Hub; one protocol over three `Grid`s; runtime chosen by `node_config` | 10 |
| **Technical execution** | Runs end to end, converges in 2 rounds, four scenarios, replays offline, invariant tests | 8 |
| **Demo and delivery** | Split screen: the protocol's own log beside a live picture of the same run | live |
| **Safety and oversight** | Fixed egress vocabulary, reject-not-scrub, reading stays on the node, 0 B by construction | 9 |

</div>

<div class="cap mt-4">

**Not claimed:** a disclosure count, a denial, a live substitution, an assembled form, a human
approval gate, a rejection count, or the central-pool baseline. Those are slide 12, and saying
so is why the rest holds up under a follow-up question.

</div>

<!--
Not presented. This is for the rehearsal, and for the judge who asks how we score ourselves -
which happens more often than you would think.
-->
