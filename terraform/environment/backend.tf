# Partial backend configuration.
#
# The s3 block is intentionally empty. The real values (bucket name, which
# embeds the AWS account ID, region, and lock table) are supplied at init time
# from a local, git-ignored backend.hcl so the account ID never lands in
# version control:
#
#   terraform init -backend-config=backend.hcl
#
# Copy backend.hcl.example to backend.hcl and fill it in from the bootstrap
# module outputs.
terraform {
  backend "s3" {}
}
