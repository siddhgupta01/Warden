# ---------------------------------------------------------------------------
# Cost guardrail: alert when estimated AWS charges cross the budget threshold.
#
# This is the first thing that should exist in any AWS account you're learning
# in. The Free Tier is now credit-based and can quietly draw down, so this
# alarm is the early-warning system that keeps a lab from becoming a surprise
# bill.
#
# The AWS/Billing metric is only emitted in us-east-1, so every resource here
# uses the aliased us_east_1 provider defined in providers.tf.
#
# One-time manual prerequisite: enable "Receive Billing Alerts" under
# Billing and Cost Management -> Billing preferences. AWS will not publish the
# EstimatedCharges metric until this is on. (It's a console toggle with no
# Terraform equivalent.)
# ---------------------------------------------------------------------------

resource "aws_sns_topic" "billing_alerts" {
  provider = aws.us_east_1
  name     = "${var.name_prefix}-billing-alerts"
}

# Create the email subscription only if an address was supplied, so a personal
# email never has to live in the committed code. Confirm the subscription from
# the email AWS sends before alerts will actually deliver.
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
  period             = 21600 # 6 hours — the billing metric only refreshes a few times a day
  evaluation_periods = 1

  threshold           = var.monthly_budget_usd
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"

  alarm_actions = [aws_sns_topic.billing_alerts.arn]
  ok_actions    = [aws_sns_topic.billing_alerts.arn]
}
