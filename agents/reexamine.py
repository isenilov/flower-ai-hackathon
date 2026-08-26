"""Round-2 gap-directed re-query.

Local recompute informed by global state, iterated over rounds — the same primitive as
federated learning. The coordinator broadcasts the uncovered requirement; the agent asks
its own library a question round 1 gave it no reason to ask.
"""
