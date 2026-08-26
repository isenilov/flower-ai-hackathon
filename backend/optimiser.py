"""Minimum-disclosure optimiser: greedy weighted set cover.

Minimise total disclosure cost subject to every MANDATORY requirement being covered at
strength >= tau, and at most ``SECTION_F_CAP`` projects chosen.
"""
