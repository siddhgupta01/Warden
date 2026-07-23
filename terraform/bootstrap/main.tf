# ---------------------------------------------------------------------------
# Warden — remote-state backend bootstrap
#
# This module creates the S3 bucket and DynamoDB lock table that every OTHER
# Terraform module in this repo will use as its remote backend.
#
# It deliberately uses LOCAL state (no backend block below). You cannot store
# a module's state in a backend that does not exist yet — so this one module
# owns its own local state, and is applied exactly once, up front.
# ---------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Every resource Warden creates is tagged, so nothing is anonymous in the
  # console or in Cost Explorer. This matters for a security project: you can
  # always answer "what did this tool create, and can I find all of it?"
  default_tags {
    tags = {
      Project   = "warden"
      Component = "tf-backend"
      ManagedBy = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  # Bucket names are globally unique across ALL of AWS. Scoping the name to the
  # account ID + region avoids collisions without you having to invent one.
  state_bucket_name = coalesce(
    var.state_bucket_name,
    "warden-tfstate-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  )
}

# --- S3 bucket that holds Terraform state -----------------------------------

resource "aws_s3_bucket" "tfstate" {
  bucket = local.state_bucket_name

  # State is precious. Refuse to `terraform destroy` this bucket by accident;
  # tearing down the lab env must never be able to delete its own state store.
  lifecycle {
    prevent_destroy = true
  }
}

# Versioning lets you recover a previous state if an apply corrupts it.
resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encrypt state at rest. SSE-S3 (AES256) is $0 and needs no key management;
# state can contain secrets, so encryption-at-rest is non-negotiable.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Belt and braces: this bucket must never be public. Warden is a security
# project — a world-readable state bucket would be an embarrassing finding.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# --- DynamoDB table for state locking ---------------------------------------
# Prevents two applies from racing and corrupting state. PAY_PER_REQUEST means
# you pay per lock operation — effectively $0 at lab scale.
resource "aws_dynamodb_table" "tf_locks" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
