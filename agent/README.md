# Warden agent

The detection and remediation engine. It scans an AWS account, finds security
issues, maps each to CIS and MITRE ATT&CK, proposes a minimal Terraform fix, and
opens that fix as a pull request for a human to review.

## Design

The pipeline is small, separated pieces so each is easy to test and extend:

```
scanner -> Facts -> detectors -> Findings -> report / dashboard / remediation PR
```

- `scanner.py` is the only code that talks to AWS (via boto3). It returns a
  normalized `Facts` snapshot.
- `detectors/` are plain functions, one per issue class, that read `Facts` and
  return `Finding`s. Add a detector by writing a function and listing it in
  `engine.py`.
- `engine.py` runs every detector and sorts findings most-severe first.
- `report.py` renders findings as Markdown or JSON; `dashboard.py` renders a
  self-contained HTML dashboard.
- `remediation/terraform.py` turns a finding into a proposed Terraform fix, and
  `remediation/pullrequest.py` assembles those into a branch and opens a pull
  request. The agent never changes infrastructure and never merges.

The three detectors mirror the deliberate targets in `terraform/environment/`:
public S3 access, SSH open to the world, and an IAM privilege-escalation path.

## Why offline-first

The scanner uses ordinary boto3 calls, so the test suite runs the whole pipeline
against `moto` (an in-memory fake AWS). The agent is fully developed and tested
with no AWS account and no cost, and the same code runs unchanged against a real
account.

## Develop

```bash
cd agent
pip install -e ".[dev]"
pytest -q
```

## See it run with no AWS

```bash
python scripts/offline_demo.py
```

Plants the three misconfigurations in a mocked account, then writes a report,
dashboard, and remediation plan to `.warden/`.

## Run against real AWS

Requires configured AWS credentials (see ../docs/AWS-SETUP.md).

```bash
warden scan                 # print findings as a table
warden scan --json          # machine-readable
warden report               # Markdown report -> .warden/findings.md
warden dashboard            # HTML dashboard -> .warden/dashboard.html
warden plan-fix             # print proposed Terraform remediation
warden remediate --repo owner/name   # open a remediation PR (needs GITHUB_TOKEN)
```

Without `--repo` and `GITHUB_TOKEN`, `remediate` writes the plan to `.warden/`
for review instead of opening a PR.

## Output privacy

Generated output can contain real resource identifiers (bucket names, IAM user
names, security group IDs) when run against a real account. Everything defaults
into the git-ignored `.warden/` directory, and `.gitignore` also excludes the
common output filenames. Keep real-account reports and remediation PRs private;
use the synthetic lab for anything public.
