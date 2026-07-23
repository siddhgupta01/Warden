# ADR-0002 — Billing alarm as the first guardrail, and a partial S3 backend

**Status:** Accepted · **Date:** 2026-07-23 · **Milestone:** M0

## Context
Two things have to be true before Warden's lab environment is safe to stand up:
you must not get a surprise AWS bill, and you must not leak account identifiers
into a public GitHub repo. This ADR records how the environment module handles
both.

## Decision 1 — A billing alarm is the first resource, not an afterthought
The module ships a CloudWatch `EstimatedCharges` alarm (default threshold $20)
wired to an SNS topic, before any lab targets exist.

- **us-east-1 only.** The `AWS/Billing` metric is published exclusively in
  us-east-1 regardless of where resources run, so the alarm and its SNS topic
  use an aliased `aws.us_east_1` provider.
- **6-hour evaluation period.** The billing metric refreshes only a few times a
  day; a shorter period would just evaluate stale data.
- **Optional email subscription.** The subscribed email is a variable
  (`alarm_email`) that defaults to `null`. With no address set, the topic is
  created but has no subscriber — so a personal email never has to be committed.
- **Manual prerequisite documented.** AWS won't emit `EstimatedCharges` until
  "Receive Billing Alerts" is enabled in Billing preferences — a console toggle
  with no Terraform equivalent. Called out in the code so it isn't a silent gap.

Why this matters for the project's story: the new credit-based Free Tier draws
down quietly. A cost guardrail as resource #1 is exactly the discipline a
security/infra engineer is expected to show.

## Decision 2 — Partial backend config keeps the account ID out of git
Terraform's `backend "s3"` block cannot use variables, so the bucket name would
normally be hardcoded — and our bucket name embeds the AWS account ID.

Instead the backend block is left empty and the real values are passed at init
from a local, git-ignored `backend.hcl`:

```
terraform init -backend-config=backend.hcl
```

A committed `backend.hcl.example` documents the shape with placeholders, and
`.gitignore` blocks the real `backend.hcl` while allowing the `.example`. Result:
the repo can be public without disclosing the account ID.

## Consequences
- `terraform init` for this module requires the extra `-backend-config` flag.
  Documented in the README getting-started steps.
- Account ID stays private; anyone cloning the repo supplies their own via their
  own `backend.hcl`, which also makes the module reusable in a different account.
