variable "aws_region" {
  description = "AWS region for the Terraform state backend."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Optional explicit state bucket name. Leave null to auto-generate warden-tfstate-<account-id>-<region>."
  type        = string
  default     = null
}

variable "lock_table_name" {
  description = "Name of the DynamoDB table used for state locking."
  type        = string
  default     = "warden-tf-locks"
}
