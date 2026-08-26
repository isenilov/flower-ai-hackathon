"""Every scenario carries the same engineered properties, not just the default one.

``tests/test_invariants.py`` guards the default scenario's files directly, because those are
the paths the brief names and the demo runs. The alternates under ``data/scenarios/`` exist to
back a specific claim — swap the requirement set and the cost function and the same harness
runs — and that claim is worth exactly as much as the weakest scenario behind it.

Rather than restate the rules here, this runs the scenario build pass itself. It is the same
code ``make data`` runs, so a rule added there is enforced here the moment it lands, and the
committed ``ground_truth.json`` files cannot drift away from the corpora they were derived
from without a red bar.
"""

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

DATA = Path(__file__).resolve().parents[1] / "data"


def _import_generate() -> Any:
    """Load ``data/generate.py`` by path — ``data/`` is a corpus directory, not a package."""
    spec = importlib.util.spec_from_file_location("data_generate", DATA / "generate.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


generate = _import_generate()
MANIFEST = json.loads((DATA / "scenarios.json").read_text())
SCENARIOS = MANIFEST["scenarios"]
VOCABULARY = json.loads((DATA / "vocabulary.json").read_text())


def _slug(scenario: dict[str, Any]) -> str:
    return scenario["slug"]


def test_should_keep_the_default_scenario_at_the_paths_everything_names() -> None:
    """`data/rfp.json` and `data/firm_*.json` are wired into the brief, the tests and the demo.

    Moving the default scenario into `data/scenarios/` alongside the alternates would be
    tidier and would break every one of them at once.
    """
    default = next(s for s in SCENARIOS if s["slug"] == MANIFEST["default"])

    assert default["path"] == "."


@pytest.mark.parametrize("scenario", SCENARIOS, ids=_slug)
def test_should_hold_every_engineered_property(scenario: dict[str, Any]) -> None:
    """One person holds the Section G cell, round 1 cannot reach them, round 2 can.

    Plus the rest of what the run rests on: three firms that each self-assess compliant, a
    sensitive record worth denying, a cheaper one to substitute in, and a blocked record the
    optimiser must never even be offered. `data/generate.py` states each rule with the reason
    it exists; the failure text is the explanation.
    """
    _, failures = generate.build(scenario, VOCABULARY)

    assert not failures, "\n".join(["", *failures])


@pytest.mark.parametrize("scenario", SCENARIOS, ids=_slug)
def test_should_match_the_committed_ground_truth(scenario: dict[str, Any]) -> None:
    """A corpus edited without re-running `make data` scores against a stale oracle.

    The baselines read `ground_truth.json`, not the corpora. Retune a bio, forget the rebuild,
    and the three-condition table reports on records that no longer say what it thinks.
    """
    built, _ = generate.build(scenario, VOCABULARY)
    committed = json.loads((DATA / scenario["path"] / "ground_truth.json").read_text())

    assert committed == built, (
        f"{scenario['slug']}/ground_truth.json is stale — run `make data` and commit the result"
    )
