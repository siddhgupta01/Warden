# ADR-0003: Deliberate misconfiguration targets for the lab environment

Status: Accepted. Date: 2026-07-23. Milestone: M0.

## Context

Warden's job, starting in M1, is to detect and remediate AWS security issues. To
build and demo that, the lab needs realistic, unambiguous problems to find. This
ADR records the three targets planted in `terraform/environment/`, why each was
chosen, and the rules that keep deliberately insecure IaC from being a real
liability.

Note: this repository intentionally contains insecure Terraform. The resources
below are detection targets, clearly tagged `WardenTarget = "true"`. They are not
representative of how the rest of the project is written; the hardened baseline
is in `terraform/bootstrap/`.

## The three targets

| File | Finding | Framework mapping |
|------|---------|-------------------|
| target_s3_public.tf | S3 bucket with Block Public Access disabled | CIS AWS 2.1.5, AWS FSBP S3.8, MITRE T1530 |
| target_sg_ssh_open.tf | Security group allows 22/tcp from 0.0.0.0/0 | CIS AWS 5.2, AWS FSBP EC2.13, MITRE T1021.004 |
| target_iam_privesc.tf | Dev user with a policy that escalates to admin | MITRE T1098, T1548, CSA "Overprivileged by Design" |

Two issue classes the roadmap calls for (a plain misconfig and an IAM privilege-
escalation path) are covered, with a third (network exposure) added because it is
cheap and demos well. Three targets done well, not twenty done shallowly.

## Why these choices

The S3 target defaults to "BPA disabled", not "fully public". AWS turns on
account-level S3 Block Public Access for new accounts, which rejects a public
bucket policy at apply time. Forcing a truly public bucket would either break
apply or require disabling an account-wide safety control. So the default finding
is the bucket-level BPA being off, a legitimate scanner-flagged CIS finding on
its own, and the fully-public policy is opt-in behind make_bucket_public.

The IAM target ships no credentials. The user has no access keys and no console
password, so nothing can actually use the escalation path until a credential is
deliberately issued. The over-privileged policy is the finding.

The SSH-open SG has no instance behind it. The open ingress rule is the finding;
a running host would add cost and real exposure for no extra detection value.

## Safety rules

Every target is tagged `WardenTarget = "true"` and `WardenFinding = "<slug>"` so
it is trivially identifiable and destroyable. Nothing here is exposed until you
run terraform apply; the files are inert code. The public bucket is created
empty. terraform destroy removes every target cleanly, which is the M0
done-criterion.

## Consequences

The repo carries a visible "intentionally insecure" note (README and this ADR) so
a reader never mistakes the targets for sloppy work. When supply-chain scanning
arrives in M6, these targets will trip tfsec and Checkov by design, so those
scans will be scoped or annotated so the intentional findings do not mask real
ones.
