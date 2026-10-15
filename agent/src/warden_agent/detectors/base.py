"""Detector interface.

A detector is just a callable that takes the scanned Facts and returns a list of
Findings. Keeping them as plain functions (not classes) makes them trivial to
test and to add: write a function, add it to the engine's list.
"""

from __future__ import annotations

from typing import Protocol

from ..models import Finding
from ..scanner import Facts


class Detector(Protocol):
    def __call__(self, facts: Facts) -> list[Finding]: ...
