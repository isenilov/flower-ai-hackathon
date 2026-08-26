"""Structured predicate prefilter over a firm's local library.

Runs before any model call: banded fields are matched exactly here so the model is only
ever asked about free-text bios on the shortlist.
"""
