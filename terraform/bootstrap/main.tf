# Warden remote-state backend bootstrap.
#
# Creates the S3 bucket and DynamoDB lock table that every other Terraform
# module uses as its remote backend. This module deliberately uses local state:
# you cannot store a module's state in a backend that does not exist yet, so it
# owns its own local state and is applied once, up front.

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
  # Bucket names are globally unique. Scoping to account ID and region avoids
  # collisions without having to invent a name.
  state_bucket_name = coalesce(
    var.state_bucket_name,
    "warden-tfstate-${data.aws_caller_identity.current.account_id}-${var.aws_region}"
  )
}

resource "aws_s3_bucket" "tfstate" {
  bucket = local.state_bucket_name

  # Never destroy the state store by accident.
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

# Encrypt state at rest. SSE-S3 (AES256) is free and needs no key management.
resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# This bucket must never be public.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# State locking prevents two applies from racing. PAY_PER_REQUEST is effectively
# free at lab scale.
resource "aws_dynamodb_table" "tf_locks" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
