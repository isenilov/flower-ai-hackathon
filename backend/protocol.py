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
from pathlib import Path

from flwr.app import ConfigRecord, Message, MessageType, RecordDict
from flwr.serverapp import Grid

from backend.firm_node import decode
from backend.schema import Attestation, Requirement

RFP_PATH = Path(__file__).resolve().parent.parent / "data" / "rfp.json"

# `flwr.simulation.run_simulation` hands the ServerApp an empty run_config, so the
# federated surface reads its round count from the environment instead.
ROUNDS_ENV = "CONSORTIUM_NUM_ROUNDS"
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


def load_rfp() -> tuple[str, str, list[Requirement]]:
    """Decompose the reference solicitation into typed requirements.

    ``as_of`` fixes the reference date for recency banding, so the same corpora give the
    same answer at rehearsal and on stage.
    """
    rfp = json.loads(RFP_PATH.read_text())
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


def run(grid: Grid, num_rounds: int, solicitation: str | None = None) -> Outcome:
    """Run the protocol to convergence or to ``num_rounds``, whichever comes first."""
    rfp_solicitation, as_of, requirements = load_rfp()
    requirements_json = json.dumps([r.__dict__ for r in requirements])

    covered: dict[str, list[Attestation]] = {r.id: [] for r in requirements}
    open_gaps: list[str] = []
    rounds_run = 0

    for server_round in range(1, num_rounds + 1):
        content = RecordDict(
            {
                "rfp": ConfigRecord({"requirements": requirements_json, "as_of": as_of}),
                # Round 1 broadcasts no gap. Later rounds carry it, and nothing else —
                # each firm re-queries its own library with a question it did not know
                # to ask, and the answer never travels in the other direction.
                "gap": ConfigRecord({"requirement_ids": ",".join(open_gaps)}),
            }
        )
        messages = [
            Message(
                content=content,
                message_type=MessageType.QUERY,
                dst_node_id=node_id,
                group_id=str(server_round),
            )
            for node_id in grid.get_node_ids()
        ]

        attestations = [
            a for reply in grid.send_and_receive(messages) for a in decode(reply.content)
        ]
        covered = {r.id: [] for r in requirements}
        for attestation in attestations:
            covered.setdefault(attestation.requirement_id, []).append(attestation)

        rounds_run = server_round
        previous_gaps, open_gaps = (
            open_gaps,
            [r.id for r in requirements if len(covered[r.id]) < r.min_count],
        )
        if not open_gaps or open_gaps == previous_gaps:
            # Either the gap closed, or re-examination found nothing new and another
            # identical broadcast would only cost time.
            break

    return Outcome(
        solicitation=solicitation or rfp_solicitation,
        requirements=requirements,
        covered=covered,
        rounds_run=rounds_run,
    )


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
