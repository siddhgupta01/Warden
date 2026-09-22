# ADR-0004: CI pipeline and pre-commit guardrails

Status: Accepted. Date: 2026-09-22. Milestone: M0.

## Context

The repo needs automated checks so quality and secret-safety do not depend on
remembering to run things by hand. Two layers make sense: local hooks that run
before a commit is recorded, and CI that runs on every push and pull request.

## Decision

Local: a pre-commit config with gitleaks (secret scanning), basic hygiene hooks
(end-of-file, trailing whitespace, merge-conflict markers, large files, private-
key detection), and the terraform hooks (fmt, validate, tflint).

CI (GitHub Actions): two jobs. One runs `terraform fmt -check -recursive` and
`terraform validate` on both modules with `-backend=false`. The other runs
gitleaks across full history. CI is the backstop if a local hook is skipped, and
the validate job is the real provider-schema validation gate, since it downloads
the AWS provider that the development sandbox could not reach.

## Why validate uses -backend=false

`terraform validate` checks configuration against provider schemas and does not
need credentials or a real backend. `-backend=false` lets `init` run without the
S3 backend existing, so validation works on a clean checkout with no AWS account.

## Why deep security scanners are deferred

tfsec and Checkov flag security issues by design, and `terraform/environment/`
contains deliberate misconfigurations as detection targets. Running them now
would produce a red build full of expected findings, which trains you to ignore
red. They are deferred to M6, where the intentional targets get annotated or
scoped so real findings are not masked. tflint stays because it checks
correctness (invalid values, deprecated syntax), not security posture, so it
stays green on the intentional targets.

## Consequences

Contributors install pre-commit once (`pip install pre-commit && pre-commit
install`). The CI badge in the README reflects fmt, validate, and secret-scan
status. When M6 adds signed images, SBOMs, and policy scanning, this workflow is
the place it extends.
