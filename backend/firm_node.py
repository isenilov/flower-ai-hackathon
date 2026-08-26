"""Firm node: private library in, banded attestations out.

One firm's agent lives here. It reads a library that never leaves the node and answers a
coordinator round with :class:`~backend.schema.Attestation` records — banded, anonymised
evidence that a matching record exists. The record itself stays put.

The banding helpers and the wire encoding below are deliberately minimal so that
``backend.bander`` and ``backend.transport`` can take them over without changing callers.
"""

import json
from logging import DEBUG
from pathlib import Path
from typing import Any

from flwr.app import ConfigRecord, Context, Message, RecordDict
from flwr.clientapp import ClientApp
from flwr.common.logger import log

from backend.scenarios import resolve
from backend.schema import NOTE_MAX_CHARS, VOCABULARY, Attestation, Requirement

# Firm order is the simulation's partition order.
FIRMS = ("a", "b", "c")

ATTESTATIONS_KEY = "attestations"


def load_library(context: Context, scenario: str = "") -> dict[str, Any]:
    """Load this node's private library.

    Simulation and deployment are discriminated on ``node_config`` exactly as the Hub's
    dual-runtime requirement specifies: a simulated SuperNode carries ``partition-id``
    and ``num-partitions``, a real one carries a ``library-path`` to its own data.

    ``scenario`` only reaches the simulated branch: it names which synthetic corpus this
    partition stands for. A real node's data is whatever its ``library-path`` points at,
    and no coordinator gets to redirect that.
    """
    node_config = context.node_config
    if "partition-id" in node_config and "num-partitions" in node_config:
        partition_id = int(node_config["partition-id"])
        firm = FIRMS[partition_id % len(FIRMS)]
        path = resolve(scenario or None).library_path(firm)
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


def _months_between(completed: str, as_of: str) -> int:
    completed_year, completed_month = (int(part) for part in completed.split("-")[:2])
    as_of_year, as_of_month = (int(part) for part in as_of.split("-")[:2])
    return (as_of_year - completed_year) * 12 + (as_of_month - completed_month)


def _recency_band(completed: str, as_of: str) -> str:
    """Band a completion date against the scenario's fixed reference date.

    ``as_of`` comes from ``rfp.json``, not the wall clock — otherwise a project silently
    ages out of R1 between rehearsal and demo.
    """
    months = _months_between(completed, as_of)
    index = 0 if months < 36 else (1 if months < 84 else 2)
    return _band(VOCABULARY["recency_band"], index)


def band_project(project: dict[str, Any], as_of: str) -> dict[str, str]:
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
        banded["recency_band"] = _recency_band(str(project["completed"]), as_of)
    return {key: value for key, value in banded.items() if value}


def band_person(person: dict[str, Any], declared_sector: dict[str, str]) -> dict[str, str]:
    """Reduce a person record to vocabulary-constrained fields.

    A person's sectors are the *declared* sectors of the projects they are booked to — that
    is where a firm's sectors have always come from, and it is what makes the Section G cell
    hideable. Firm B's holder is booked to work filed as civic, so no structured search
    reaches them; only the bio says the building was a hospital, and only round 2 reads bios.
    """
    banded = {"role": person.get("role", "")}
    credentials = [c for c in person.get("credentials", []) if c in VOCABULARY["credentials"]]
    if credentials:
        banded["credentials"] = ",".join(sorted(credentials))
    sectors = {declared_sector[h] for h in person.get("projects", []) if h in declared_sector}
    if sectors:
        banded["sector"] = ",".join(sorted(sectors))
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


def matches(predicate: dict[str, str], banded: dict[str, str]) -> bool:
    """Test one requirement predicate against a banded record.

    Declared fields only: plain equality (multi-valued fields are comma-joined) and
    ``<key>_min`` / ``<key>_max`` over an ordered band list. ``join`` is handled by the
    caller, not here.

    A predicate key with no declared source fails. That is the round boundary, and it is
    why the Section G cell survives round 1 — reading prose is round 2's job.
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

        declared = banded.get(key)
        if declared is None:
            # No declared source for this key, so a structured search cannot satisfy it.
            # Round 2 is what reads prose, and it does that with a model in
            # ``agents.reexamine`` rather than by keyword here.
            return False

        if wanted not in declared.split(","):
            return False

    return True


def _attestation(
    record: dict[str, Any],
    firm: str,
    requirement: Requirement,
    banded: dict[str, str],
    is_person: bool,
    match_strength: float,
    note: str = "",
) -> Attestation:
    """Wrap one matching record as banded evidence that it exists."""
    return Attestation(
        handle=str(record["handle"]),
        firm=firm,
        kind="PERSON" if is_person else "PROJECT",
        requirement_id=requirement.id,
        match_strength=match_strength,
        banded=banded,
        disclosure_cost=int(record.get("disclosure_cost", 0)),
        links=[h for h in record.get("projects", []) if h.startswith(firm)],
        note=note[:NOTE_MAX_CHARS],
    )


def _band_of(record: dict[str, Any], declared_sector: dict[str, str], as_of: str) -> dict[str, str]:
    is_person = "bio" in record or "projects" in record
    return band_person(record, declared_sector) if is_person else band_project(record, as_of)


def attest(
    library: dict[str, Any], requirements: list[Requirement], as_of: str
) -> list[Attestation]:
    """Round 1: emit one attestation per (requirement, declared match) pair.

    ``disclosure_cost`` 3 means blocked: those records never enter the candidate set, so a
    refusal cannot be routed around downstream. This is why attestation counts sit below
    ``ground_truth.json``'s ``coverage`` — that is the oracle over every record, blocked
    ones included, while a node only ever attests to what it could actually offer.
    """
    firm = str(library.get("firm", "UNKNOWN"))
    declared_sector = {p["handle"]: p["sector"] for p in library.get("projects", [])}
    attestations: list[Attestation] = []

    for requirement in requirements:
        wants_join = requirement.predicate.get("join") == "person_x_project"
        records = library.get("people" if requirement.section in ("E", "G") else "projects", [])

        for record in records:
            if int(record.get("disclosure_cost", 0)) >= 3:
                continue

            is_person = "bio" in record or "projects" in record
            banded = _band_of(record, declared_sector, as_of)
            if not matches(requirement.predicate, banded):
                continue

            links = [h for h in record.get("projects", []) if h.startswith(firm)]
            if wants_join and not links:
                # Section G needs the person-on-project join, not just the person.
                continue

            attestations.append(_attestation(record, firm, requirement, banded, is_person, 1.0))

    return attestations


def reexamine_gaps(
    library: dict[str, Any],
    requirements: list[Requirement],
    gap_ids: list[str],
    as_of: str,
    reader: object | None,
    model_id: str,
) -> list[Attestation]:
    """Round 2: re-read this firm's own prose against each broadcast gap.

    The node is handed the uncovered requirement and nothing else — not the answer, not
    which of its records to look at. ``match_strength`` is below 1.0 because this is a
    judgement about prose, not an exact match on a declared field, and the optimiser
    downstream should be able to tell the difference.
    """
    if reader is None or not gap_ids or not model_id:
        return []

    from agents.reexamine import reexamine  # imported here to keep round 1 dependency-free

    firm = str(library.get("firm", "UNKNOWN"))
    declared_sector = {p["handle"]: p["sector"] for p in library.get("projects", [])}
    by_handle = {
        record["handle"]: record
        for group in ("projects", "people")
        for record in library.get(group, [])
    }

    attestations: list[Attestation] = []
    for requirement in (r for r in requirements if r.id in gap_ids):
        wants_join = requirement.predicate.get("join") == "person_x_project"
        for handle, why in reexamine(library, requirement, reader, model_id).items():  # type: ignore[arg-type]
            record = by_handle[handle]
            links = [h for h in record.get("projects", []) if h.startswith(firm)]
            if wants_join and not links:
                continue

            # The model's reasoning stays on the node. It is prose derived from a bio, and
            # the whole claim is that no record content leaves before authorisation — so
            # the wire gets requirement-side vocabulary only, never the model's sentence.
            log(DEBUG, "[%s] %s evidences %s: %s", firm, handle, requirement.id, why)
            terms = sorted(k for k in requirement.predicate if k != "join")

            attestations.append(
                _attestation(
                    record,
                    firm,
                    requirement,
                    _band_of(record, declared_sector, as_of),
                    is_person="bio" in record or "projects" in record,
                    match_strength=0.8,
                    note=f"prose evidences: {', '.join(terms)}",
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


def make_client_app(injected_reader: object | None = None) -> ClientApp:
    """Build the firm-node ``ClientApp``.

    Used by ``backend.client_app`` for the federated surface and by
    ``backend.agent_app`` through ``LocalGrid`` for the published harness.

    ``injected_reader`` is how a model reaches a node. Only the AgentApp has an
    ``AgentSession``, so it passes ``agent.responses.create`` down; the federated surface
    passes nothing and each node resolves its own endpoint from the environment.
    """
    app = ClientApp()

    @app.query()
    def query(msg: Message, context: Context) -> Message:
        """Answer a coordinator round with this firm's attestations."""
        from agents import model as model_client

        rfp = msg.content["rfp"]
        requirements = [Requirement(**item) for item in json.loads(str(rfp["requirements"]))]
        as_of = str(rfp["as_of"])
        model_id = str(rfp["model"]) if "model" in rfp else ""
        gap_ids = [gid for gid in str(msg.content["gap"]["requirement_ids"]).split(",") if gid]

        library = load_library(context, str(rfp["scenario"]) if "scenario" in rfp else "")
        attestations = attest(library, requirements, as_of)
        if gap_ids:
            # A broadcast gap is the only thing that licenses re-reading prose.
            reader = model_client.resolve_reader(injected_reader)  # type: ignore[arg-type]
            attestations += reexamine_gaps(library, requirements, gap_ids, as_of, reader, model_id)

        return Message(content=encode(attestations), reply_to=msg)

    return app
