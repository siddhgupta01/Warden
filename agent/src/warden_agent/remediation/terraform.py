"""Generate the minimal Terraform fix for a finding.

The agent never edits infrastructure directly. It proposes a change as Terraform
and (next milestone) opens it as a pull request for a human to review and merge.
This keeps remediation reviewable, reversible, and under human control.

Each proposal is a small, self-contained snippet with a comment explaining what
it fixes. The snippets are illustrative starting points for the PR, not a full
drop-in replacement for the existing resource blocks.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Finding


@dataclass(frozen=True)
class FixProposal:
    finding_id: str
    path: str
    content: str
    summary: str


def generate_fix(finding: Finding) -> FixProposal | None:
    kind = finding.id.split(":", 1)[0]
    if kind == "s3-public-access":
        return _fix_s3_public(finding)
    if kind == "sg-ssh-open":
        return _fix_sg_ssh_open(finding)
    if kind == "iam-privesc":
        return _fix_iam_privesc(finding)
    return None


def _fix_s3_public(finding: Finding) -> FixProposal:
    bucket = finding.resource_id
    content = f'''# Warden remediation for {finding.id}
# Re-enable S3 Block Public Access on the bucket.
resource "aws_s3_bucket_public_access_block" "{_slug(bucket)}" {{
  bucket = "{bucket}"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}
'''
    return FixProposal(
        finding_id=finding.id,
        path=f"terraform/remediation/{_slug(bucket)}_public_access_block.tf",
        content=content,
        summary="Enable all four S3 Block Public Access settings on the bucket.",
    )


def _fix_sg_ssh_open(finding: Finding) -> FixProposal:
    sg = finding.resource_id
    content = f'''# Warden remediation for {finding.id}
# Remove the 0.0.0.0/0 SSH ingress rule and scope SSH to a known admin CIDR.
# Delete the existing open ingress rule, then apply this scoped rule.
variable "admin_cidr" {{
  description = "CIDR allowed to reach SSH (set to your admin IP/range)."
  type        = string
}}

resource "aws_vpc_security_group_ingress_rule" "ssh_admin_only" {{
  security_group_id = "{sg}"
  description       = "SSH restricted to admin CIDR (Warden remediation)"
  ip_protocol       = "tcp"
  from_port         = 22
  to_port           = 22
  cidr_ipv4         = var.admin_cidr
}}
'''
    return FixProposal(
        finding_id=finding.id,
        path=f"terraform/remediation/{_slug(sg)}_ssh_scoped.tf",
        content=content,
        summary="Replace the open SSH rule with one scoped to an admin CIDR.",
    )


def _fix_iam_privesc(finding: Finding) -> FixProposal:
    user = finding.resource_id
    dangerous = finding.evidence.get("dangerous_actions", [])
    comment_lines = "\n".join(f"#   - {a}" for a in dangerous)
    content = f'''# Warden remediation for {finding.id}
# The user's policy grants privilege-escalation actions:
{comment_lines}
# Replace the over-privileged policy with a least-privilege, read-only baseline.
# Review and widen only to the specific actions this user actually needs.
data "aws_iam_policy_document" "{_slug(user)}_least_priv" {{
  statement {{
    sid       = "ReadOnlyBaseline"
    effect    = "Allow"
    actions   = ["ec2:Describe*", "s3:ListAllMyBuckets", "cloudwatch:GetMetricData"]
    resources = ["*"]
  }}
}}
'''
    return FixProposal(
        finding_id=finding.id,
        path=f"terraform/remediation/{_slug(user)}_least_privilege.tf",
        content=content,
        summary="Replace the privilege-escalation policy with a least-privilege baseline.",
    )


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name).strip("_").lower()
