"""Wire schema for federated bid assembly.

The privacy boundary is structural: an ``Attestation`` has no field that can carry a
client name, a fee, or a person's identity. Enforcement of the *values* lives in
``backend.bander``; this module fixes the *shape*.

Frozen at the 11:20 milestone — every other task depends on it.
"""

from dataclasses import dataclass, field
from typing import Literal

AssetKind = Literal["PROJECT", "PERSON"]
RequirementKind = Literal["MANDATORY", "WEIGHTED"]
Section = Literal["E", "F", "G"]

# Closed vocabulary. The bander rejects any banded key or value outside these sets.
VOCABULARY: dict[str, tuple[str, ...]] = {
    "value_band": ("0-10M", "10-50M", "50-100M", "100-250M", "250M+"),
    "recency_band": ("0-3y", "3-7y", "7y+"),
    "sector": ("healthcare", "education", "transport", "civic", "industrial", "defence"),
    "delivery": ("design-build", "design-bid-build", "cm-at-risk", "ipd"),
    "credentials": ("PMP", "SE", "PE", "AIA", "LEED-AP"),
    "client_type": ("federal", "state", "municipal", "private"),
    "certification": ("LEED-Silver", "LEED-Gold", "LEED-Platinum", "none"),
}

# Section F admits at most ten example projects. This cap is what turns disclosure
# into an optimisation problem instead of a dump.
SECTION_F_CAP = 10

NOTE_MAX_CHARS = 120


@dataclass(frozen=True)
class Requirement:
    """One typed line item decomposed from the solicitation."""

    id: str
    section: Section
    kind: RequirementKind
    predicate: dict[str, str]
    min_count: int = 1
    weight: float = 1.0
    description: str = ""


@dataclass
class Attestation:
    """Banded, anonymised evidence that a matching record exists.

    Never the record itself. Emitted by a firm node, consumed by the coordinator.
    """

    handle: str  # "FIRM_B::PERSON::007" — opaque, firm-local
    firm: str
    kind: AssetKind
    requirement_id: str
    match_strength: float  # 0-1
    banded: dict[str, str]  # keys and values restricted to VOCABULARY
    disclosure_cost: int  # 0 free | 1 NDA-limited | 2 sensitive | 3 blocked
    links: list[str] = field(default_factory=list)  # same-firm handles only
    note: str = ""  # <= NOTE_MAX_CHARS, passes the bander validator
