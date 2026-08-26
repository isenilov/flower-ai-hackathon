"""Egress validator and outbound byte counter.

Every attestation leaving a firm node passes through here. The bander rejects rather
than sanitises: an unknown banded key is an error, not something to drop quietly, so a
matcher that invents a field fails loudly at the boundary instead of leaking through it.
"""
