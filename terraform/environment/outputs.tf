# Identifiers for the lab targets, so later milestones and the demo can refer to
# them and you can eyeball what was created after an apply.

output "vpc_id" {
  description = "ID of the lab VPC."
  value       = aws_vpc.lab.id
}

output "public_bucket_name" {
  description = "Name of the deliberately public-access S3 target bucket."
  value       = aws_s3_bucket.public_target.bucket
}

output "ssh_open_security_group_id" {
  description = "ID of the security group with SSH open to the world."
  value       = aws_security_group.ssh_open.id
}

output "privesc_user_name" {
  description = "Name of the over-privileged dev IAM user (the privesc target)."
  value       = aws_iam_user.dev.name
}

output "privesc_policy_arn" {
  description = "ARN of the over-privileged policy attached to the dev user."
  value       = aws_iam_policy.privesc.arn
}

output "billing_alarm_name" {
  description = "Name of the estimated-charges CloudWatch alarm."
  value       = aws_cloudwatch_metric_alarm.estimated_charges.alarm_name
}

output "billing_sns_topic_arn" {
  description = "ARN of the SNS topic the billing alarm notifies."
  value       = aws_sns_topic.billing_alerts.arn
}
