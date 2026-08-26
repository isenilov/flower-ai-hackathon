"""Round-2 gap-directed re-query.

Local recompute informed by global state, iterated over rounds — the same primitive as
federated learning. The coordinator broadcasts the uncovered requirement; the agent asks
its own library a question round 1 gave it no reason to ask.

Round 1 can only match what a record *declares*. A person's sectors are the sectors of the
projects they are booked to, because that is where a firm's sectors have always come from.
The Section G cell hides in exactly that gap: Firm B's holder is booked to work filed as
civic, so no structured search reaches them, and only their bio says the building was a
hospital.

So round 2 reads prose, and it reads it with a model. It does **not** get a keyword list:
``data/scenarios.json`` carries a lexicon, but that is the oracle ``generate.py`` uses to
prove the cell is findable, and handing it to a node would be handing it the answer key.
The node is told the requirement it failed to cover — never the answer, never which of its
records to look at.
"""

import json
import sys
import time
from logging import INFO, WARNING
from pathlib import Path
from typing import Any

from flwr.common.logger import log

from agents import model, search
from backend import ansi
from backend.schema import Requirement

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "round2_reexamine.md"

# Measured against the shared Qwen3.5 endpoint: it spends most of its budget reasoning and
# emits the answer last, so a cap that looks generous is the difference between a result and
# `status=incomplete` with nothing but a scratchpad in it. 4096 and 8192 both returned empty.
# Passing `reasoning: {"effort": ...}` made it slower, not terser.
MAX_OUTPUT_TOKENS = 16384

# Everything after this heading in the prompt file is the model's `instructions`, so the
# prompt is editable without touching Python — which is the point of keeping it in prompts/.
_INSTRUCTIONS_MARKER = "## instructions"


def instructions() -> str:
    """Read the round-2 instructions out of the prompt file."""
    text = PROMPT_PATH.read_text()
    _, _, body = text.partition(_INSTRUCTIONS_MARKER)
    return body.strip() or text.strip()


def _describe(requirement: Requirement) -> str:
    """State the gap as a requirement, with its predicate spelled out but not resolved."""
    terms = [f"{key} = {value}" for key, value in requirement.predicate.items() if key != "join"]
    lines = [
        f"Requirement {requirement.id} (SF330 section {requirement.section}, "
        f"{requirement.kind.lower()}): {requirement.description}",
        f"Every term must hold: {'; '.join(terms)}",
    ]
    if requirement.predicate.get("join") == "person_x_project":
        lines.append(
            "This is a Section G cell: one named person on one named project, both yours. "
            "A person who has done each half on different jobs does not satisfy it."
        )
    return "\n".join(lines)


def _candidates(library: dict[str, Any], requirement: Requirement) -> list[dict[str, Any]]:
    """The records worth re-reading: eligible for the requirement, and carrying prose.

    Eligibility — the right half of the library, blocked records excluded — belongs to
    ``agents.search``, so the two rounds cannot drift on what a node is allowed to look at.
    Cost-3 records are out here exactly as in round 1: a refusal that a second look could
    route around would not be a refusal.
    """
    return [
        record
        for record in search.eligible(library, requirement)
        if str(record.get("bio") or record.get("narrative") or "").strip()
    ]


def _payload(
    library: dict[str, Any], requirement: Requirement, records: list[dict[str, Any]]
) -> str:
    """Render the local records for the model. Stays inside the node.

    Deliberately lean. Every extra sentence is more for a reasoning model to chew through,
    and the shared endpoint answered a fuller version of this prompt in ~240s — most of
    SuperGrid's per-task budget. So a person gets their own prose and the *declared* sectors
    of their work, not the full text of every project they touched: the prose is where a
    hidden cell can live, and the Section G join is a structural fact checked in code.
    """
    declared = {p["handle"]: p for p in library.get("projects", [])}
    lines = [_describe(requirement), "", "Your records:"]

    for record in records:
        prose = record.get("bio") or record.get("narrative") or ""
        lines.append(f"\n- {record['handle']}")
        if "role" in record:
            credentials = ", ".join(record.get("credentials", [])) or "none"
            lines.append(f"  role: {record['role']}; credentials: {credentials}")
            sectors = sorted(
                {declared[h]["sector"] for h in record.get("projects", []) if h in declared}
            )
            if sectors:
                lines.append(f"  their projects are filed as: {', '.join(sectors)}")
        else:
            lines.append(
                f"  filed as {record.get('sector')}, {record.get('delivery')}, "
                f"{record.get('client_type')} client"
            )
        lines.append(f"  description: {prose}")

    return "\n".join(lines)


def reexamine(
    library: dict[str, Any],
    requirement: Requirement,
    reader: model.Reader,
    model_id: str,
) -> dict[str, str]:
    """Re-read this firm's own prose against one uncovered requirement.

    Returns ``{handle: why}`` for records the agent judges to satisfy it. Returns empty on
    any failure — a model that is slow, absent, or talking nonsense must cost the harness a
    closed gap, not a crashed run.
    """
    records = _candidates(library, requirement)
    if not records:
        return {}

    # Ray forwards a SuperNode's stdout to the driver with the actor's pid attached, so these
    # lines land in the demo's terminal pane already labelled by node. That is the whole
    # reason to log here rather than at the coordinator: it is visible proof that the prose
    # was read on the firm's own node, and that only a verdict left it.
    who = _firm_of(records)
    model_name = model_id.rsplit("/", 1)[-1] or model_id
    _say(
        _node_line(
            who, f"gap {requirement.id} - re-reading {len(records)} records with {model_name}"
        )
    )

    request: dict[str, Any] = {
        "model": model_id,
        "instructions": instructions(),
        "input": _payload(library, requirement, records),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
    # Asked before the call, not inferred from how long it took. A rehearsal runs entirely
    # off the cache, and "0ms" with no explanation reads as a model that was never asked.
    replay = bool(getattr(reader, "cached", None) and reader.cached(request))  # type: ignore[attr-defined]

    started = time.monotonic()
    try:
        response = reader(request)
        answer = model.extract_json(response)
    except (LookupError, ValueError, OSError, json.JSONDecodeError) as exc:
        # A slow, absent, or rambling model must cost the harness a closed gap, not a
        # crashed run — but say so, or a silent miss looks like a correct empty answer.
        log(WARNING, "round-2 re-examination unavailable for %s: %s", requirement.id, exc)
        return {}
    elapsed = time.monotonic() - started

    known = {record["handle"] for record in records}
    why = answer.get("why") if isinstance(answer.get("why"), dict) else {}
    # Only handles the model was actually shown. A hallucinated handle is not evidence.
    found = {
        handle: str(why.get(handle, "re-examined against the broadcast gap"))
        for handle in answer.get("handles", [])
        if isinstance(handle, str) and handle in known
    }

    if not found:
        _say(
            _node_line(
                who,
                f"{requirement.id} - nothing here evidences it ({_took(elapsed, replay)})",
                ansi.DIM,
            )
        )
    for handle, reason in found.items():
        _say(
            _node_line(
                who, f"{requirement.id} <- {handle} - {reason} ({_took(elapsed, replay)})", ansi.OK
            )
        )
    return found


def _say(line: str) -> None:
    """Log from inside a SuperNode, and flush so the line arrives while it is still true.

    A ClientAppActor's stderr is a pipe, not a terminal, so Python block-buffers it and Ray
    forwards nothing until the actor is torn down — which puts "firm B found it" on screen
    *after* the verdict. Flushing is what makes the node-side beat land in its own round.
    """
    log(INFO, "%s", line)
    sys.stderr.flush()
    sys.stdout.flush()


def _took(seconds: float, replay: bool) -> str:
    """How long the model took, or that it was never asked because the answer was on disk."""
    if replay:
        return "from cache"
    return f"{seconds * 1000:.0f}ms" if seconds < 1 else f"{seconds:.1f}s"


def _firm_of(records: list[dict[str, Any]]) -> str:
    """The firm these records belong to, read off a handle rather than passed in."""
    return str(records[0]["handle"]).split("::", 1)[0]


def _node_line(firm: str, detail: str, tone: tuple[int, int, int] | None = None) -> str:
    """A node-side line in the same columns and lane colour the coordinator's log uses."""
    name = firm.replace("FIRM_", "firm ")
    return ansi.paint(f"{name:<9}", ansi.firm_tone(firm), bold=True) + ansi.paint(detail, tone)
