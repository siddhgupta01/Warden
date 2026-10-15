"""Render findings as JSON or Markdown.

JSON is for machines (CI, the future dashboard). Markdown is the human-readable
report that goes in a PR description or a docs page.
"""

from __future__ import annotations

import json

from .models import Finding


def to_json(findings: list[Finding]) -> str:
    return json.dumps([f.to_dict() for f in findings], indent=2)


def to_markdown(findings: list[Finding]) -> str:
    if not findings:
        return "# Warden findings\n\nNo issues detected.\n"

    lines = ["# Warden findings", "", f"{len(findings)} issue(s) detected.", ""]
    lines += ["| Severity | Title | Resource | Frameworks |", "|---|---|---|---|"]
    for f in findings:
        frameworks = ", ".join([*f.cis, *f.mitre]) or "-"
        lines.append(
            f"| {f.severity.value.upper()} | {f.title} | `{f.resource_id}` | {frameworks} |"
        )

    lines += ["", "## Details", ""]
    for f in findings:
        lines.append(f"### {f.severity.value.upper()}: {f.title}")
        lines.append("")
        lines.append(f"- Resource: `{f.resource_id}` ({f.resource_type}, {f.region})")
        if f.cis:
            lines.append(f"- CIS: {', '.join(f.cis)}")
        if f.mitre:
            lines.append(f"- MITRE ATT&CK: {', '.join(f.mitre)}")
        lines.append(f"- {f.description}")
        lines.append(f"- Fix: {f.remediation_summary}")
        lines.append("")
    return "\n".join(lines)
