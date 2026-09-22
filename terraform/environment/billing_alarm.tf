# Cost guardrail: alert when estimated AWS charges cross the budget threshold.
# This should be the first thing in any account you are learning in, since the
# credit-based Free Tier can draw down quietly.
#
# The AWS/Billing metric is only emitted in us-east-1, so these resources use
# the aliased us_east_1 provider.
#
# One-time manual step: enable "Receive Billing Alerts" under Billing and Cost
# Management, Billing preferences. AWS does not publish EstimatedCharges until
# this is on, and there is no Terraform equivalent for the toggle.

resource "aws_sns_topic" "billing_alerts" {
  provider = aws.us_east_1
  name     = "${var.name_prefix}-billing-alerts"
}

# Create the email subscription only if an address was supplied, so a personal
# email never has to live in committed code. Confirm the subscription from the
# email AWS sends before alerts deliver.
resource "aws_sns_topic_subscription" "billing_email" {
  count     = var.alarm_email == null ? 0 : 1
  provider  = aws.us_east_1
  topic_arn = aws_sns_topic.billing_alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "estimated_charges" {
  provider          = aws.us_east_1
  alarm_name        = "${var.name_prefix}-estimated-charges-over-${var.monthly_budget_usd}usd"
  alarm_description = "Estimated AWS charges exceeded $${var.monthly_budget_usd}."

  namespace   = "AWS/Billing"
  metric_name = "EstimatedCharges"
  dimensions = {
    Currency = "USD"
  }

  statistic          = "Maximum"
  period             = 21600 # 6 hours; the billing metric refreshes a few times a day
  evaluation_periods = 1

  threshold           = var.monthly_budget_usd
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.billing_alerts.arn]
  ok_actions    = [aws_sns_topic.billing_alerts.arn]
}
