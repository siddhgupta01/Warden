variable "aws_region" {
  description = "Region for the Warden lab environment."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to resource names so every lab resource is easy to find and destroy."
  type        = string
  default     = "warden-lab"
}

variable "monthly_budget_usd" {
  description = "Dollar threshold for the estimated-charges CloudWatch alarm."
  type        = number
  default     = 20
}

variable "alarm_email" {
  description = "Email that receives the billing alarm. Null by default so no personal email is committed. Set it in a git-ignored terraform.tfvars or pass -var at apply time. When null, the SNS topic has no subscription."
  type        = string
  default     = null
}

variable "make_bucket_public" {
  description = "When true, the S3 target also gets a public-read bucket policy. Defaults to false because new accounts enable account-level S3 Block Public Access, which rejects a public policy at apply time. With the flag off, the bucket still has its own Block Public Access disabled, which is itself a valid finding."
  type        = bool
  default     = false
}
