# ADR-0006: Remediation pull requests and output privacy

Status: Accepted. Date: 2026-10-15. Milestone: M1.

## Context

M1 finishes with the remediation side of the agent and a findings dashboard. A
security audit of the public repo also raised a real point: output the agent
generates from a real account (reports, dashboards, remediation files) contains
resource identifiers (bucket names, IAM user names, security group IDs). Those
are not secrets, but publishing an account's inventory in a public repo is
avoidable exposure. This ADR records how remediation works and how output is
kept out of git.

## Decisions

Remediation is a pull request, never a direct change. `remediation/pullrequest.py`
builds a plan (branch name, fix files, PR body) from findings. With a repo and a
`GITHUB_TOKEN` it opens a real PR through the GitHub REST API (create branch, add
files, open PR) for a human to review and merge. Without them it writes the plan
locally for inspection. The agent never merges and never applies.

Testability. Plan building, local writing, and the PR body are pure and unit-
tested. The GitHub call takes an injectable session, so the happy path and error
path are tested with a fake session, no network or token.

The dashboard is one self-contained HTML file. No external scripts or network,
works in light and dark, severity-colored. It is the demo artifact. All user-
supplied text is HTML-escaped (tested) so a crafted resource name cannot inject
markup.

Output privacy (audit response). Every generated artifact defaults into a git-
ignored `.warden/` directory, and `.gitignore` also excludes the common output
filenames (`findings.md`, `findings.json`, `dashboard.html`, and similar). So a
real-account report cannot be committed by accident. The operational rule, also
in the dashboard footer and the agent README, is: keep real-account reports and
remediation PRs private; use the synthetic lab for anything public.

## Consequences

The agent gains a `requests` dependency, used only for the live PR path. The
offline demo (`agent/scripts/offline_demo.py`) exercises the whole pipeline
against mocked AWS and writes to `.warden/`, so the end-to-end flow is runnable
and recordable with no account. Deeper identifier redaction (hashing resource
names in public artifacts) is a possible later refinement if real-account output
ever needs to be shared.
