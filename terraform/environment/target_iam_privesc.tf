# DELIBERATE MISCONFIGURATION: detection target, not a mistake.
#
# Finding:   An IAM principal that looks low-privilege ("dev") but holds a policy
#            that lets it escalate to administrator. This is the "two hops from
#            admin" path from the roadmap.
# Mapped to: MITRE ATT&CK T1098 (Account Manipulation), T1548 (Abuse Elevation
#            Control Mechanism); over-privilege per CSA "Overprivileged by Design".
# Purpose:   Warden (M1) models the account as a graph, flags the path to admin,
#            and opens a PR that right-sizes the policy.
#
# The escalation: with iam:AttachUserPolicy over "*", this user can attach the
# managed AdministratorAccess policy to itself, one API call from full admin.
# iam:CreatePolicyVersion + iam:SetDefaultPolicyVersion is a second, independent
# primitive (rewrite any managed policy's default version).
#
# Safety: no access keys and no console password are created, so the user has no
# usable credential. The dangerous policy is the finding; nothing can actually
# assume it until a credential is deliberately issued. Keep it that way.

resource "aws_iam_user" "dev" {
  name = "${var.name_prefix}-dev"

  tags = {
    WardenTarget  = "true"
    WardenFinding = "iam-privesc-to-admin"
  }
}

data "aws_iam_policy_document" "privesc" {
  # Escalation primitive 1: attach any managed policy to any user or role.
  statement {
    sid    = "AttachAnyPolicy"
    effect = "Allow"
    actions = [
      "iam:AttachUserPolicy",
      "iam:AttachRolePolicy",
    ]
    resources = ["*"]
  }

  # Escalation primitive 2: rewrite the default version of any managed policy.
  statement {
    sid    = "RewriteManagedPolicies"
    effect = "Allow"
    actions = [
      "iam:CreatePolicyVersion",
      "iam:SetDefaultPolicyVersion",
    ]
    resources = ["*"]
  }

  # Benign-looking read access that makes the role appear normal at a glance.
  # This is what makes the escalation easy to miss by eye.
  statement {
    sid    = "LooksLikeADevRole"
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "s3:ListAllMyBuckets",
      "cloudwatch:GetMetricData",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "privesc" {
  name        = "${var.name_prefix}-dev-overprivileged"
  description = "LAB TARGET: over-privileged policy with an IAM privesc path"
  policy      = data.aws_iam_policy_document.privesc.json
}

resource "aws_iam_user_policy_attachment" "dev_privesc" {
  user       = aws_iam_user.dev.name
  policy_arn = aws_iam_policy.privesc.arn
}
