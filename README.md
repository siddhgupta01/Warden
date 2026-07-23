# Warden

> **An autonomous AI agent that continuously finds and fixes security issues in an AWS account — and that I hardened so it can't be turned into the attacker's foothold.**

Warden detects cloud misconfigurations, IAM privilege-escalation paths, and risky drift, then remediates them via reviewed Terraform pull requests. The harder, rarer half of the project is **containing the agent itself**: Warden holds real cloud credentials *and* acts on untrusted input (resource names, tags, alerts, docs), which makes it a new kind of privileged principal. Securing it is the whole point.

> **Why now:** the Cloud Security Alliance reports that **1 in 8 reported AI breaches is now linked to agentic systems.** Warden is a hands-on answer to the [OWASP Top 10 for Agentic Applications (2026)](https://genai.owasp.org/) and the CSA finding that AI agents are *"overprivileged by design."*

---

## Defense in depth — one powerful agent, four containment layers

```
                 UNTRUSTED INPUT (tags, alerts, docs, resource names)
                                   |
                          [ WARDEN AGENT ]
                                   |
  Layer 4  APPLICATION   input validation · output schema · injection defenses · human approval
  Layer 3  SUPPLY CHAIN  signed image (Cosign) · SBOM (Syft) · Trivy gate · RAG provenance
  Layer 2  RUNTIME (K8s) ServiceAccount RBAC · NetworkPolicy egress · Pod Security Standards
  Layer 1  CLOUD (AWS)   short-lived least-priv IAM role (BYOSA) · SCP guardrails · CloudTrail
                                   |
                         ACTS ON  ->  AWS account  (detect + remediate)
                                   |
                    META-DETECTION watches the agent's own behavior -> kill switch
```

## What it does

**Detection — two levels**
- *Outward (Warden's job):* cloud misconfigurations, IAM privilege-escalation paths (blast-radius graph), and attack signals from CloudTrail + GuardDuty. Every finding mapped to CIS + MITRE ATT&CK.
- *Inward (the differentiator):* **meta-detection** of Warden itself — out-of-allowlist API calls, unexpected egress, action spikes, and prompt-injection attempts in its inputs.

**Remediation — not just alerting**
- Generates the minimal Terraform fix and opens it as a reviewed PR.
- Right-sizes IAM from observed CloudTrail behavior (over-permissioned role → least-privilege policy).
- Reverts drift to the known-good IaC baseline.
- All under guardrails: plan-before-apply, human approval, allow-listed actions, reversible-only changes, kill switch.

---

## Milestone status

| # | Milestone | Status |
|---|-----------|--------|
| M0 | Foundation — repo hygiene, billing alarm, Terraform lab env + remote state | 🟡 in progress |
| M1 | Detect + remediate MVP (agent opens a Terraform fix PR) | ⬜ not started |
| M2 | Containerize + K8s runtime containment | ⬜ not started |
| M3 | Lock down identity (short-lived least-priv creds, blast-radius analysis) | ⬜ not started |
| M4 | Attack the agent, then defend it (prompt-injection kill chain) | ⬜ not started |
| M5 | Meta-detection + kill switch | ⬜ not started |
| M6 | Supply chain + polish | ⬜ not started |

---

## Repository layout

```
warden/
├── terraform/
│   ├── bootstrap/     # one-time: creates the S3 state bucket + DynamoDB lock table
│   └── environment/   # the lab AWS env (targets + billing alarm) — added in M0 part 2
├── docs/
│   └── decisions/     # architecture decision records (ADRs)
└── ...
```

## Getting started

Warden's AWS environment is defined entirely in Terraform. Remote state has a
chicken-and-egg problem — the backend must exist before anything can use it —
so it's created once by a separate `bootstrap` module using local state.

```bash
# 1. Create the remote-state backend (run once, ~$0/mo)
cd terraform/bootstrap
terraform init
terraform apply

# 2. (next step) Stand up the lab environment against that backend
#    cd ../environment && terraform init && terraform apply
```

> ⚠️ **Cost note.** AWS's Free Tier changed on 2025-07-15 to a credit model.
> Set a billing alarm before creating anything, and run `terraform destroy` when
> idle. The backend (S3 + on-demand DynamoDB) costs effectively nothing at rest.

## License

MIT — see [LICENSE](./LICENSE).
