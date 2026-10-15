"""Command-line entry point.

    warden scan        scan AWS and print findings (table or --json)
    warden report      write a Markdown findings report
    warden dashboard   write a self-contained HTML dashboard
    warden plan-fix    print the proposed Terraform remediation for each finding
    warden remediate   open a remediation pull request (or write the plan locally)

Scanning runs against real AWS using your configured credentials. The test suite
exercises the same code against mocked AWS (moto), so you can develop with no
account.

Generated output (reports, dashboards, remediation files) can contain real
resource identifiers, so everything defaults into the git-ignored .warden/
directory. Do not commit those files to a public repo.
"""

from __future__ import annotations

import argparse
import os
import sys

from .dashboard import to_html
from .engine import Engine
from .remediation import pullrequest, terraform
from .report import to_json, to_markdown

WARDEN_DIR = ".warden"


def _scan(region: str):
    return Engine(region=region).run()


def _ensure_dir(path: str) -> None:
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="warden", description="Detect and remediate AWS security issues.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="scan AWS and print findings")
    p_scan.add_argument("--region", default="us-east-1")
    p_scan.add_argument("--json", action="store_true", help="output JSON instead of a table")

    p_report = sub.add_parser("report", help="write a Markdown findings report")
    p_report.add_argument("--region", default="us-east-1")
    p_report.add_argument("--out", default=f"{WARDEN_DIR}/findings.md")

    p_dash = sub.add_parser("dashboard", help="write a self-contained HTML dashboard")
    p_dash.add_argument("--region", default="us-east-1")
    p_dash.add_argument("--out", default=f"{WARDEN_DIR}/dashboard.html")

    p_fix = sub.add_parser("plan-fix", help="print Terraform remediation for findings")
    p_fix.add_argument("--region", default="us-east-1")

    p_rem = sub.add_parser("remediate", help="open a remediation PR, or write the plan locally")
    p_rem.add_argument("--region", default="us-east-1")
    p_rem.add_argument("--repo", help="owner/name of the repo to open the PR against")
    p_rem.add_argument("--base", default="main")
    p_rem.add_argument("--out", default=f"{WARDEN_DIR}/remediation", help="dry-run output directory")

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
        _ensure_dir(args.out)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(findings))
        print(f"Wrote {len(findings)} finding(s) to {args.out}")
        return 0

    if args.command == "dashboard":
        findings = _scan(args.region)
        _ensure_dir(args.out)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(to_html(findings))
        print(f"Wrote dashboard with {len(findings)} finding(s) to {args.out}")
        return 0

    if args.command == "plan-fix":
        for f in _scan(args.region):
            proposal = terraform.generate_fix(f)
            if proposal is None:
                continue
            print(f"# ---- {proposal.finding_id} -> {proposal.path} ----")
            print(proposal.content)
        return 0

    if args.command == "remediate":
        findings = _scan(args.region)
        plan = pullrequest.build_plan(findings)
        if plan is None:
            print("No remediable findings.")
            return 0

        token = os.environ.get("GITHUB_TOKEN")
        if args.repo and token:
            url = pullrequest.open_pull_request(plan, repo=args.repo, token=token, base=args.base)
            print(f"Opened pull request: {url}")
        else:
            written = pullrequest.write_plan_locally(plan, args.out)
            print("Dry run (set --repo and GITHUB_TOKEN to open a real PR).")
            print(f"Branch would be: {plan.branch}")
            for p in written:
                print(f"  wrote {p}")
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
