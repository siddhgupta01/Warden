# Warden agent

The detection and remediation engine. It scans an AWS account, finds security
issues, maps each to CIS and MITRE ATT&CK, and proposes a minimal Terraform fix.

## Design

The pipeline is four small, separated pieces so each is easy to test and extend:

```
scanner  ->  Facts  ->  detectors  ->  Findings  ->  report / remediation
```

- `scanner.py` is the only code that talks to AWS (via boto3). It returns a
  normalized `Facts` snapshot.
- `detectors/` are plain functions, one per issue class, that read `Facts` and
  return `Finding`s. Add a detector by writing a function and listing it in
  `engine.py`.
- `engine.py` runs every detector and sorts findings most-severe first.
- `report.py` renders findings as Markdown or JSON.
- `remediation/terraform.py` turns a finding into a proposed Terraform fix. The
  agent never changes infrastructure directly; fixes go out as pull requests for
  a human to review (that PR step lands next).

The three detectors mirror the deliberate targets in `terraform/environment/`:
public S3 access, SSH open to the world, and an IAM privilege-escalation path.

## Why offline-first

The scanner uses ordinary boto3 calls, so the test suite runs the whole pipeline
against `moto` (an in-memory fake AWS). That means the agent is fully developed
and tested with no AWS account and no cost. The same code runs unchanged against
a real account.

## Develop

```bash
cd agent
pip install -e ".[dev]"
pytest -q
```

## Run against real AWS

Requires configured AWS credentials (see ../docs/AWS-SETUP.md).

```bash
warden scan                 # print findings as a table
warden scan --json          # machine-readable
warden report --out findings.md
warden plan-fix             # print proposed Terraform remediation
```
