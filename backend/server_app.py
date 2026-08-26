"""Coordinator: RFP decomposition, round orchestration, gap broadcast, SF330 assembly.

The federated surface. Same protocol as the published harness — see
:mod:`backend.protocol` — but over a real ``Grid``, one SuperNode per firm. Driven by
``backend.rounds`` (``make rounds``), which uses the simulation runtime rather than
``flwr run``: the FAB is an agentapp bundle now, so ``flwr run .`` starts the harness.
"""

import os
from logging import INFO

from flwr.app import Context
from flwr.common.logger import log
from flwr.serverapp import Grid, ServerApp

from backend import protocol
from backend.trace import Trace

# `run_simulation` seeds no run_config, so the simulation surface takes the model id from
# the environment the same way it takes the round count.
MODEL_ENV = "CONSORTIUM_MODEL"

app = ServerApp()


@app.main()
def main(grid: Grid, context: Context) -> None:
    """Run the protocol: blind attestation, gap re-examination, disclosure."""
    num_rounds = protocol.resolve_rounds(context.run_config.get("num-rounds"))
    scenario = protocol.resolve_scenario(context.run_config.get("scenario"))
    model_id = str(context.run_config.get("model", "") or os.environ.get(MODEL_ENV, ""))
    # On SuperGrid the JSONL sink is written inside a container and thrown away with it, so
    # a page on the operator's machine would follow a file nothing writes. `trace-to-log`
    # adds the sink that survives the trip — see `backend.trace`. Off by default: locally the
    # file is already right there, and the extra lines would only clutter the demo pane.
    to_log = str(context.run_config.get("trace-to-log", "")).strip().lower() in ("true", "1")
    outcome = protocol.run(
        grid,
        num_rounds,
        trace=Trace(scenario=scenario.slug, to_log=to_log),
        scenario=scenario,
        model_id=model_id,
    )
    log(INFO, "\n%s", protocol.render(outcome))
