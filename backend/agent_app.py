"""Consortium — a collaborative disclosure harness, published as a Flower Agent.

This is the entry point published to Flower Hub and invoked from ``flwr chat``. The
protocol itself lives in :mod:`backend.protocol`; this module supplies the surface —
an operator's solicitation in, a coverage report out.

The AgentApp process gets no ``Grid``, so the round loop runs over
:class:`~backend.local_grid.LocalGrid` — one ``Context`` per firm, nothing but Flower
``Message`` objects crossing between them. ``backend.server_app`` drives the identical
protocol over a real grid.
"""

from logging import INFO

from flwr.agentapp import AgentApp, AgentSession
from flwr.app import Context, RecordDict
from flwr.common.logger import log

from backend import protocol
from backend.firm_node import FIRMS, make_client_app
from backend.local_grid import LocalGrid
from backend.trace import Trace

app = AgentApp()


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


@app.main()
def main(agent: AgentSession, context: Context) -> None:
    """Run the harness over the operator's solicitation and report coverage."""
    num_rounds = protocol.resolve_rounds(context.run_config.get("num-rounds"))
    num_firms = int(context.run_config.get("num-firms", len(FIRMS)))
    model = str(context.run_config.get("model", ""))
    operator_input = str(context.run_config.get("agent.input", "")).strip() or None

    # The session doubles as an event sink: `push_run_events` reaches every
    # `Control.StreamRunEvents` consumer, so `flwr chat` sees the same protocol events
    # the local visualisation reads. Absent on runtimes that do not offer it.
    scenario = protocol.resolve_scenario(context.run_config.get("scenario"))
    outcome = protocol.run(
        build_grid(num_firms),
        num_rounds,
        operator_input,
        trace=Trace(session=agent, scenario=scenario.slug),
        scenario=scenario,
    )
    log(
        INFO,
        "%s rounds, %s firms, %s open gaps",
        outcome.rounds_run,
        num_firms,
        len(outcome.open_gaps),
    )

    report = protocol.render(outcome)
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
