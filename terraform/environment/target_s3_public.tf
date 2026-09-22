# DELIBERATE MISCONFIGURATION: detection target, not a mistake.
#
# Finding:   S3 bucket does not block public access.
# Mapped to: CIS AWS 2.1.5, AWS FSBP S3.8, MITRE ATT&CK T1530.
# Purpose:   Warden (M1) detects this and opens a Terraform PR that re-enables
#            Block Public Access.
# Safety:    The bucket is created empty. Do not put real data in it. Account-
#            level S3 Block Public Access (on by default for new accounts) still
#            protects actual access unless you turn it off; see make_bucket_public.

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "public_target" {
  bucket = "${var.name_prefix}-public-target-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name          = "${var.name_prefix}-public-target"
    WardenTarget  = "true"
    WardenFinding = "s3-public-access"
  }
}

# The misconfig: every guard set to false. A secure bucket sets all four to true
# (as the bootstrap state bucket does).
resource "aws_s3_bucket_public_access_block" "public_target" {
  bucket = aws_s3_bucket.public_target.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Optional second stage: an actually-public bucket policy. Guarded by a flag,
# because account-level BPA rejects this at apply time on new accounts.
data "aws_iam_policy_document" "public_read" {
  count = var.make_bucket_public ? 1 : 0

  statement {
    sid       = "PublicRead"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.public_target.arn}/*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
  }
}

resource "aws_s3_bucket_policy" "public_read" {
  count  = var.make_bucket_public ? 1 : 0
  bucket = aws_s3_bucket.public_target.id
  policy = data.aws_iam_policy_document.public_read[0].json

  depends_on = [aws_s3_bucket_public_access_block.public_target]
}
