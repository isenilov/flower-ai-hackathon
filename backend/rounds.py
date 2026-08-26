"""Run the federated protocol on the simulation runtime — one SuperNode per firm.

``flwr run .`` cannot do this any more. The FAB declares ``agentapp``, and the SuperLink
derives the task type from that alone (``_get_app_type``), so every ``flwr run`` of this
project starts the harness and ``--federation-config num-supernodes=N`` is accepted and
silently ignored. Hub also rejects a bundle carrying both surfaces, so the two cannot be
split back apart by declaring all three components.

The simulation runtime takes the apps directly and does not care what the FAB declares,
which makes this the honest way to get genuine per-node process isolation::

    uv run python -m backend.rounds --rounds 3 --supernodes 3
"""

import argparse
import os

from backend import protocol


def main() -> None:
    """Parse arguments and hand the two apps to the simulation runtime."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rounds", type=int, default=protocol.DEFAULT_ROUNDS)
    parser.add_argument("--supernodes", type=int, default=3)
    parser.add_argument(
        "--verbose", action="store_true", help="Show the simulation runtime's own logging"
    )
    args = parser.parse_args()

    # `run_simulation` hands the ServerApp an empty run_config and offers no way to seed
    # one, so the round count travels by environment.
    os.environ[protocol.ROUNDS_ENV] = str(args.rounds)

    # Imported here so `--help` does not pay for loading Ray.
    from flwr.simulation import run_simulation

    from backend.client_app import app as client_app
    from backend.server_app import app as server_app

    run_simulation(
        server_app=server_app,
        client_app=client_app,
        num_supernodes=args.supernodes,
        verbose_logging=args.verbose,
    )


if __name__ == "__main__":
    main()
