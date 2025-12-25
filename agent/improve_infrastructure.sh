#!/bin/bash
# -*- coding: utf-8 -*-
# סקריפט לשיפור תשתית AWS
# Script to improve AWS infrastructure

set -e

echo "=========================================="
echo "🔧 Improving AWS Infrastructure"
echo "=========================================="

cd "$(dirname "$0")/../infra"

# Check if Terraform is initialized
if [ ! -d ".terraform" ]; then
    echo "Initializing Terraform..."
    terraform init
fi

# Show what will be added
echo ""
echo "The following improvements will be added:"
echo "  ✓ CloudWatch Logs"
echo "  ✓ CloudWatch Alarms (CPU, Status)"
echo "  ✓ SNS Topic for alerts"
echo "  ✓ Lambda function for monitoring"
echo "  ✓ CloudWatch Events (scheduled monitoring)"
echo ""

read -p "Apply infrastructure improvements? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Apply CloudWatch and Lambda resources
terraform apply -target=aws_cloudwatch_log_group.app_logs
terraform apply -target=aws_sns_topic.alerts
terraform apply -target=aws_cloudwatch_metric_alarm.high_cpu
terraform apply -target=aws_cloudwatch_metric_alarm.instance_status
terraform apply -target=aws_iam_role.lambda_monitor_role
terraform apply -target=aws_iam_role_policy.lambda_monitor_policy
terraform apply -target=aws_lambda_function.monitor
terraform apply -target=aws_cloudwatch_event_rule.monitor_schedule
terraform apply -target=aws_cloudwatch_event_target.lambda_target
terraform apply -target=aws_lambda_permission.allow_cloudwatch

echo ""
echo "✅ Infrastructure improvements applied!"
echo ""
echo "Next steps:"
echo "  1. Package Lambda function:"
echo "     cd agent && zip lambda_monitor.zip lambda_monitor.py"
echo "  2. Upload to Lambda (or use Terraform with source_code_hash)"
echo "  3. Subscribe to SNS topic for alerts (optional)"
echo ""

