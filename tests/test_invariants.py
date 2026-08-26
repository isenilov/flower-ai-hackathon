"""Invariants guarding the schema/corpus contract the demo rests on.

Two things break this run without raising anything. The wire schema in ``backend.schema``
drifts away from the data files that feed it, or a corpus edit closes the engineered R4
gap. Either way the federation still completes — the coverage matrix just comes out wrong
on stage, in front of the room. These tests turn that into a red bar beforehand.

The schema-versus-data checks run now. The corpus and ground-truth checks skip while the
firm corpora are placeholders and go live unchanged, with no edit here, the moment the
Data owner commits real records (``data/README.md``).
"""

import json
from pathlib import Path
from typing import Any

import pytest

from backend.schema import SECTION_F_CAP, VOCABULARY, Requirement

DATA = Path(__file__).resolve().parents[1] / "data"
FIRMS = ("FIRM_A", "FIRM_B", "FIRM_C")

Corpus = dict[str, Any]


def _load(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text())


@pytest.fixture(scope="session")
def rfp() -> dict[str, Any]:
    return _load("rfp.json")


@pytest.fixture(scope="session")
def corpora() -> dict[str, Corpus]:
    """The three firm corpora, keyed by the firm their filename names.

    Skips the whole corpus suite while any firm is still a placeholder: the rules below
    are cross-firm invariants and cannot be judged on a partial set.
    """
    loaded = {firm: _load(f"{firm.lower()}.json") for firm in FIRMS}
    placeholders = [f for f, c in loaded.items() if not c["projects"] and not c["people"]]
    if placeholders:
        pytest.skip(
            f"corpora still placeholders ({', '.join(placeholders)}) — these rules go live "
            "when the Data owner commits records, see data/README.md"
        )
    return loaded


@pytest.fixture(scope="session")
def r4_coverage() -> list[str]:
    coverage = _load("ground_truth.json")["coverage"]
    if "R4" not in coverage:
        pytest.skip("ground_truth.json carries no R4 coverage yet — see data/README.md")
    return coverage["R4"]


def test_should_mirror_the_schema_vocabulary_on_disk() -> None:
    """The bander rejects any band outside ``VOCABULARY``.

    A value the corpora use but the schema does not know is dropped at egress, so the
    requirement it was evidence for reads as uncovered with nothing to explain why.
    """
    on_disk = {key: tuple(values) for key, values in _load("vocabulary.json").items()}

    assert on_disk == VOCABULARY, (
        "data/vocabulary.json and backend.schema.VOCABULARY have drifted; the bander "
        "silently strips whatever only one of them knows about"
    )


def test_should_decompose_the_solicitation_into_six_typed_requirements(
    rfp: dict[str, Any],
) -> None:
    """R1-R6 are the coverage matrix's rows and the optimiser's columns."""
    requirements = [Requirement(**entry) for entry in rfp["requirements"]]

    assert [r.id for r in requirements] == ["R1", "R2", "R3", "R4", "R5", "R6"]
    assert rfp["section_f_cap"] == SECTION_F_CAP, (
        "the cap the optimiser enforces is not the cap the solicitation states, so the "
        "assembled Section F is either short or non-compliant"
    )


def test_should_keep_r1_to_r4_mandatory(rfp: dict[str, Any]) -> None:
    """A MANDATORY requirement nobody covers is the red cell the demo opens on.

    Downgrade one to WEIGHTED and the matrix has no failure to show.
    """
    mandatory = {r["id"] for r in rfp["requirements"] if r["kind"] == "MANDATORY"}

    assert mandatory == {"R1", "R2", "R3", "R4"}


def test_should_state_r4_as_a_single_section_g_cell(rfp: dict[str, Any]) -> None:
    """R4 is one person against one project, not a count of either.

    Read as an aggregate it is satisfiable by any firm with healthcare work and seismic
    work separately — which is exactly the self-assessment the federated round refutes.
    """
    r4 = next(r for r in rfp["requirements"] if r["id"] == "R4")

    assert r4["section"] == "G"
    assert r4["min_count"] == 1


def test_should_prefix_every_handle_with_its_own_firm(corpora: dict[str, Corpus]) -> None:
    """A handle is the only identity a record keeps once banded.

    One that names another firm routes the coordinator's follow-up to a node that has
    never heard of the record, and the disclosure ledger credits the wrong firm.
    """
    foreign = [
        f"{firm}: {record['handle']}"
        for firm, corpus in corpora.items()
        for record in (*corpus["projects"], *corpus["people"])
        if not record["handle"].startswith(f"{firm}::")
    ]

    assert not foreign, f"handles that do not name the firm holding them: {foreign}"


def test_should_link_people_only_to_same_firm_projects(corpora: dict[str, Corpus]) -> None:
    """The Section G join is firm-local: no firm can assert facts about another's work.

    A cross-firm link claims evidence the linking node cannot produce when asked.
    """
    cross_firm: list[str] = []
    for corpus in corpora.values():
        own_projects = {project["handle"] for project in corpus["projects"]}
        cross_firm += [
            f"{person['handle']} -> {linked}"
            for person in corpus["people"]
            for linked in person["projects"]
            if linked not in own_projects
        ]

    assert not cross_firm, f"person links reaching outside their own firm: {cross_firm}"


def test_should_band_every_disclosure_cost(corpora: dict[str, Corpus]) -> None:
    """0 free, 1 NDA-limited, 2 sensitive, 3 blocked — the optimiser's whole cost axis.

    An out-of-range cost either sorts ahead of the free records or is never offered at all.
    """
    out_of_range = [
        f"{record['handle']}={record['disclosure_cost']}"
        for corpus in corpora.values()
        for record in (*corpus["projects"], *corpus["people"])
        if record["disclosure_cost"] not in (0, 1, 2, 3)
    ]

    assert not out_of_range, f"disclosure costs outside 0-3: {out_of_range}"


def test_should_leave_the_optimiser_something_to_substitute(corpora: dict[str, Corpus]) -> None:
    """The BD lead denies a sensitive record on stage and the optimiser swaps in another.

    With no cost-2 record there is nothing to deny; with only one affordable record there
    is nothing to swap in, and the beat plays as a dead end instead of a re-plan.
    """
    projects = [p for corpus in corpora.values() for p in corpus["projects"]]
    records = projects + [p for corpus in corpora.values() for p in corpus["people"]]

    assert any(p["disclosure_cost"] == 2 for p in projects), (
        "no project is sensitive enough to deny — the denial beat has nothing to refuse"
    )
    assert len([r for r in records if r["disclosure_cost"] <= 2]) >= 2, (
        "fewer than two affordable records — the optimiser has nothing to substitute once "
        "one is denied"
    )


def test_should_place_the_sole_r4_match_at_firm_b(r4_coverage: list[str]) -> None:
    """The entire scenario is that exactly one person, at Firm B, satisfies R4.

    A second match anywhere makes the gap findable alone and the federated round pointless;
    a project handle instead of a person makes it a Section F line, not the Section G cell.
    """
    assert len(r4_coverage) == 1, (
        f"R4 must have exactly one true match across all three firms, got {r4_coverage}"
    )
    assert r4_coverage[0].startswith("FIRM_B::PERSON::"), (
        f"the sole R4 match must be a Firm B person, got {r4_coverage[0]}"
    )


def test_should_hide_the_r4_match_in_non_obvious_wording(
    corpora: dict[str, Corpus], r4_coverage: list[str]
) -> None:
    """Round 1 has to miss this bio and round 2 has to find it.

    Naming both halves outright makes the match a plain keyword hit, so round 1 finds it
    and the gap-directed re-examination — the point of the whole demo — has nothing left
    to discover.
    """
    handle = r4_coverage[0]
    person = next((p for p in corpora["FIRM_B"]["people"] if p["handle"] == handle), None)

    assert person is not None, (
        f"ground truth names {handle} as the sole R4 match but firm_b.json has no such "
        "person, so the baselines score a match no node can produce"
    )
    bio = person["bio"].lower()
    assert not ("seismic" in bio and "healthcare" in bio), (
        f"{handle}'s bio names both halves of R4 outright, so round 1 finds the match and "
        "the round-2 beat dies; describe the hospital work obliquely, per data/README.md"
    )
