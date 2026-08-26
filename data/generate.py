"""Scenario build pass: derive ground truth from the corpora, and refuse to write it if the
engineered gap has been edited away.

Schema first, then generate. The record shapes in ``data/README.md`` are fixed before this
runs and the corpora themselves are hand-authored JSON — this pass invents no records. What
it does is the part that must never drift: it evaluates every typed predicate in a scenario's
``rfp.json`` against that scenario's three firm corpora, writes the result to
``ground_truth.json``, and fails loudly if the properties the demo rests on are gone.

Three readings of the same corpora are produced, and the whole scenario lives in the gap
between them:

``declared``  what a round-1 agent's structured prefilter can see. A person's sectors are the
              declared sectors of the projects they are linked to, and nothing more.
``firm``      what a firm knows about itself before any federation. It reads its own bios, so
              it knows its people's disciplines — but sectors still come from its project
              ledger, because that is where a firm's sectors have always come from.
``oracle``    what a perfect reader of the free text would find: the declared fields plus the
              full scenario lexicon over project narratives and person bios.

Round 1 misses the Section G cell because the holder's linked projects declare the wrong
sector. Round 2 finds it because the bio says so in prose. That wording is a tuning
parameter, not fixed data (``data/README.md``): re-tune it, run ``make data``, and this pass
says immediately whether round 1 can still miss it and round 2 still find it.

Usage:
    uv run python data/generate.py                    # every scenario in data/scenarios.json
    uv run python data/generate.py healthcare-seismic
    uv run python data/generate.py --check            # verify only, write nothing
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent
MANIFEST = DATA / "scenarios.json"
FIRMS = ("FIRM_A", "FIRM_B", "FIRM_C")

# The Hub rejects a source file over 1 MB (brief §10.3).
MAX_FILE_BYTES = 1_000_000

# The SF330 section decides what kind of record can answer a requirement: E is resumes, F is
# example projects, G is the person-by-project matrix.
SECTION_KIND = {"E": "PERSON", "F": "PROJECT", "G": "PERSON"}

# `_min` / `_max` read the band list in vocabulary.json positionally. Certification is the one
# closed set whose list order is not its rank — "none" is listed last there but ranks below
# every award — so its order is pinned here instead.
CERTIFICATION_ORDER = ("none", "LEED-Silver", "LEED-Gold", "LEED-Platinum")

Record = dict[str, Any]


# --------------------------------------------------------------------------------- facts


@dataclass(frozen=True)
class Facts:
    """One record reduced to what a typed predicate can be evaluated against."""

    handle: str
    firm: str
    kind: str
    cost: int
    fields: dict[str, str]
    credentials: tuple[str, ...]
    tags: frozenset[str]


def months_between(completed: str, as_of: str) -> int:
    completed_year, completed_month = (int(part) for part in completed.split("-")[:2])
    as_of_year, as_of_month = (int(part) for part in as_of.split("-")[:2])
    return (as_of_year - completed_year) * 12 + (as_of_month - completed_month)


def value_band(usd: int, order: tuple[str, ...]) -> str:
    """Band an exact contract value. The exact figure never leaves the node."""
    for band, ceiling in zip(order, (10, 50, 100, 250), strict=False):
        if usd < ceiling * 1_000_000:
            return band
    return order[-1]


def recency_band(completed: str, as_of: str, order: tuple[str, ...]) -> str:
    """Band an exact completion date against the scenario's fixed reference date."""
    months = months_between(completed, as_of)
    for band, ceiling in zip(order, (36, 84), strict=False):
        if months < ceiling:
            return band
    return order[-1]


def compile_lexicon(lexicon: dict[str, list[str]]) -> dict[str, re.Pattern[str]]:
    """Word-boundary matchers, one per evidence tag.

    Boundaries matter: "ward" must not fire on "awarded", and a substring match would make the
    uniqueness check on the Section G cell quietly meaningless.
    """
    compiled = {}
    for tag, words in lexicon.items():
        longest_first = sorted(words, key=len, reverse=True)
        alternation = "|".join(re.escape(word) for word in longest_first)
        compiled[tag] = re.compile(rf"\b(?:{alternation})\b", re.IGNORECASE)
    return compiled


def read_tags(text: str, patterns: dict[str, re.Pattern[str]]) -> set[str]:
    return {tag for tag, pattern in patterns.items() if pattern.search(text)}


def build_facts(
    corpora: dict[str, Record],
    vocabulary: dict[str, list[str]],
    as_of: str,
    patterns: dict[str, re.Pattern[str]],
    mode: str,
) -> dict[str, list[Facts]]:
    """Reduce every record in every firm to `Facts` under one of the three evidence modes.

    The `firm` mode is the load-bearing one. A firm reads its own bios, so it knows perfectly
    well who its tunnellers and its seismic engineers are — what it does not do is re-file a
    project's sector on the strength of a sentence in a resume. Its people are transport
    people because the ledger says the job was transport.
    """
    sectors = set(vocabulary["sector"])
    if mode == "declared":
        readable: dict[str, re.Pattern[str]] = {}
    elif mode == "firm":
        readable = {tag: pattern for tag, pattern in patterns.items() if tag not in sectors}
    else:
        readable = patterns
    value_order = tuple(vocabulary["value_band"])
    recency_order = tuple(vocabulary["recency_band"])
    by_firm: dict[str, list[Facts]] = {}

    for firm, corpus in corpora.items():
        declared_sector: dict[str, str] = {}
        facts: list[Facts] = []

        for project in corpus["projects"]:
            declared_sector[project["handle"]] = project["sector"]
            tags = {project["sector"]} | read_tags(project["narrative"], readable)
            facts.append(
                Facts(
                    handle=project["handle"],
                    firm=firm,
                    kind="PROJECT",
                    cost=project["disclosure_cost"],
                    fields={
                        "sector": project["sector"],
                        "delivery": project["delivery"],
                        "client_type": project["client_type"],
                        "certification": project["certification"],
                        "value_band": value_band(project["value_usd"], value_order),
                        "recency_band": recency_band(project["completed"], as_of, recency_order),
                    },
                    credentials=(),
                    tags=frozenset(tags),
                )
            )

        for person in corpus["people"]:
            # A person's sectors are the sectors of the work they are booked to. The bio is
            # read on top of that, and it is the only place a hidden cell ever lives.
            linked = [h for h in person["projects"] if h in declared_sector]
            tags = {declared_sector[handle] for handle in linked}
            tags |= read_tags(person["bio"], readable)
            facts.append(
                Facts(
                    handle=person["handle"],
                    firm=firm,
                    kind="PERSON",
                    cost=person["disclosure_cost"],
                    fields={"role": person["role"]},
                    credentials=tuple(person["credentials"]),
                    tags=frozenset(tags),
                )
            )

        by_firm[firm] = facts

    return by_firm


# ---------------------------------------------------------------------------- predicates


def satisfies_atom(facts: Facts, key: str, value: str, orders: dict[str, tuple[str, ...]]) -> bool:
    if key.endswith(("_min", "_max")):
        base, _, bound = key.rpartition("_")
        held = facts.fields.get(base)
        if held is None:
            return False
        order = orders[base]
        if bound == "min":
            return order.index(held) >= order.index(value)
        return order.index(held) <= order.index(value)
    if key == "credentials":
        return value in facts.credentials
    if key in ("sector", "experience"):
        return value in facts.tags
    return facts.fields.get(key) == value


def unmet_atoms(requirement: Record, facts: Facts, orders: dict[str, tuple[str, ...]]) -> list[str]:
    return [
        f"{key}={value}"
        for key, value in requirement["predicate"].items()
        if key != "join" and not satisfies_atom(facts, key, value, orders)
    ]


def covers(requirement: Record, facts: Facts, orders: dict[str, tuple[str, ...]]) -> bool:
    """The joined reading: one record satisfies every atom of the predicate at once."""
    if facts.kind != SECTION_KIND[requirement["section"]]:
        return False
    return not unmet_atoms(requirement, facts, orders)


def coverage(
    rfp: Record, facts_by_firm: dict[str, list[Facts]], orders: dict[str, tuple[str, ...]]
) -> dict[str, list[str]]:
    every = [f for facts in facts_by_firm.values() for f in facts]
    return {
        requirement["id"]: sorted(f.handle for f in every if covers(requirement, f, orders))
        for requirement in rfp["requirements"]
    }


def aggregate_citation(
    requirement: Record, facts: list[Facts], orders: dict[str, tuple[str, ...]]
) -> dict[str, str] | None:
    """The discipline view of a joined requirement: each half, held by anyone at all.

    This is the single line of difference between the isolated condition and the truth. A firm
    reading its roster by discipline sees healthcare people and it sees seismic people, and
    concludes the Section G cell is covered. It never asks whether they are the same person.
    """
    pool = [f for f in facts if f.kind == SECTION_KIND[requirement["section"]]]
    cited: dict[str, str] = {}
    for key, value in requirement["predicate"].items():
        if key == "join":
            continue
        holder = next((f for f in pool if satisfies_atom(f, key, value, orders)), None)
        if holder is None:
            return None
        cited[f"{key}={value}"] = holder.handle
    return cited


def self_assessment(
    rfp: Record, facts_by_firm: dict[str, list[Facts]], orders: dict[str, tuple[str, ...]]
) -> dict[str, Record]:
    """What each firm concludes from its own library alone, before any federation.

    Runs on the `firm` facts: a firm is not short of information about its own staff. What it
    does not do is the join, and no amount of reading its own resumes fixes that.
    """
    mandatory = [r["id"] for r in rfp["requirements"] if r["kind"] == "MANDATORY"]
    assessed: dict[str, Record] = {}

    for firm, facts in facts_by_firm.items():
        verdicts: dict[str, Record] = {}
        for requirement in rfp["requirements"]:
            if "join" in requirement["predicate"]:
                cited = aggregate_citation(requirement, facts, orders)
                verdicts[requirement["id"]] = {
                    "covered": cited is not None,
                    "reading": "aggregate",
                    "cited": cited or {},
                }
                continue
            handles = sorted(f.handle for f in facts if covers(requirement, f, orders))
            verdicts[requirement["id"]] = {
                "covered": len(handles) >= requirement["min_count"],
                "reading": "joined",
                "cited": handles,
            }
        assessed[firm] = {
            "compliant": all(verdicts[rid]["covered"] for rid in mandatory),
            "requirements": verdicts,
        }

    return assessed


# -------------------------------------------------------------------------------- verify


def near_misses(rfp: Record, facts: list[Facts], orders: dict[str, tuple[str, ...]]) -> list[str]:
    """Records that fail exactly one atom — what a correct matcher has to reject."""
    return sorted(
        {
            f.handle
            for f in facts
            for requirement in rfp["requirements"]
            if f.kind == SECTION_KIND[requirement["section"]]
            and len(unmet_atoms(requirement, f, orders)) == 1
        }
    )


def verify(
    scenario: Record,
    rfp: Record,
    corpora: dict[str, Record],
    oracle: dict[str, list[str]],
    round_one: dict[str, list[str]],
    assessed: dict[str, Record],
    facts_by_firm: dict[str, list[Facts]],
    firm_facts: dict[str, list[Facts]],
    orders: dict[str, tuple[str, ...]],
    vocabulary: dict[str, list[str]],
) -> list[str]:
    """Every engineered property the demo rests on, checked. Returns the failures."""
    failures: list[str] = []
    gap = scenario["gap"]
    mandatory = [r for r in rfp["requirements"] if r["kind"] == "MANDATORY"]
    closed = {key: set(values) for key, values in vocabulary.items()}

    # --- shape, handles, and the closed vocabulary ---------------------------------
    for firm, corpus in corpora.items():
        for record in (*corpus["projects"], *corpus["people"]):
            if not record["handle"].startswith(f"{firm}::"):
                failures.append(f"{record['handle']} is held by {firm} but does not name it")
            if record["disclosure_cost"] not in (0, 1, 2, 3):
                cost = record["disclosure_cost"]
                failures.append(f"{record['handle']} has disclosure_cost {cost}, outside 0-3")
        own = {project["handle"] for project in corpus["projects"]}
        for project in corpus["projects"]:
            for key in ("sector", "delivery", "client_type", "certification"):
                if project[key] not in closed[key]:
                    value = project[key]
                    failures.append(
                        f"{project['handle']}.{key}={value!r} is outside the vocabulary"
                    )
            if not re.fullmatch(r"\d{4}-\d{2}", project["completed"]):
                stamp = project["completed"]
                failures.append(f"{project['handle']}.completed={stamp!r} is not YYYY-MM")
        for person in corpus["people"]:
            for credential in person["credentials"]:
                if credential not in closed["credentials"]:
                    failures.append(
                        f"{person['handle']} holds {credential!r}, outside the vocabulary"
                    )
            for linked in person["projects"]:
                if linked not in own:
                    failures.append(f"{person['handle']} links outside its own firm: {linked}")

    # --- the engineered gap ---------------------------------------------------------
    holders = oracle.get(gap["requirement"], [])
    if len(holders) != 1:
        failures.append(
            f"{gap['requirement']} must have exactly one true match across all firms, got {holders}"
        )
    elif not holders[0].startswith(f"{gap['firm']}::PERSON::"):
        failures.append(
            f"the sole {gap['requirement']} match must be a {gap['firm']} person, got {holders[0]}"
        )
    else:
        handle = holders[0]
        person = next(p for p in corpora[gap["firm"]]["people"] if p["handle"] == handle)
        bio = person["bio"].lower()
        named = [tag for tag in gap["tags"] if all(word in bio for word in tag.split("-"))]
        if len(named) == len(gap["tags"]):
            failures.append(
                f"{handle}'s bio names every half of {gap['requirement']} outright ({named}), so "
                "round 1 finds the match by keyword and the round-2 beat dies"
            )
        linked_sectors = {
            project["sector"]
            for project in corpora[gap["firm"]]["projects"]
            if project["handle"] in person["projects"]
        }
        exposed = [tag for tag in gap["tags"] if tag in closed["sector"] and tag in linked_sectors]
        if exposed:
            failures.append(
                f"{handle} is linked to a project already declaring {exposed}, so a structured "
                "round-1 search reaches them and there is no gap left to broadcast"
            )

    # --- round 1 opens on exactly one red cell --------------------------------------
    if round_one.get(gap["requirement"]):
        found = round_one[gap["requirement"]]
        failures.append(
            f"round 1 already covers {gap['requirement']} via {found} — the joint coverage "
            "matrix opens with nothing red"
        )
    for requirement in mandatory:
        found = len(round_one.get(requirement["id"], []))
        if requirement["id"] != gap["requirement"] and found < requirement["min_count"]:
            failures.append(
                f"round 1 leaves {requirement['id']} short ({found}/{requirement['min_count']}) — "
                f"only {gap['requirement']} may be red on the joint matrix"
            )
        if len(oracle.get(requirement["id"], [])) < requirement["min_count"]:
            failures.append(
                f"{requirement['id']} is unsatisfiable even with every library open — the "
                "consortium condition cannot reach compliance"
            )

    # --- the isolated condition is confidently wrong --------------------------------
    gap_requirement = next(r for r in rfp["requirements"] if r["id"] == gap["requirement"])
    for firm, facts in firm_facts.items():
        alone = [f.handle for f in facts if covers(gap_requirement, f, orders)]
        if alone:
            failures.append(
                f"{firm} can join {gap['requirement']} from its own library ({alone}) — "
                "'no single firm could have seen this' is then not true"
            )
    for firm, verdict in assessed.items():
        if not verdict["compliant"]:
            short = [rid for rid, v in verdict["requirements"].items() if not v["covered"]]
            failures.append(
                f"{firm} does not self-assess compliant (short on {short}) — the demo opens on "
                "three firms that each believe the bid is already fine"
            )

    # --- the disclosure beats -------------------------------------------------------
    every = [f for facts in facts_by_firm.values() for f in facts]
    if not any(f.kind == "PROJECT" and f.cost == 2 for f in every):
        failures.append(
            "no project is sensitive enough to deny — the denial beat has nothing to refuse"
        )

    substitutable = False
    for requirement in mandatory:
        if SECTION_KIND[requirement["section"]] != "PROJECT":
            continue
        affordable = [f for f in every if f.cost <= 2 and covers(requirement, f, orders)]
        if any(f.cost == 2 for f in affordable) and len(affordable) > requirement["min_count"]:
            substitutable = True
    if not substitutable:
        failures.append(
            "denying any sensitive project leaves a mandatory requirement short — the optimiser "
            "has nothing to substitute and the beat plays as a dead end"
        )

    if not any(
        f.cost == 3 and any(covers(r, f, orders) for r in rfp["requirements"]) for f in every
    ):
        failures.append(
            "no cost-3 record would have matched anything — 'the refusal is honoured' is then a "
            "claim about a candidate set that never excluded a thing"
        )

    for firm, facts in facts_by_firm.items():
        found_misses = near_misses(rfp, facts, orders)
        if len(found_misses) < 2:
            failures.append(
                f"{firm} carries {len(found_misses)} near-miss distractors, want at least 2"
            )

    # --- size ------------------------------------------------------------------------
    for path in sorted((DATA / scenario["path"]).glob("*.json")):
        if path.stat().st_size > MAX_FILE_BYTES:
            failures.append(f"{path.relative_to(DATA)} is over 1 MB — the Hub upload rejects it")

    return failures


# --------------------------------------------------------------------------------- build


def build(scenario: Record, vocabulary: dict[str, list[str]]) -> tuple[Record, list[str]]:
    """Derive one scenario's ground truth and check it. Returns (ground_truth, failures)."""
    root = DATA / scenario["path"]
    rfp = json.loads((root / "rfp.json").read_text())
    corpora = {firm: json.loads((root / f"{firm.lower()}.json").read_text()) for firm in FIRMS}

    as_of = rfp["as_of"]
    patterns = compile_lexicon(scenario["lexicon"])
    orders = {
        "value_band": tuple(vocabulary["value_band"]),
        "recency_band": tuple(vocabulary["recency_band"]),
        "certification": CERTIFICATION_ORDER,
    }

    oracle_facts = build_facts(corpora, vocabulary, as_of, patterns, "oracle")
    firm_facts = build_facts(corpora, vocabulary, as_of, patterns, "firm")
    declared_facts = build_facts(corpora, vocabulary, as_of, patterns, "declared")

    oracle = coverage(rfp, oracle_facts, orders)
    round_one = coverage(rfp, declared_facts, orders)
    assessed = self_assessment(rfp, firm_facts, orders)

    failures = verify(
        scenario,
        rfp,
        corpora,
        oracle,
        round_one,
        assessed,
        oracle_facts,
        firm_facts,
        orders,
        vocabulary,
    )

    every = [f for facts in oracle_facts.values() for f in facts]
    offerable = [
        f for f in every if f.cost <= 2 and any(covers(r, f, orders) for r in rfp["requirements"])
    ]
    holders = oracle.get(scenario["gap"]["requirement"]) or [None]

    ground_truth = {
        "scenario": scenario["slug"],
        "solicitation": rfp["solicitation"],
        "as_of": as_of,
        "gap": {**scenario["gap"], "handle": holders[0]},
        "coverage": oracle,
        "round_one_coverage": round_one,
        "self_assessment": assessed,
        "candidate_pool": {
            "records": len(every),
            "offerable": len(offerable),
            "blocked": sum(1 for f in every if f.cost == 3),
        },
        "notes": (
            "Derived by data/generate.py — do not hand-edit. `coverage` is the oracle reading: "
            "declared fields plus the scenario lexicon over narratives and bios, which is what a "
            "centralised pool with a perfect reader would find. `round_one_coverage` is the same "
            "predicates against declared fields only, which is what a firm's agent sees before the "
            "gap is broadcast. The difference between the two is the Section G cell. "
            "`self_assessment` is each firm alone, reading a joined requirement as an aggregate — "
            "the one word of difference that makes the isolated condition confidently wrong. "
            "Read only by backend/baselines.py, never by a firm node."
        ),
    }
    return ground_truth, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and verify the scenario datasets.")
    parser.add_argument("slugs", nargs="*", help="scenarios to build (default: all of them)")
    parser.add_argument("--check", action="store_true", help="verify only, write nothing")
    args = parser.parse_args(argv)

    manifest = json.loads(MANIFEST.read_text())
    vocabulary = json.loads((DATA / "vocabulary.json").read_text())
    scenarios = [s for s in manifest["scenarios"] if not args.slugs or s["slug"] in args.slugs]
    if not scenarios:
        parser.error(f"no scenario in {MANIFEST.name} matches {args.slugs}")

    failed = 0
    for scenario in scenarios:
        ground_truth, failures = build(scenario, vocabulary)
        gap = ground_truth["gap"]
        status = "FAIL" if failures else "ok"
        print(f"{scenario['slug']:<24} {status:<5} {gap['requirement']} -> {gap['handle']}")
        for failure in failures:
            print(f"  ! {failure}")
        if failures:
            failed += 1
            continue
        pool = ground_truth["candidate_pool"]
        print(
            f"{'':<24}       {pool['offerable']} of {pool['records']} records offerable, "
            f"{pool['blocked']} blocked"
        )
        if not args.check:
            target = DATA / scenario["path"] / "ground_truth.json"
            target.write_text(json.dumps(ground_truth, indent=2, ensure_ascii=False) + "\n")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
