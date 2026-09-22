terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }
}

# Primary provider: where the Warden lab environment lives.
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "warden"
      Component = "lab-environment"
      ManagedBy = "terraform"
    }
  }
}

# Billing metrics (the AWS/Billing namespace) are only published in us-east-1,
# regardless of where resources run. This aliased provider lets the billing
# alarm live in us-east-1 even if the lab runs elsewhere.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project   = "warden"
      Component = "lab-environment"
      ManagedBy = "terraform"
    }
  }
}
