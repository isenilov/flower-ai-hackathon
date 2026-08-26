"""Coordinator: RFP decomposition, round orchestration, gap broadcast, SF330 assembly.

The federated surface. Same protocol as the published harness — see
:mod:`backend.protocol` — but over a real ``Grid``, one SuperNode per firm. Driven by
``backend.rounds`` (``make rounds``), which uses the simulation runtime rather than
``flwr run``: the FAB is an agentapp bundle now, so ``flwr run .`` starts the harness.
"""

from logging import INFO

from flwr.app import Context
from flwr.common.logger import log
from flwr.serverapp import Grid, ServerApp

from backend import protocol
from backend.trace import Trace

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Run the protocol: blind attestation, gap re-examination, disclosure."""
    num_rounds = protocol.resolve_rounds(context.run_config.get("num-rounds"))
    outcome = protocol.run(grid, num_rounds, trace=Trace())
    log(INFO, "\n%s", protocol.render(outcome))
