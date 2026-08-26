"""Firm node: private library in, banded attestations out.

One firm's agent lives here. It reads a library that never leaves the node and answers a
coordinator round with :class:`~backend.schema.Attestation` records — banded, anonymised
evidence that a matching record exists. The record itself stays put.

The banding helpers and the wire encoding below are deliberately minimal so that
``backend.bander`` and ``backend.transport`` can take them over without changing callers.
"""

import json
from pathlib import Path
from typing import Any

from flwr.app import ConfigRecord, Context, Message, RecordDict
from flwr.clientapp import ClientApp

from backend.schema import VOCABULARY, Attestation, Requirement

# Firm order is the simulation's partition order.
FIRMS = ("a", "b", "c")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# `completed` is banded against this year rather than the wall clock, so a run is
# reproducible and the engineered R4 gap does not drift.
REFERENCE_YEAR = 2026

ATTESTATIONS_KEY = "attestations"


def load_library(context: Context) -> dict[str, Any]:
    """Load this node's private library.

    Simulation and deployment are discriminated on ``node_config`` exactly as the Hub's
    dual-runtime requirement specifies: a simulated SuperNode carries ``partition-id``
    and ``num-partitions``, a real one carries a ``library-path`` to its own data.
    """
    node_config = context.node_config
    if "partition-id" in node_config and "num-partitions" in node_config:
        partition_id = int(node_config["partition-id"])
        path = DATA_DIR / f"firm_{FIRMS[partition_id % len(FIRMS)]}.json"
    else:
        path = Path(str(node_config["library-path"]))
    return json.loads(path.read_text())


# ----------------------------------------------------------------------- banding


def _band(ordered: tuple[str, ...], index: int) -> str:
    """Clamp an index into an ordered band list."""
    return ordered[min(max(index, 0), len(ordered) - 1)]


def _value_band(value_usd: int) -> str:
    thresholds = (10, 50, 100, 250)  # in millions, matching VOCABULARY["value_band"]
    millions = value_usd / 1_000_000
    index = sum(millions >= threshold for threshold in thresholds)
    return _band(VOCABULARY["value_band"], index)


def _recency_band(completed: str) -> str:
    year = int(completed.split("-")[0])
    age = REFERENCE_YEAR - year
    index = 0 if age <= 3 else (1 if age <= 7 else 2)
    return _band(VOCABULARY["recency_band"], index)


def band_project(project: dict[str, Any]) -> dict[str, str]:
    """Reduce a project record to vocabulary-constrained fields."""
    banded = {
        "sector": project.get("sector", ""),
        "delivery": project.get("delivery", ""),
        "client_type": project.get("client_type", ""),
        "certification": project.get("certification", "none"),
    }
    if "value_usd" in project:
        banded["value_band"] = _value_band(int(project["value_usd"]))
    if "completed" in project:
        banded["recency_band"] = _recency_band(str(project["completed"]))
    return {key: value for key, value in banded.items() if value}


def band_person(person: dict[str, Any]) -> dict[str, str]:
    """Reduce a person record to vocabulary-constrained fields.

    ``role`` and ``experience`` are not in the closed vocabulary; they are requirement-side
    keys, so they pass through as-is and the bander validates them on egress.
    """
    banded = {"role": person.get("role", "")}
    credentials = [c for c in person.get("credentials", []) if c in VOCABULARY["credentials"]]
    if credentials:
        banded["credentials"] = ",".join(sorted(credentials))
    return {key: value for key, value in banded.items() if value}


# ---------------------------------------------------------------------- matching


def _rank_order(ordered: tuple[str, ...] | None) -> tuple[str, ...] | None:
    """Return a band list ordered worst-to-best for ``_min`` / ``_max`` comparison.

    ``VOCABULARY["certification"]`` ends in ``"none"`` because it is a set, not a scale.
    Left alone, an uncertified project would satisfy ``certification_min = LEED-Gold``.
    """
    if ordered is None or "none" not in ordered:
        return ordered
    return ("none",) + tuple(band for band in ordered if band != "none")


def matches(predicate: dict[str, str], banded: dict[str, str], text: str = "") -> bool:
    """Test one requirement predicate against a banded record.

    Three predicate forms: plain equality, ``<key>_min`` / ``<key>_max`` over an ordered
    band list, and free-text keys that fall through to a substring search over the
    record's narrative or bio. ``join`` is handled by the caller, not here.
    """
    for key, wanted in predicate.items():
        if key == "join":
            continue

        if key.endswith(("_min", "_max")):
            field, bound = key.rsplit("_", 1)
            ordered = _rank_order(VOCABULARY.get(field))
            have = banded.get(field)
            if ordered is None or have not in ordered or wanted not in ordered:
                return False
            if bound == "min" and ordered.index(have) < ordered.index(wanted):
                return False
            if bound == "max" and ordered.index(have) > ordered.index(wanted):
                return False
            continue

        have = banded.get(key)
        if have is None:
            # Not a banded field — round 1 can only look for it in free text.
            if wanted.replace("-", " ") not in text.lower():
                return False
            continue

        if wanted not in have.split(","):
            return False

    return True


def attest(library: dict[str, Any], requirements: list[Requirement]) -> list[Attestation]:
    """Emit one attestation per (requirement, matching record) pair.

    ``disclosure_cost`` 3 means blocked: those records never enter the candidate set, so a
    refusal cannot be routed around downstream.
    """
    firm = str(library.get("firm", "UNKNOWN"))
    attestations: list[Attestation] = []

    for requirement in requirements:
        wants_join = requirement.predicate.get("join") == "person_x_project"
        records = library.get("people" if requirement.section in ("E", "G") else "projects", [])

        for record in records:
            if int(record.get("disclosure_cost", 0)) >= 3:
                continue

            is_person = "bio" in record or "projects" in record
            banded = band_person(record) if is_person else band_project(record)
            text = str(record.get("bio") or record.get("narrative") or "")

            if not matches(requirement.predicate, banded, text):
                continue

            links = [h for h in record.get("projects", []) if h.startswith(firm)]
            if wants_join and not links:
                # Section G needs the person-on-project join, not just the person.
                continue

            attestations.append(
                Attestation(
                    handle=str(record["handle"]),
                    firm=firm,
                    kind="PERSON" if is_person else "PROJECT",
                    requirement_id=requirement.id,
                    match_strength=1.0,
                    banded=banded,
                    disclosure_cost=int(record.get("disclosure_cost", 0)),
                    links=links,
                )
            )

    return attestations


# --------------------------------------------------------------------- transport


def encode(attestations: list[Attestation]) -> RecordDict:
    """Put attestations on the wire. Interim home; ``backend.transport`` should own this."""
    payload = json.dumps([a.__dict__ for a in attestations])
    return RecordDict({ATTESTATIONS_KEY: ConfigRecord({"json": payload})})


def decode(content: RecordDict) -> list[Attestation]:
    """Read attestations off the wire."""
    payload = str(content[ATTESTATIONS_KEY]["json"])
    return [Attestation(**item) for item in json.loads(payload)]


# ----------------------------------------------------------------------- the app


def make_client_app() -> ClientApp:
    """Build the firm-node ``ClientApp``.

    Used by ``backend.client_app`` for the federated surface and by
    ``backend.agent_app`` through ``LocalGrid`` for the published harness.
    """
    app = ClientApp()

    @app.query()
    def query(msg: Message, context: Context) -> Message:
        """Answer a coordinator round with this firm's attestations."""
        requirements = [
            Requirement(**item) for item in json.loads(str(msg.content["rfp"]["requirements"]))
        ]
        library = load_library(context)
        return Message(content=encode(attest(library, requirements)), reply_to=msg)

    return app
