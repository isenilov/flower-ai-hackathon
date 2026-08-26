# The event — logistics, access, and links

Everything from the organisers' post, so nobody re-reads it on the day:
<https://discuss.flower.ai/t/collaborative-agent-hackathon-cambridge-uk-2026/1269>

Fetched 26 Aug 2026. Where the post is silent, this says so rather than guessing — the
gaps are as load-bearing as the facts. The brief owns what we build and when; this owns
what the organisers said.

---

## Where and when

**Wednesday 26 August 2026, 09:30–19:00.**
LT1 & LT2, William Gates Building, University of Cambridge, 15 JJ Thomson Avenue,
Cambridge CB3 0FD.

| Time | Event |
|---|---|
| 09:30 | Registration, light breakfast |
| 10:00 | Welcome and introduction |
| 10:15 | Technical talk — collaborative agents with Flower |
| 10:45 | Team formation |
| 11:00 | **Build session begins** |
| 12:45 | Lunch and mentor office hours |
| 13:30 | Build session resumes |
| 17:15 | Demo preparation |
| 17:30 | **Demos — 3–5 minutes per team**, then judges' questions |
| 18:45 | Awards and closing |
| 19:00 | Ends |

Bring a laptop, charger, and your own adapters. Extension cords are provided but
"supplies may be limited".

---

## Our track: **Track 1 — SuperGrid**

> **Track 1: SuperGrid** — "Using the existing SuperGrid infrastructure, your goal is to
> showcase the collaborative aspect of Flower Agents running on SuperGrid."

Selected and settled. Write **Track 1: SuperGrid** on the submission form — the brief calls
the same thing a "Flower Agent Harness", which is our framing, not a name the organisers
use anywhere.

The other option, for context only: *Track 2: Infrastructure* — "Build a new
collaborative-agent use case by adapting or extending the existing infrastructure. You have
more flexibility to define the problem and the solution."

Track 1 is the tighter brief of the two, and it puts SuperGrid on the critical path rather
than in the nice-to-have column: our app has to actually run there, not merely be
publishable. Brief §0.1 already treats the Hub publish as a pass/fail gate.

**Both tracks carry the same bar:** *"For both tracks, prepare a working `AgentApp` and a
demo of no more than 3–5 minutes."* An `AgentApp` is not optional on either track.

---

## Setup, before anything else

- Flower account — <https://flower.ai/>
- `uv` — <https://docs.astral.sh/uv/>
- Flower Slack — <https://flower.ai/join-slack>, then join **`#hackathon_cambridge_2026`**

The Slack channel is not optional infrastructure: **the shared model API keys are posted
there and nowhere else.** It is also where mentors answer and where feedback goes.

### Documentation the organisers flag as required reading

| Topic | URL |
|---|---|
| Flower Agent docs (index) | <https://flower.ai/docs/agent/> |
| SuperGrid quickstart | <https://flower.ai/docs/agent/tutorials/quickstart.html> |
| Flower Chat in the terminal | <https://flower.ai/docs/agent/tutorials/get-started-with-flower-agent.html> |
| Write your first AgentApp | <https://flower.ai/docs/agent/tutorials/write-your-first-agentapp.html> |
| Run on SuperGrid | <https://flower.ai/docs/agent/how-to-guides/run-on-supergrid.html> |
| Run with a local SuperLink | <https://flower.ai/docs/agent/how-to-guides/run-with-local-superlink.html> |
| Connectors | <https://flower.ai/docs/agent/explanations/use-connectors.html> |
| Ollama / custom endpoints | <https://flower.ai/docs/agent/how-to-guides/run-with-ollama.html> |

### Example recipes to start from

- Collaborative AgentApp — <https://flower.ai/apps/flwrlabs/hackathon-collab-agent-recipe>
- Ollama AgentApp — <https://flower.ai/apps/flwrlabs/hackathon-ollama-agent-recipe>

---

## Shared model endpoints

Hosted by AMD, OpenAI-compatible, exposed as `/v1/responses`. Plain `http`, raw IPs — as
published.

| Model | Endpoint | Model ID | Key |
|---|---|---|---|
| Qwen3.5 397B | `http://129.212.182.232:8001/v1/responses` | `/models/Qwen3.5-397B-A17B-FP8` | **none — unset the variable** |
| Kimi-K2.7-Code | `http://134.199.193.245:8001/v1/responses` | `/models/Kimi-K2.7-Code` | from Slack |
| GLM-5.2 | `http://129.212.179.194:8001/v1/responses` | `glm-5.2-fp8` | from Slack |
| MiniMax-M3 | `http://165.245.135.52:8001/v1/responses` | `minimax-m3` | from Slack |

```bash
export FLWR_MODEL_API_ENDPOINT='<endpoint from the table>'
export FLWR_MODEL_API_KEY='<key from Slack>'
uv run flower-superlink --insecure
```

Two things that will cost someone twenty minutes otherwise:

- **Qwen takes no key.** Run `unset FLWR_MODEL_API_KEY` or the call fails.
- **Restart `flower-superlink` after switching models.** The endpoint is read at start-up,
  so an exported variable alone changes nothing.

Calls go through the Responses API:

```python
agent.responses.create({"model": MODEL_ID, "input": prompt, "stream": True})
```

### The constraint that shapes our design

> "Each task has a 5-minute timeout, starting from when the task switches to the
> `Running` status."

Five minutes per task on SuperGrid, wall-clock. A full round that fans out across three
firm nodes and calls a model per shortlisted record has to fit inside that — which is why
the brief prefilters on banded fields and only invokes the model on the shortlist.

Credits: *"We will ensure that you have sufficient credits to run your `AgentApp`s on
SuperGrid throughout the duration of the hackathon."* Rate limits and contention are not
mentioned, so treat ~130 attendees on shared endpoints as an unpriced risk and cache
responses during development.

---

## Submission

Submitted **before the demos** — the post gives no clock time, so treat 17:15 as the real
deadline and the brief's 16:30 final publish as the one that matters.

- Team name, members, and email addresses
- Selected track — **Track 1: SuperGrid**
- Short project description
- **Published Flower Hub app**
- **GitHub repository link**

The last two are the pass/fail gates. Brief §0.1 owns them and §10 is the publishing
runbook.

### Judging — six axes

| Axis | As the organisers put it |
|---|---|
| Impact | Solution value and usefulness |
| Innovation | Originality of approach |
| Use of Flower | Effectiveness of Flower Agent / SuperGrid integration |
| Technical execution | Functionality and code quality |
| Demo and delivery | Clarity and presentation |
| Safety and oversight | Transparency, reliability, appropriate supervision |

> "Agent performance may inform the assessment, but it is not the sole or decisive factor."

Worth reading twice: a rough-edged agent with a clear, well-supervised story scores better
than a slick one with no oversight. Brief §0.2 maps each axis to the artefact that
evidences it.

---

## Teams, prizes, partners

Recommended **2–4 people** with complementary skills. Solo is allowed; collaboration is
encouraged.

Prize pool **£1,500** — a Bambu Lab P1S 3D printer, Bose QuietComfort Ultra headphones,
Amazon Echo devices, and Flower Labs / ARM swag. Partners: ARM, AMD, Amazon.

Mentors are available all day, in person and in the Slack channel.

---

## What the post does not say

Do not infer these from this document:

- **No Python version requirement.** We chose ≥ 3.13; that is ours, not theirs.
- **No `flwr` version requirement.** We pin `flwr[simulation]>=1.34.0` because that is
  what we verified against.
- **No clock time for the submission deadline** — only "before the demos".
- **Nothing about rate limits** on the shared endpoints, only that credits are sufficient.
