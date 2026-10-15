"""Engine: scan the account, run every detector, collect findings.

This is the orchestration seam. It owns the list of detectors and the order
findings come back in (most severe first), and nothing else.
"""

from __future__ import annotations

from .detectors import iam_privesc, s3_public, sg_ssh_open
from .models import Finding, Severity
from .scanner import CloudScanner, Facts

DETECTORS = [s3_public.detect, sg_ssh_open.detect, iam_privesc.detect]

_SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH: 1,
    Severity.MEDIUM: 2,
    Severity.LOW: 3,
}


class Engine:
    def __init__(self, scanner: CloudScanner | None = None, region: str = "us-east-1"):
        self.scanner = scanner or CloudScanner(region=region)

    def run(self) -> list[Finding]:
        facts = self.scanner.collect()
        return self.run_on(facts)

    @staticmethod
    def run_on(facts: Facts) -> list[Finding]:
        findings: list[Finding] = []
        for detect in DETECTORS:
            findings.extend(detect(facts))
        findings.sort(key=lambda f: _SEVERITY_ORDER[f.severity])
        return findings
