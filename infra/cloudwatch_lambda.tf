# ============================================
# CloudWatch & Lambda for Monitoring
# ניטור אוטומטי ושיפורים
# ============================================

# ===== CloudWatch Log Group =====
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/salary-tracker"
  retention_in_days = 7  # Free tier: 5GB storage, 7 days retention

  tags = {
    Name = "salary-tracker-logs"
  }
}

# ===== SNS Topic for Alerts =====
resource "aws_sns_topic" "alerts" {
  name = "salary-tracker-alerts"

  tags = {
    Name = "salary-tracker-alerts"
  }
}

# ===== CloudWatch Alarm - High CPU =====
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "salary-tracker-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors EC2 CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = aws_instance.web_server.id
  }

  tags = {
    Name = "salary-tracker-cpu-alarm"
  }
}

# ===== CloudWatch Alarm - Instance Status Check =====
resource "aws_cloudwatch_metric_alarm" "instance_status" {
  alarm_name          = "salary-tracker-instance-status"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "This metric monitors EC2 instance status checks"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    InstanceId = aws_instance.web_server.id
  }

  tags = {
    Name = "salary-tracker-status-alarm"
  }
}

# ===== IAM Role for Lambda =====
resource "aws_iam_role" "lambda_monitor_role" {
  name = "salary-tracker-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "salary-tracker-lambda-role"
  }
}

# ===== IAM Policy for Lambda =====
resource "aws_iam_role_policy" "lambda_monitor_policy" {
  name = "salary-tracker-lambda-policy"
  role = aws_iam_role.lambda_monitor_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:SendCommand",
          "ssm:GetCommandInvocation"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.alerts.arn
      }
    ]
  })
}

# ===== Lambda Function for Monitoring =====
resource "aws_lambda_function" "monitor" {
  filename         = "lambda_monitor.zip"
  function_name    = "salary-tracker-monitor"
  role            = aws_iam_role.lambda_monitor_role.arn
  handler         = "lambda_monitor.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 128

  environment {
    variables = {
      AWS_REGION    = "us-east-1"
      SNS_TOPIC_ARN = aws_sns_topic.alerts.arn
    }
  }

  source_code_hash = filebase64sha256("${path.module}/../agent/lambda_monitor.py")

  tags = {
    Name = "salary-tracker-monitor"
  }
}

# ===== CloudWatch Event Rule - Schedule =====
resource "aws_cloudwatch_event_rule" "monitor_schedule" {
  name                = "salary-tracker-monitor-schedule"
  description         = "Trigger monitoring every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Name = "salary-tracker-monitor-schedule"
  }
}

# ===== CloudWatch Event Target =====
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.monitor_schedule.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.monitor.arn
}

# ===== Lambda Permission =====
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monitor_schedule.arn
}

# ===== Outputs =====
output "sns_topic_arn" {
  description = "SNS Topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.monitor.arn
}

