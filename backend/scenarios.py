"""Scenario catalogue — which solicitation and which corpora a run stands on.

``data/scenarios.json`` is the manifest the Data owner maintains; this module is the only
thing that reads it on the run path. Every scenario has the same requirement ids and the
same record shapes, so nothing downstream — matcher, optimiser, or frontend — needs a
per-scenario branch.

The default scenario lives at ``data/`` itself rather than under ``data/scenarios/``, so the
paths the brief and the tests name do not move.
"""

import json
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CATALOGUE_PATH = DATA_DIR / "scenarios.json"


@dataclass(frozen=True)
class Scenario:
    """One solicitation and the three corpora that answer it."""

    slug: str
    root: Path
    title: str
    headline: str
    gap: dict[str, object]

    @property
    def rfp_path(self) -> Path:
        """Where this scenario's decomposed solicitation lives."""
        return self.root / "rfp.json"

    def library_path(self, firm: str) -> Path:
        """Where one firm's private library lives under this scenario."""
        return self.root / f"firm_{firm}.json"


def catalogue() -> dict[str, Scenario]:
    """Every scenario in the manifest, keyed by slug."""
    manifest = json.loads(CATALOGUE_PATH.read_text())
    return {
        entry["slug"]: Scenario(
            slug=entry["slug"],
            root=(DATA_DIR / entry["path"]).resolve(),
            title=entry["title"],
            headline=entry["headline"],
            gap=entry.get("gap", {}),
        )
        for entry in manifest["scenarios"]
    }


def default_slug() -> str:
    """The scenario a run uses when none is named."""
    return str(json.loads(CATALOGUE_PATH.read_text())["default"])


def resolve(slug: str | None) -> Scenario:
    """Look up a scenario by slug, falling back to the manifest's default.

    An unknown slug is an error rather than a silent fallback: running the wrong corpus
    and reporting it as the right one is the one failure that would survive rehearsal.
    """
    entries = catalogue()
    wanted = slug or default_slug()
    if wanted not in entries:
        raise KeyError(f"unknown scenario {wanted!r}; have {', '.join(sorted(entries))}")
    return entries[wanted]
