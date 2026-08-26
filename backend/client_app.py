"""Firm node: local search, matcher agent, bander, and the BD approval gate.

The node-side half lives in :mod:`backend.firm_node` so that the published harness and
this federated surface answer a round identically — the harness reaches the same handler
through ``LocalGrid``, this module through a real SuperNode.
"""

from backend.firm_node import make_client_app

app = make_client_app()
