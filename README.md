# Warden

An autonomous AI agent that continuously finds and fixes security issues in an
AWS account, hardened so it cannot be turned into an attacker's foothold.

Warden detects cloud misconfigurations, IAM privilege-escalation paths, and
risky drift, then remediates them through reviewed Terraform pull requests. The
harder half of the project is containing the agent itself. Warden holds real
cloud credentials and acts on untrusted input (resource names, tags, alerts,
docs), which makes it a new kind of privileged principal. Securing it is the
point of the project.

Context: the Cloud Security Alliance reports that roughly one in eight reported
AI breaches is now linked to agentic systems. Warden is a hands-on response to
the OWASP Top 10 for Agentic Applications (2026) and the CSA finding that AI
agents are "overprivileged by design."

## Defense in depth: one agent, four containment layers

```
                 UNTRUSTED INPUT (tags, alerts, docs, resource names)
                                   |
                          [ WARDEN AGENT ]
                                   |
  Layer 4  APPLICATION   input validation, output schema, injection defenses, human approval
  Layer 3  SUPPLY CHAIN  signed image (Cosign), SBOM (Syft), Trivy gate, RAG provenance
  Layer 2  RUNTIME (K8s) ServiceAccount RBAC, NetworkPolicy egress, Pod Security Standards
  Layer 1  CLOUD (AWS)   short-lived least-priv IAM role, SCP guardrails, CloudTrail
                                   |
                         ACTS ON: AWS account (detect + remediate)
                                   |
                    META-DETECTION watches the agent's own behavior, kill switch
```

## What it does

Detection works at two levels. Outward, Warden finds cloud misconfigurations,
IAM privilege-escalation paths, and attack signals from CloudTrail and
GuardDuty, with every finding mapped to CIS and MITRE ATT&CK. Inward, and this
is the differentiating part, Warden runs meta-detection on itself: out-of-
allowlist API calls, unexpected egress, action spikes, and prompt-injection
attempts in its inputs.

Remediation goes beyond alerting. Warden generates the minimal Terraform fix and
opens it as a reviewed PR, right-sizes IAM from observed CloudTrail behavior,
and reverts drift to the known-good baseline. Everything runs under guardrails:
plan before apply, human approval, allow-listed actions, reversible-only
changes, and a kill switch.

## Milestone status

| # | Milestone | Status |
|---|-----------|--------|
| M0 | Foundation: repo hygiene, billing alarm, Terraform lab env, remote state | code complete (apply pending AWS account setup) |
| M1 | Detect and remediate MVP (agent opens a Terraform fix PR) | not started |
| M2 | Containerize and add K8s runtime containment | not started |
| M3 | Lock down identity (short-lived least-priv creds, blast-radius analysis) | not started |
| M4 | Attack the agent, then defend it (prompt-injection kill chain) | not started |
| M5 | Meta-detection and kill switch | not started |
| M6 | Supply chain and polish | not started |

## Repository layout

```
warden/
  terraform/
    bootstrap/          one-time: S3 state bucket + DynamoDB lock table
    environment/        the lab AWS env
      providers.tf          AWS provider + us-east-1 alias (billing metrics)
      backend.tf            partial S3 backend (account ID stays out of git)
      variables.tf
      billing_alarm.tf      estimated-charges alarm, the cost guardrail
      network.tf            minimal lab VPC
      target_s3_public.tf       intentional: S3 public-access finding
      target_sg_ssh_open.tf     intentional: SSH open to 0.0.0.0/0
      target_iam_privesc.tf     intentional: IAM privilege-escalation path
      outputs.tf
  docs/
    decisions/          architecture decision records (ADRs)
  LICENSE
```

Note: this repo intentionally contains insecure Terraform. The files under
`terraform/environment/` tagged `WardenTarget = "true"` are deliberate
detection targets for Warden to find and fix. They are not how the project
itself is written; the hardened baseline is in `terraform/bootstrap/`. See
docs/decisions/0003-deliberate-lab-targets.md.

## Getting started

The AWS environment is defined entirely in Terraform. Remote state has a
chicken-and-egg problem (the backend must exist before anything can use it), so
it is created once by a separate bootstrap module that uses local state.

```bash
# 1. Create the remote-state backend (run once, about $0/mo)
cd terraform/bootstrap
terraform init
terraform apply
terraform output          # note the bucket and lock table names

# 2. Stand up the lab environment against that backend
cd ../environment
cp backend.hcl.example backend.hcl     # edit with the outputs from step 1
terraform init -backend-config=backend.hcl
cp terraform.tfvars.example terraform.tfvars   # optional: set alarm_email
terraform apply

# Tear the lab down when idle (the backend from step 1 stays)
terraform destroy
```

Cost note: AWS's Free Tier changed on 2025-07-15 to a credit model. The billing
alarm is applied by the environment module, but AWS only emits the billing
metric after you enable "Receive Billing Alerts" once in the Billing console.
Run `terraform destroy` when idle. The backend (S3 and on-demand DynamoDB) and
the lab targets (no instances) cost effectively nothing at rest.

## License

MIT, see LICENSE.
