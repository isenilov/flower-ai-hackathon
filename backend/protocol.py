"""The harness protocol, independent of which surface drives it.

Four stages over parties that are not allowed to pool their data::

    attest -> detect gap -> re-examine locally against the gap -> minimise disclosure

Stages one and two live here. Everything is parameterised by a ``Grid``, so the same loop
runs under the published ``AgentApp`` (over ``LocalGrid``, in process) and under the
federated ``ServerApp`` (over a real grid, one SuperNode per firm). Neither surface owns
the protocol; both call it.
"""

import json
import os
from dataclasses import dataclass

from flwr.app import ConfigRecord, Message, MessageType, RecordDict
from flwr.serverapp import Grid

from backend.firm_node import ATTESTATIONS_KEY, decode
from backend.scenarios import Scenario, resolve
from backend.schema import Attestation, Requirement
from backend.trace import TRACE_VERSION, Trace

# `flwr.simulation.run_simulation` hands the ServerApp an empty run_config, so the
# federated surface reads its round count and scenario from the environment instead.
ROUNDS_ENV = "CONSORTIUM_NUM_ROUNDS"
SCENARIO_ENV = "CONSORTIUM_SCENARIO"
DEFAULT_ROUNDS = 3


@dataclass
class Outcome:
    """What one protocol run established."""

    solicitation: str
    requirements: list[Requirement]
    covered: dict[str, list[Attestation]]
    rounds_run: int

    @property
    def open_gaps(self) -> list[str]:
        """Requirements the consortium still cannot evidence."""
        return [r.id for r in self.requirements if len(self.covered[r.id]) < r.min_count]

    @property
    def mandatory_gaps(self) -> list[str]:
        """The open gaps that make the bid non-compliant rather than merely weaker."""
        open_gaps = set(self.open_gaps)
        return [r.id for r in self.requirements if r.kind == "MANDATORY" and r.id in open_gaps]


def load_rfp(scenario: Scenario | None = None) -> tuple[str, str, list[Requirement]]:
    """Decompose a scenario's solicitation into typed requirements.

    ``as_of`` fixes the reference date for recency banding, so the same corpora give the
    same answer at rehearsal and on stage.
    """
    rfp = json.loads((scenario or resolve(None)).rfp_path.read_text())
    return (
        rfp["solicitation"],
        rfp["as_of"],
        [Requirement(**item) for item in rfp["requirements"]],
    )


def resolve_rounds(configured: object = None) -> int:
    """Round count from the run config, else the environment, else the default."""
    if configured not in (None, ""):
        return int(configured)  # type: ignore[arg-type]
    return int(os.environ.get(ROUNDS_ENV, DEFAULT_ROUNDS))


def resolve_scenario(configured: object = None) -> Scenario:
    """Scenario from the run config, else the environment, else the manifest default."""
    if configured not in (None, ""):
        return resolve(str(configured))
    return resolve(os.environ.get(SCENARIO_ENV) or None)


def run(
    grid: Grid,
    num_rounds: int,
    solicitation: str | None = None,
    trace: Trace | None = None,
    scenario: Scenario | None = None,
    model_id: str = "",
) -> Outcome:
    """Run the protocol to convergence or to ``num_rounds``, whichever comes first.

    ``model_id`` travels to the nodes because round 2 is a model reading prose. Without
    one, round 2 finds nothing and the gap stays open — which is the honest outcome, not
    a failure.
    """
    scenario = scenario or resolve(None)
    rfp_solicitation, as_of, requirements = load_rfp(scenario)
    requirements_json = json.dumps([r.__dict__ for r in requirements])
    node_ids = list(grid.get_node_ids())

    covered: dict[str, list[Attestation]] = {r.id: [] for r in requirements}
    open_gaps: list[str] = []
    rounds_run = 0
    banded_bytes = 0
    # Which requirements each firm has already spoken to, so a round-2 reply can be
    # reported as a delta. The delta is the demo beat: one firm answering a question it
    # could not have known to ask in round 1.
    answered: dict[str, set[str]] = {}

    if trace:
        trace.emit(
            "run_started",
            version=TRACE_VERSION,
            started_at=trace.started_at,
            scenario={
                "slug": scenario.slug,
                "title": scenario.title,
                "headline": scenario.headline,
                "gap": scenario.gap,
            },
            solicitation=solicitation or rfp_solicitation,
            as_of=as_of,
            num_rounds=num_rounds,
            firms=[f"node {node_id}" for node_id in node_ids],
            requirements=[
                {
                    "id": r.id,
                    "section": r.section,
                    "kind": r.kind,
                    "min_count": r.min_count,
                    "weight": r.weight,
                    "description": r.description,
                    "predicate": r.predicate,
                }
                for r in requirements
            ],
        )

    for server_round in range(1, num_rounds + 1):
        gap_ids = ",".join(open_gaps)
        content = RecordDict(
            {
                # The slug selects which synthetic corpus a partition stands for. A real
                # SuperNode carries its own `library-path` and ignores it. The model id
                # travels too, because round-2 re-examination is a model reading prose.
                "rfp": ConfigRecord(
                    {
                        "requirements": requirements_json,
                        "as_of": as_of,
                        "scenario": scenario.slug,
                        "model": model_id,
                    }
                ),
                # Round 1 broadcasts no gap. Later rounds carry it, and nothing else —
                # each firm re-queries its own library with a question it did not know
                # to ask, and the answer never travels in the other direction.
                "gap": ConfigRecord({"requirement_ids": gap_ids}),
            }
        )
        messages = [
            Message(
                content=content,
                message_type=MessageType.QUERY,
                dst_node_id=node_id,
                group_id=str(server_round),
            )
            for node_id in node_ids
        ]

        if trace:
            trace.emit("round_started", round=server_round, gap=list(open_gaps))
            trace.emit(
                "broadcast",
                round=server_round,
                gap=list(open_gaps),
                requirements=len(requirements),
                to=[f"node {node_id}" for node_id in node_ids],
                bytes=len(requirements_json.encode()) + len(gap_ids.encode()),
                # Counted apart from the round's payload because it is the whole claim:
                # what travels back to the firms is the hole, never the evidence.
                gap_bytes=len(gap_ids.encode()),
                reads_text=bool(gap_ids),
            )

        attestations: list[Attestation] = []
        for reply in grid.send_and_receive(messages):
            from_firm = decode(reply.content)
            attestations += from_firm
            if not trace:
                continue

            firm = from_firm[0].firm if from_firm else f"node {reply.metadata.src_node_id}"
            spoke_to = {a.requirement_id for a in from_firm}
            reply_bytes = len(str(reply.content[ATTESTATIONS_KEY]["json"]).encode())
            banded_bytes += reply_bytes
            trace.emit(
                "reply",
                round=server_round,
                firm=firm,
                attestations=len(from_firm),
                bytes=reply_bytes,
                per_requirement={
                    rid: sum(a.requirement_id == rid for a in from_firm) for rid in sorted(spoke_to)
                },
                new_requirements=sorted(spoke_to - answered.get(firm, set())),
                handles=sorted({a.handle for a in from_firm}),
            )
            answered[firm] = answered.get(firm, set()) | spoke_to

        covered = {r.id: [] for r in requirements}
        for attestation in attestations:
            covered.setdefault(attestation.requirement_id, []).append(attestation)

        rounds_run = server_round
        previous_gaps, open_gaps = (
            open_gaps,
            [r.id for r in requirements if len(covered[r.id]) < r.min_count],
        )

        if trace:
            trace.emit(
                "matrix",
                round=server_round,
                rows=[
                    {
                        "id": r.id,
                        "section": r.section,
                        "kind": r.kind,
                        "need": r.min_count,
                        "have": len(covered[r.id]),
                        "firms": sorted({a.firm for a in covered[r.id]}),
                        "met": len(covered[r.id]) >= r.min_count,
                        "attested": [
                            {
                                "firm": a.firm,
                                "handle": a.handle,
                                "kind": a.kind,
                                "disclosure_cost": a.disclosure_cost,
                                "banded": a.banded,
                            }
                            for a in covered[r.id]
                        ],
                    }
                    for r in requirements
                ],
                open_gaps=list(open_gaps),
                closed=sorted(set(previous_gaps) - set(open_gaps)),
            )

        if not open_gaps or open_gaps == previous_gaps:
            # Either the gap closed, or re-examination found nothing new and another
            # identical broadcast would only cost time.
            if trace:
                trace.emit(
                    "round_ended",
                    round=server_round,
                    open_gaps=list(open_gaps),
                    stopped="converged" if not open_gaps else "no-new-evidence",
                )
            break

        if trace:
            trace.emit("round_ended", round=server_round, open_gaps=list(open_gaps), stopped="")

    outcome = Outcome(
        solicitation=solicitation or rfp_solicitation,
        requirements=requirements,
        covered=covered,
        rounds_run=rounds_run,
    )

    if trace:
        trace.emit(
            "run_ended",
            rounds_run=rounds_run,
            open_gaps=outcome.open_gaps,
            mandatory_gaps=outcome.mandatory_gaps,
            compliant=not outcome.mandatory_gaps,
            banded_bytes=banded_bytes,
            # Nothing in this protocol puts record content on the wire, so the counter is
            # zero by construction rather than by policy. The approval gate is what will
            # make it non-zero, and only for handles a BD lead has released.
            record_bytes=0,
        )

    return outcome


def render(outcome: Outcome) -> str:
    """Render the coverage matrix as text.

    Text, not HTML: Hub's upload filter drops ``.html``/``.css``/``.js``, so a judge who
    installs this app from the Hub only ever sees what Python prints.
    """
    lines = [
        f"Solicitation: {outcome.solicitation}",
        "",
        f"{'REQ':<5} {'SEC':<4} {'KIND':<10} {'NEED':>5} {'HAVE':>5}  FIRMS  STATUS",
    ]
    for requirement in outcome.requirements:
        found = outcome.covered[requirement.id]
        firms = ",".join(sorted({a.firm.removeprefix("FIRM_") for a in found})) or "-"
        met = len(found) >= requirement.min_count
        lines.append(
            f"{requirement.id:<5} {requirement.section:<4} {requirement.kind:<10} "
            f"{requirement.min_count:>5} {len(found):>5}  {firms:<6} "
            f"{'ok' if met else 'GAP'}"
        )

    mandatory = outcome.mandatory_gaps
    lines += [
        "",
        f"rounds run: {outcome.rounds_run}",
        "disclosed records: 0 (attestations only)",
        f"open gaps: {', '.join(outcome.open_gaps) or 'none'}",
        f"bid is {'NON-COMPLIANT' if mandatory else 'compliant'}"
        f"{' — mandatory: ' + ', '.join(mandatory) if mandatory else ''}",
    ]
    return "\n".join(lines)
