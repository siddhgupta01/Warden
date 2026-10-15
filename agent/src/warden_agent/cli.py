"""Command-line entry point.

    warden scan       scan AWS and print findings (table or --json)
    warden report     write a Markdown findings report
    warden plan-fix   print the proposed Terraform remediation for each finding

These run against real AWS using your configured credentials. The test suite
exercises the same code against mocked AWS (moto), so you can develop without an
account.
"""

from __future__ import annotations

import argparse
import sys

from .engine import Engine
from .remediation import terraform
from .report import to_json, to_markdown


def _scan(region: str):
    return Engine(region=region).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="warden", description="Detect and remediate AWS security issues.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="scan AWS and print findings")
    p_scan.add_argument("--region", default="us-east-1")
    p_scan.add_argument("--json", action="store_true", help="output JSON instead of a table")

    p_report = sub.add_parser("report", help="write a Markdown findings report")
    p_report.add_argument("--region", default="us-east-1")
    p_report.add_argument("--out", default="findings.md")

    p_fix = sub.add_parser("plan-fix", help="print Terraform remediation for findings")
    p_fix.add_argument("--region", default="us-east-1")

    args = parser.parse_args(argv)

    if args.command == "scan":
        findings = _scan(args.region)
        if args.json:
            print(to_json(findings))
        else:
            if not findings:
                print("No issues detected.")
            for f in findings:
                frameworks = ", ".join([*f.cis, *f.mitre]) or "-"
                print(f"[{f.severity.value.upper():8}] {f.title} :: {f.resource_id} ({frameworks})")
        return 1 if findings else 0

    if args.command == "report":
        findings = _scan(args.region)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(findings))
        print(f"Wrote {len(findings)} finding(s) to {args.out}")
        return 0

    if args.command == "plan-fix":
        findings = _scan(args.region)
        for f in findings:
            proposal = terraform.generate_fix(f)
            if proposal is None:
                continue
            print(f"# ---- {proposal.finding_id} -> {proposal.path} ----")
            print(proposal.content)
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
