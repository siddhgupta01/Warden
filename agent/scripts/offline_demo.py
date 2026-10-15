"""Offline end-to-end demo.

Runs the whole Warden pipeline against a mocked AWS account (moto), with no real
AWS and no cost. Plants the same three misconfigurations the Terraform targets
create, then scans, reports, builds a dashboard, and writes a remediation plan.

    python agent/scripts/offline_demo.py

Outputs land in .warden/ (git-ignored).
"""

from __future__ import annotations

import os
import sys

# Make the package importable whether or not it is pip-installed.
_SRC = os.path.join(os.path.dirname(__file__), "..", "src")
sys.path.insert(0, os.path.abspath(_SRC))
_TESTS = os.path.join(os.path.dirname(__file__), "..", "tests")
sys.path.insert(0, os.path.abspath(_TESTS))

from moto import mock_aws  # noqa: E402

import conftest  # noqa: E402  (reuses the same planting helpers as the tests)
from warden_agent.dashboard import to_html  # noqa: E402
from warden_agent.engine import Engine  # noqa: E402
from warden_agent.remediation import pullrequest  # noqa: E402
from warden_agent.report import to_markdown  # noqa: E402
from warden_agent.scanner import CloudScanner  # noqa: E402

OUT = ".warden"


def main() -> int:
    os.environ.update(
        AWS_ACCESS_KEY_ID="testing",
        AWS_SECRET_ACCESS_KEY="testing",
        AWS_SESSION_TOKEN="testing",
        AWS_DEFAULT_REGION="us-east-1",
    )
    os.makedirs(OUT, exist_ok=True)

    with mock_aws():
        conftest._plant_s3()
        conftest._plant_security_groups()
        conftest._plant_iam()

        findings = Engine(scanner=CloudScanner(region="us-east-1")).run()

        print(f"Detected {len(findings)} finding(s):")
        for f in findings:
            print(f"  [{f.severity.value.upper()}] {f.title} :: {f.resource_id}")

        with open(os.path.join(OUT, "findings.md"), "w", encoding="utf-8") as fh:
            fh.write(to_markdown(findings))
        with open(os.path.join(OUT, "dashboard.html"), "w", encoding="utf-8") as fh:
            fh.write(to_html(findings))

        plan = pullrequest.build_plan(findings)
        if plan is not None:
            written = pullrequest.write_plan_locally(plan, os.path.join(OUT, "remediation"))
            print(f"\nRemediation plan (branch {plan.branch}):")
            for p in written:
                print(f"  {p}")

    print(f"\nReport, dashboard, and remediation written to {OUT}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
