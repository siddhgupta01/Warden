"""Core data types shared across the agent.

A Finding is the single unit everything produces and consumes: detectors emit
them, the report renders them, and remediation reads them. Keeping it small and
immutable makes the whole pipeline easy to test and reason about.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Finding:
    """One security issue found in the account.

    Fields map to what a reviewer needs: what it is, where it is, how bad it is,
    which frameworks flag it, and the raw evidence that triggered it (so the
    finding is explainable, not a black box).
    """

    id: str
    title: str
    severity: Severity
    resource_type: str
    resource_id: str
    region: str
    description: str
    cis: tuple[str, ...] = ()
    mitre: tuple[str, ...] = ()
    evidence: dict = field(default_factory=dict)
    remediation_summary: str = ""

    def to_dict(self) -> dict:
        d = dataclasses.asdict(self)
        d["severity"] = self.severity.value
        return d
