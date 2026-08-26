"""Consortium — a collaborative disclosure harness, published as a Flower Agent.

The harness runs four stages over parties that are not allowed to pool their data::

    attest -> detect gap -> re-examine locally against the gap -> minimise disclosure

This module is the published entry point. It holds stages one and two and broadcasts the
gap that stage three consumes; SF330 bid assembly is the reference application supplied by
``data/rfp.json``.

The AgentApp process gets no ``Grid`` and cannot import the simulation runtime, so the
round loop runs over :class:`~backend.local_grid.LocalGrid` — one ``Context`` per firm,
nothing but Flower ``Message`` objects crossing between them.
"""

import json
from logging import INFO
from pathlib import Path

from flwr.agentapp import AgentApp, AgentSession
from flwr.app import ConfigRecord, Context, MessageType, RecordDict
from flwr.common.logger import log

from backend.firm_node import FIRMS, decode, make_client_app
from backend.local_grid import LocalGrid
from backend.schema import Attestation, Requirement

RFP_PATH = Path(__file__).resolve().parent.parent / "data" / "rfp.json"

app = AgentApp()


def load_requirements() -> tuple[str, list[Requirement]]:
    """Decompose the reference solicitation into typed requirements."""
    rfp = json.loads(RFP_PATH.read_text())
    return rfp["solicitation"], [Requirement(**item) for item in rfp["requirements"]]


def build_grid(num_firms: int) -> LocalGrid:
    """Stand up one firm node per party, each with its own isolated context."""
    contexts = {
        100 + partition_id: Context(
            run_id=0,
            node_id=100 + partition_id,
            node_config={"partition-id": partition_id, "num-partitions": num_firms},
            state=RecordDict(),
            run_config={},
        )
        for partition_id in range(num_firms)
    }
    return LocalGrid(make_client_app(), contexts)


def coverage(
    requirements: list[Requirement], attestations: list[Attestation]
) -> dict[str, list[Attestation]]:
    """Group attestations by requirement."""
    by_requirement: dict[str, list[Attestation]] = {r.id: [] for r in requirements}
    for attestation in attestations:
        by_requirement.setdefault(attestation.requirement_id, []).append(attestation)
    return by_requirement


def gaps(requirements: list[Requirement], covered: dict[str, list[Attestation]]) -> list[str]:
    """Requirements the consortium cannot yet evidence.

    This is the only thing broadcast back to the nodes: the gap, never the answer. Each
    firm re-queries its own library with a question it did not know to ask.
    """
    return [r.id for r in requirements if len(covered[r.id]) < r.min_count]


def render(
    solicitation: str,
    requirements: list[Requirement],
    covered: dict[str, list[Attestation]],
) -> str:
    """Render the coverage matrix as text.

    Text, not HTML: Hub's upload filter drops ``.html``/``.css``/``.js``, so a judge who
    installs this app from the Hub only ever sees what Python prints.
    """
    lines = [
        f"Solicitation: {solicitation}",
        "",
        f"{'REQ':<5} {'SEC':<4} {'KIND':<10} {'NEED':>5} {'HAVE':>5}  FIRMS  STATUS",
    ]
    for requirement in requirements:
        found = covered[requirement.id]
        firms = ",".join(sorted({a.firm.removeprefix("FIRM_") for a in found})) or "-"
        met = len(found) >= requirement.min_count
        lines.append(
            f"{requirement.id:<5} {requirement.section:<4} {requirement.kind:<10} "
            f"{requirement.min_count:>5} {len(found):>5}  {firms:<6} "
            f"{'ok' if met else 'GAP'}"
        )

    open_gaps = gaps(requirements, covered)
    mandatory_gaps = [r.id for r in requirements if r.kind == "MANDATORY" and r.id in open_gaps]
    lines += [
        "",
        "disclosed records: 0 (attestations only)",
        f"open gaps: {', '.join(open_gaps) or 'none'}",
        f"bid is {'NON-COMPLIANT' if mandatory_gaps else 'compliant'}"
        f"{' — mandatory: ' + ', '.join(mandatory_gaps) if mandatory_gaps else ''}",
    ]
    return "\n".join(lines)


@app.main()
def main(agent: AgentSession, context: Context) -> None:
    """Run the harness over the reference solicitation and report coverage."""
    num_rounds = int(context.run_config.get("num-rounds", 2))
    num_firms = int(context.run_config.get("num-firms", len(FIRMS)))
    model = str(context.run_config.get("model", ""))

    operator_input = str(context.run_config.get("agent.input", "")).strip()
    solicitation, requirements = load_requirements()
    if operator_input:
        solicitation = operator_input

    grid = build_grid(num_firms)
    requirements_json = json.dumps([r.__dict__ for r in requirements])

    covered: dict[str, list[Attestation]] = {r.id: [] for r in requirements}
    open_gaps: list[str] = []

    for server_round in range(1, num_rounds + 1):
        content = RecordDict(
            {
                "rfp": ConfigRecord({"requirements": requirements_json}),
                # Round 1 broadcasts no gap; later rounds carry it, and nothing else.
                "gap": ConfigRecord({"requirement_ids": ",".join(open_gaps)}),
            }
        )
        messages = [
            grid.create_message(
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
        covered = coverage(requirements, attestations)
        open_gaps = gaps(requirements, covered)
        log(
            INFO,
            "round %s: %s attestations from %s firms, %s open gaps",
            server_round,
            len(attestations),
            num_firms,
            len(open_gaps),
        )
        if not open_gaps:
            break

    report = render(solicitation, requirements, covered)
    log(INFO, "\n%s", report)

    if not model:
        return

    agent.responses.create(
        {
            "model": model,
            "instructions": (
                "You are reporting the result of a federated compliance check to a bid "
                "manager. Restate the coverage table verbatim inside a code block, then "
                "in at most four sentences say which requirements are unmet and what the "
                "consortium should do next. Do not invent numbers."
            ),
            "input": report,
            "stream": True,
        }
    )
