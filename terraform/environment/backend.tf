# Partial backend configuration.
#
# The s3 block is intentionally EMPTY here. The real values — the bucket name
# (which embeds your AWS account ID), region, and lock table — are supplied at
# init time from a local, git-ignored backend.hcl, so the account ID never
# lands in version control:
#
#   terraform init -backend-config=backend.hcl
#
# Copy backend.hcl.example -> backend.hcl and fill it in with the outputs the
# terraform/bootstrap module printed.
terraform {
  backend "s3" {}
}
