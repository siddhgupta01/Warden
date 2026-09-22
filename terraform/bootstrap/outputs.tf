output "state_bucket" {
  description = "Name of the S3 bucket holding Terraform remote state."
  value       = aws_s3_bucket.tfstate.id
}

output "lock_table" {
  description = "Name of the DynamoDB state-lock table."
  value       = aws_dynamodb_table.tf_locks.name
}

output "region" {
  description = "Region the backend lives in."
  value       = var.aws_region
}

# Copy-paste-ready backend config for the environment module. The key is set
# per module, so it is left as a placeholder here.
output "backend_hcl" {
  description = "Backend configuration snippet for downstream modules."
  value       = <<-EOT
    bucket         = "${aws_s3_bucket.tfstate.id}"
    key            = "environment/terraform.tfstate"
    region         = "${var.aws_region}"
    dynamodb_table = "${aws_dynamodb_table.tf_locks.name}"
    encrypt        = true
  EOT
}
