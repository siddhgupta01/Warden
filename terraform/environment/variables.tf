variable "aws_region" {
  description = "Region for the Warden lab environment."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefix applied to resource names so every lab resource is easy to find (and destroy)."
  type        = string
  default     = "warden-lab"
}

variable "monthly_budget_usd" {
  description = "Dollar threshold for the estimated-charges CloudWatch alarm."
  type        = number
  default     = 20
}

variable "alarm_email" {
  description = <<-EOT
    Email address that receives the billing alarm. Left null by default so no
    personal email is ever committed. Set it in a git-ignored terraform.tfvars,
    or pass -var 'alarm_email=you@example.com' at apply time. When null, the SNS
    topic is still created but has no subscription.
  EOT
  type        = string
  default     = null
}
