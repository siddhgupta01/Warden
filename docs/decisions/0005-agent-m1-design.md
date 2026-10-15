# ADR-0005: M1 detection and remediation agent design

Status: Accepted. Date: 2026-10-11. Milestone: M1.

## Context

M1 is the useful core of Warden: detect misconfigurations and an IAM privilege-
escalation path, and propose fixes as reviewed Terraform pull requests. The build
had to fit a short sprint, be defensible line by line, and not depend on a live
AWS account (the free credits are gone, and real spend should not gate progress).

## Decisions

Python, with a scanner/detector/engine separation. The scanner is the only code
that calls AWS; detectors are pure functions over a normalized `Facts` snapshot.
This seam is what makes everything testable.

Offline-first with moto. Because the scanner uses ordinary boto3 calls, the test
suite runs the entire pipeline against moto, an in-memory fake AWS. The agent is
fully developed and tested with no account and no cost, and the same code runs
unchanged against real AWS later.

Deterministic detectors before any LLM. The three detectors are rule-based and
fully unit-tested (positive and negative cases). An LLM is not needed to decide
whether a bucket blocks public access; that is a fact. The LLM layer (triage
narrative, PR descriptions, and reasoning over less clear-cut findings) is a
later addition on top of a correct, testable base.

Remediation as a proposal, never a direct change. The agent generates a minimal
Terraform fix per finding. It does not touch infrastructure. Fixes go out as pull
requests for human review, which keeps remediation reviewable, reversible, and
under human control. Automated PR creation via the GitHub API is the next step.

Findings map to frameworks. Every finding carries its CIS and MITRE ATT&CK
references and the raw evidence that triggered it, so a reviewer can see what was
found and why, and nothing is a black box.

## Consequences

The agent test suite runs in CI with no cloud credentials. Adding a detector is a
function plus a test. The remediation snippets are starting points for a PR, not
drop-in replacements for existing resource blocks, which is called out in the
code and will tighten as the PR workflow lands.
