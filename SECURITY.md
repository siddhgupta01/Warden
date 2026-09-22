# Security Policy

## Reporting a vulnerability

This is a personal learning and portfolio project. If you find a security issue,
please open a GitHub issue or contact the maintainer through the profile on the
repository. There is no formal SLA.

## Intentionally insecure code

This repository intentionally contains insecure infrastructure as code. The
files under `terraform/environment/` tagged `WardenTarget = "true"` are
deliberate misconfigurations used as detection targets for the Warden agent.
They are documented in `docs/decisions/0003-deliberate-lab-targets.md`.

These targets are inert until someone runs `terraform apply` with their own AWS
credentials. They contain no secrets and create no live credentials. Do not
deploy them in an account that holds real data.

## What this project protects against

Secrets never live in the repo. AWS credentials are read from the local AWS
credentials file or environment, never committed. Terraform state, `*.tfvars`,
`backend.hcl`, and `.env` are git-ignored. Commits are scanned by gitleaks both
locally (pre-commit) and in CI to block accidental secret exposure.
