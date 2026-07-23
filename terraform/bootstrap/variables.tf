variable "aws_region" {
  description = "AWS region for the Terraform state backend."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = <<-EOT
    Optional explicit name for the state bucket. Leave null to auto-generate
    a globally-unique name of the form
    warden-tfstate-<account-id>-<region>.
  EOT
  type        = string
  default     = null
}

variable "lock_table_name" {
  description = "Name of the DynamoDB table used for state locking."
  type        = string
  default     = "warden-tf-locks"
}
