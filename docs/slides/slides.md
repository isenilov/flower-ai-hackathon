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

The through-line to say here, and to land on again when the six slides run out: the bidding
form is the example, the harness is the product.
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

# What the database fields can prove

<div class="sub">each firm searches its own records on declared fields &nbsp;·&nbsp; the coordinator joins the answers</div>

<div class="fields">

<div></div>
<div class="hd">Firm A</div>
<div class="hd">Firm B</div>
<div class="hd">Firm C</div>
<div class="hd team">The team</div>

<div class="rq"><span class="rid">R1</span><b>Three</b> hospital projects over $50m</div>
<div class="ok">✓</div><div class="no">✗</div><div class="ok">✓</div><div class="ok team">✓</div>

<div class="rq"><span class="rid">R2</span><b>Two</b> design-build jobs for a federal client</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div><div class="ok team">✓</div>

<div class="rq"><span class="rid">R3</span>A project manager with hospital work</div>
<div class="ok">✓</div><div class="no">✗</div><div class="no">✗</div><div class="ok team">✓</div>

<div class="rq hot"><span class="rid">R4</span>One person: hospital <i>and</i> earthquake retrofit</div>
<div class="maybe">?</div><div class="maybe">?</div><div class="maybe">?</div><div class="maybe team">?</div>

<div class="rq"><span class="rid">R5</span>A chartered structural lead</div>
<div class="no">✗</div><div class="ok">✓</div><div class="no">✗</div><div class="ok team">✓</div>

<div class="rq"><span class="rid">R6</span><b>Two</b> green-certified projects</div>
<div class="ok">✓</div><div class="ok">✓</div><div class="ok">✓</div><div class="ok team">✓</div>

</div>

<div class="legend">
<div><span class="ok">✓</span> the fields prove it</div>
<div><span class="no">✗</span> the fields rule it out</div>
<div><span class="maybe">?</span> the fields cannot say either way</div>
</div>

<div v-click class="cap mt-3">

No firm's column is complete. The team's is, bar one row — and that row the fields cannot answer
either way, so it goes down as an open gap. **An open gap is not the same as nobody having it.**

</div>


<!--
This is the design constraint, and the corpora are built backwards from it.

Two things to say, in this order. First: no column is complete, so none of them can bid this
alone - A has no chartered structural lead, B is a project short on hospital work and has no
credentialled PM, C has neither. Point at the last column: only together do they clear the form.

Second, and this is the one to slow down for: R4 is not a cross, it is a question mark. The five
settled rows are settled either way by the fields - the crosses are as provable as the ticks.
R4 is the row where a structured search returns nothing and that proves nothing, because the
answer is in prose. A judge who reads R4 as a cross will think the next slide contradicts this
one.

The row ids are the ones the log and the live page print, so R4 said here is R4 there.

The last column is derived, not reported: one firm's tick makes the team's tick, which is stage
2 of the loop two slides on. Verified off `data/ground_truth.json` - round 1 gives A 7/3 on R1
and 0 on R5, B 2/3 on R1 and 0 on R3, C 0 on R3 and R5, and R4 zero handles from anyone. The
oracle reading agrees on every row but R4, so the crosses survive reading every paragraph too.
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

<div class="text-xs opacity-55 mb-1">R4 again, same columns as the last slide &nbsp;·&nbsp; watch the last cell</div>

<div class="fields">
<div></div>
<div class="hd">Firm A</div>
<div class="hd">Firm B</div>
<div class="hd">Firm C</div>
<div class="hd team">The team</div>

<div class="rq">round 1 &nbsp;·&nbsp; matched on fields</div>
<div class="maybe">?</div><div class="maybe">?</div><div class="maybe">?</div><div class="maybe team">?</div>

<div class="rq">round 2 &nbsp;·&nbsp; read in the bios</div>
<div class="no">✗</div><div class="ok">✓</div><div class="no">✗</div><div class="ok team">✓</div>
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

Stage 3 is where the whole claim sits, and the number to have ready is two bytes: the string
"R4". Not which firm has the hole, not what would fill it. The coordinator does not know which
firm can close it, and Firm B's agent re-read its own bios on the strength of two bytes about
somebody else's coverage. The line the log prints:

  firm B  R4 <- FIRM_B::PERSON::007 - prose details seismic base isolation
          and strengthening on an acute care wing upgrade

Be straight about the dashed box. A judge who catches an overclaim stops believing the rest.
-->

