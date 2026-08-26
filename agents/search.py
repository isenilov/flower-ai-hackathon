"""Structured predicate prefilter over a firm's local library.

Runs before any model call: banded fields are matched exactly here so the model is only
ever asked about free-text bios on the shortlist.

Both rounds start here. Round 1 grades what the prefilter admits; round 2 re-reads what it
turned down. The exclusions they share — the wrong half of the library for the section, and
blocked records — live here once instead of drifting apart in two modules.

Nothing here calls a model. This is the module that decides *what to ask about*, and it is
why the call count is one per requirement rather than one per record: six calls a firm, not
ninety. Banding and predicate semantics are injected rather than imported — they belong to
the wire schema in ``backend``, and a firm's agent has no business redefining either.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from backend.schema import Requirement

Bander = Callable[[dict[str, Any]], dict[str, str]]
Admits = Callable[[dict[str, str], dict[str, str]], bool]

# `disclosure_cost` 3 means blocked. Excluded before any matching in both rounds: a refusal
# that a second look could route around would not be a refusal.
BLOCKED_COST = 3


@dataclass(frozen=True)
class Candidate:
    """One local record, with the banded view of it the predicate was tested against."""

    record: dict[str, Any]
    banded: dict[str, str]
    links: list[str]

    @property
    def handle(self) -> str:
        """The firm-local opaque id — the only part of a record that ever travels."""
        return str(self.record["handle"])

    @property
    def is_person(self) -> bool:
        """People carry a bio or a project list; projects carry neither."""
        return "bio" in self.record or "projects" in self.record

    @property
    def prose(self) -> str:
        """The free text a model could read, or ``''`` for a record with none."""
        return str(self.record.get("bio") or self.record.get("narrative") or "").strip()


def group(requirement: Requirement) -> str:
    """Which half of the library a requirement's section is about."""
    return "people" if requirement.section in ("E", "G") else "projects"


def eligible(library: dict[str, Any], requirement: Requirement) -> list[dict[str, Any]]:
    """Records the requirement could speak to at all: right group, not blocked."""
    return [
        record
        for record in library.get(group(requirement), [])
        if int(record.get("disclosure_cost", 0)) < BLOCKED_COST
    ]


def shortlist(
    library: dict[str, Any],
    requirement: Requirement,
    firm: str,
    banded_of: Bander,
    admits: Admits,
) -> list[Candidate]:
    """The declared matches for one requirement — round 1's whole candidate set.

    Declared fields only. A predicate key with no banded source fails, and that is the round
    boundary: the Section G cell survives round 1 because the filing says civic and only the
    bio says hospital. Reading the bio is ``agents.reexamine``'s job, not this one.
    """
    wants_join = requirement.predicate.get("join") == "person_x_project"
    found: list[Candidate] = []

    for record in eligible(library, requirement):
        banded = banded_of(record)
        if not admits(requirement.predicate, banded):
            continue
        links = [h for h in record.get("projects", []) if h.startswith(firm)]
        if wants_join and not links:
            # Section G needs the person-on-project join, not just the person.
            continue
        found.append(Candidate(record=record, banded=banded, links=links))

    return found
