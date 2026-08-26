"""Round-1 matcher: search the local library, score matches, emit attestations.

``agents.search`` decides which records a requirement's declared fields admit. This module
asks the model the one question those fields cannot answer: does the record's own prose bear
its filing out? The answer rides out as ``match_strength`` and a note on each attestation.

**It grades; it never re-decides.** ``data/ground_truth.json`` carries two oracles —
``round_one_coverage``, the declared reading, and ``coverage``, the reading that includes
free text. They differ on exactly one requirement, and that difference is the demo. So a
round-1 call that could *add* a record would close the gap a round early, and one that could
*drop* a record would put the harness below the oracle it is scored against, on the strength
of a sampled completion. Both are refused in code and not merely discouraged in the prompt:
handles the model was not shown are discarded, and the two grades map to strengths that both
clear the optimiser's tau. The coverage matrix is the same matrix with or without a model.

**One call per firm.** The whole matrix goes in a single request — six requirements and their
shortlists — because the cost that matters here is round trips, not tokens. Per requirement
it was eighteen calls a run and two minutes a firm on a cold cache; this is three calls a run
and one wait. It also gives a firm exactly one cache entry per scenario, so a rehearsed run
replays instantly instead of partially.

**The model's sentence stays on the node.** It is prose derived from a bio, and the claim
this harness makes is that no record content crosses before authorisation. What travels is a
float and requirement-side field names; the clause goes to the local log. ``agents.reexamine``
draws the same line in round 2.
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from logging import DEBUG, WARNING
from pathlib import Path

from flwr.common.logger import log

from agents import model, search
from backend import ansi
from backend.schema import Requirement

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "round1_match.md"

# Everything after this heading in the prompt file is the model's `instructions`, so the
# prompt is editable without touching Python — which is the point of keeping it in prompts/.
_INSTRUCTIONS_MARKER = "## instructions"

# How long a round may wait for its grades. Deliberately well below `model.DEFAULT_TIMEOUT`,
# which is sized for round 2: round 2 is the beat and the call allowed to take its time, and
# a grade is not worth a missed round. Whatever has not landed by here is left to finish into
# the cache, so the next run of this scenario gets it for nothing.
GRADING_BUDGET = 120.0

# Generous because Qwen3.5 spends most of its budget reasoning and emits the answer last — the
# same finding that sized round 2's ceiling. The answer itself is a word and a clause per
# record; it is the thinking in front of it that needs the room.
MAX_OUTPUT_TOKENS = 16384

# `corroborated` keeps the declared strength; `thin` marks a filing its own prose does not
# bear out. Both sit above the optimiser's default tau of 0.6 — see the module docstring:
# grading is not overruling, and dropping a declared match out of the disclosure set on a
# sampled completion is not round 1's call to make.
STRENGTH = {"corroborated": 1.0, "thin": 0.7}


@dataclass(frozen=True)
class Grade:
    """What round 1 says about one (requirement, record) pair on the wire."""

    strength: float
    note: str = ""


# What an ungraded pair gets: the declared match at full strength, nothing added. Every
# failure path in this module lands here, so a model that is slow, absent, or talking
# nonsense costs the harness its annotations and nothing else.
DECLARED = Grade(strength=1.0, note="")

Shortlists = list[tuple[Requirement, list[search.Candidate]]]


def instructions() -> str:
    """Read the round-1 instructions out of the prompt file."""
    text = PROMPT_PATH.read_text()
    _, _, body = text.partition(_INSTRUCTIONS_MARKER)
    return body.strip() or text.strip()


def _terms(requirement: Requirement) -> str:
    """The predicate's field names — requirement-side vocabulary, safe to put on the wire."""
    return ", ".join(sorted(key for key in requirement.predicate if key != "join"))


def _payload(shortlists: Shortlists) -> str:
    """Render every shortlist for the model. Stays inside the node.

    Lean on purpose. The model is being asked one question per record, and every extra
    sentence is more for a reasoning model to chew through before it answers it.
    """
    blocks = []
    for requirement, candidates in shortlists:
        terms = "; ".join(
            f"{key} = {value}" for key, value in requirement.predicate.items() if key != "join"
        )
        lines = [
            f"## {requirement.id} — SF330 section {requirement.section}, "
            f"{requirement.kind.lower()}: {requirement.description}",
            f"Every term must hold: {terms}",
            "",
            "Records already matching on filed fields:",
        ]
        for candidate in candidates:
            filed = ", ".join(f"{key}={value}" for key, value in sorted(candidate.banded.items()))
            lines.append(f"\n- {candidate.handle}")
            lines.append(f"  filed as: {filed}")
            lines.append(f"  description: {candidate.prose or '(no description on file)'}")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)


def _read(answer: model.JSONObject, shortlists: Shortlists) -> dict[tuple[str, str], Grade]:
    """Turn the model's verdicts into grades, discarding anything it was not asked about."""
    verdicts = answer.get("verdicts")
    if not isinstance(verdicts, dict):
        log(WARNING, "round-1 grading returned no verdicts object")
        return {}

    graded: dict[tuple[str, str], Grade] = {}
    for requirement, candidates in shortlists:
        for_requirement = verdicts.get(requirement.id)
        if not isinstance(for_requirement, dict):
            continue

        known = {candidate.handle for candidate in candidates}
        terms = _terms(requirement)
        for handle, verdict in for_requirement.items():
            # A handle the model was not shown is not a grade of anything, and neither is a
            # handle under the wrong requirement. This is the code half of "it may not
            # nominate" — the prompt asks for it, this is what enforces it.
            if handle not in known or not isinstance(verdict, dict):
                continue
            label = str(verdict.get("grade", "")).strip().lower()
            if label not in STRENGTH:
                continue

            # The clause is derived from a bio, so it goes to the log and not to the wire.
            log(
                DEBUG,
                "[round 1] %s %s for %s: %s",
                handle,
                label,
                requirement.id,
                verdict.get("why"),
            )
            note = (
                f"prose corroborates: {terms}"
                if label == "corroborated"
                else f"filed only; prose thin on: {terms}"
            )
            graded[(requirement.id, handle)] = Grade(strength=STRENGTH[label], note=note)

    return graded


def _firm_of(shortlists: Shortlists) -> str:
    """The firm being graded, read off a handle rather than threaded through the call."""
    for _, candidates in shortlists:
        if candidates:
            return str(candidates[0].handle).split("::", 1)[0]
    return "UNKNOWN"


def _model_name(model_id: str) -> str:
    """The model id without its path, which is all a terminal column has room for."""
    return model_id.rsplit("/", 1)[-1] or model_id


def _call(
    shortlists: Shortlists, reader: model.Reader, model_id: str
) -> dict[tuple[str, str], Grade]:
    """Ask for the whole matrix at once. Returns ``{}`` rather than raising, ever."""
    who = _firm_of(shortlists)
    pairs = sum(len(candidates) for _, candidates in shortlists)
    request = {
        "model": model_id,
        "instructions": instructions(),
        "input": _payload(shortlists),
        "max_output_tokens": MAX_OUTPUT_TOKENS,
    }
    # Asked of the cache before the call, so a replay is reported as a replay rather than as
    # a suspiciously fast model. Same reading round 2 takes.
    replay = bool(getattr(reader, "cached", None) and reader.cached(request))  # type: ignore[attr-defined]

    ansi.say(
        ansi.node_line(
            who,
            f"round 1 - grading {pairs} declared matches with {_model_name(model_id)}",
        )
    )

    started = time.monotonic()
    try:
        response = reader(request)
        grades = _read(model.extract_json(response), shortlists)
    except (LookupError, ValueError, OSError, json.JSONDecodeError) as exc:
        # Say so. A silent degrade to declared-only looks exactly like a model that agreed
        # with every filing, and those two readings of the matrix are not the same claim.
        ansi.say(ansi.node_line(who, f"round 1 - grading unavailable: {exc}", ansi.GAP))
        log(WARNING, "round-1 grading unavailable: %s", exc)
        return {}

    took = ansi.took(time.monotonic() - started, replay)
    thin = sum(1 for grade in grades.values() if grade.strength < STRENGTH["corroborated"])
    ansi.say(
        ansi.node_line(
            who,
            f"round 1 - {len(grades)} graded, {thin} filed thinner than the prose ({took})",
            ansi.DIM,
        )
    )
    return grades


def grade(
    shortlists: Shortlists,
    reader: model.Reader | None,
    model_id: str,
) -> dict[tuple[str, str], Grade]:
    """Grade every shortlisted pair this firm is about to attest to.

    Keyed by ``(requirement_id, handle)``. A pair missing from the result is one the caller
    should emit as :data:`DECLARED` — that is the whole degrade path, and it is why this
    returns a mapping rather than mutating anything.
    """
    if reader is None or not model_id:
        return {}

    # Only requirements with something to read. A shortlist whose records carry no prose has
    # no question in it, and including it spends tokens to be told so.
    work = [
        (requirement, candidates)
        for requirement, candidates in shortlists
        if any(candidate.prose for candidate in candidates)
    ]
    if not work:
        return {}

    # A thread purely as a timeout: the reader may be `agent.responses.create`, whose own
    # timeout this module does not get to set, and a round must not be able to hang on a
    # grade. Not cancelled on the way out — an in-flight call is left to finish into the
    # on-disk cache, so the next run gets the grade this one waited too long for.
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(_call, work, reader, model_id)
        done, _ = wait([future], timeout=GRADING_BUDGET)
        if not done:
            ansi.say(
                ansi.node_line(
                    _firm_of(work),
                    f"round 1 - grading gave up after {GRADING_BUDGET:.0f}s, "
                    f"attesting the declared reading",
                    ansi.GAP,
                )
            )
            log(WARNING, "round-1 grading did not land inside %.0fs", GRADING_BUDGET)
            return {}
        try:
            return future.result()
        except Exception as exc:  # noqa: BLE001 - a grade must never fail a round
            log(WARNING, "round-1 grading abandoned: %s", exc)
            return {}
    finally:
        pool.shutdown(wait=False)
