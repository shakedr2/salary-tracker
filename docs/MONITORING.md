# 📊 Monitoring & Observability Guide

## Overview

This document describes the monitoring and observability features of the Salary Tracker application.

## Structured Logging

### CloudWatch-Compatible Logging

All application logs are structured in JSON format, ready for CloudWatch Logs:

```json
{
  "timestamp": "2025-01-15T10:30:00.123456",
  "level": "INFO",
  "logger": "backend.app",
  "message": "Salary refresh completed",
  "endpoint": "/api/refresh",
  "days_processed": 20,
  "total_salary": 15000.0
}
```

### Log Levels
- **INFO**: Normal operations, successful requests
- **WARNING**: Non-critical issues, missing data
- **ERROR**: Errors that don't stop the application
- **DEBUG**: Detailed debugging information

## Metrics

### Available Metrics

Access metrics at `/api/metrics`:

```bash
curl http://localhost:5000/api/metrics
```

#### Scraping Metrics
- `total_runs`: Total scraping attempts
- `successful_runs`: Successful scrapes
- `failed_runs`: Failed scrapes
- `avg_duration_seconds`: Average scraping time
- `total_records_scraped`: Total records collected

#### Calculation Metrics
- `total_calculations`: Number of calculations performed
- `total_days_processed`: Total days calculated
- `total_salary_calculated`: Total salary amount

#### API Metrics
- `total_requests`: Total API requests
- `health_checks`: Health check requests
- `salary_requests`: Salary data requests
- `refresh_requests`: Refresh requests
- `errors`: Total errors

#### Health Metrics
- `status`: Application status (healthy/unhealthy)
- `last_check`: Last health check timestamp
- `uptime_seconds`: Application uptime

## CloudWatch Integration

### Setting Up CloudWatch Logs

1. **Create Log Group:**
```bash
aws logs create-log-group --log-group-name /aws/ec2/salary-tracker
```

2. **Configure Log Stream:**
The application automatically sends logs to CloudWatch when running on EC2.

3. **View Logs:**
```bash
aws logs tail /aws/ec2/salary-tracker --follow
```

### CloudWatch Dashboard

#### Create Dashboard

1. Go to CloudWatch Console → Dashboards
2. Create new dashboard: "Salary-Tracker-Monitoring"

#### Recommended Widgets

**1. Application Health**
- Metric: Custom metric from `/api/health`
- Widget: Number widget
- Alarm: Alert if status != "ok"

**2. Scraping Success Rate**
- Metric: `scraping.successful_runs / scraping.total_runs`
- Widget: Line graph
- Alarm: Alert if success rate < 80%

**3. API Request Count**
- Metric: `api.total_requests`
- Widget: Line graph
- Time range: Last 24 hours

**4. Error Rate**
- Metric: `api.errors / api.total_requests`
- Widget: Line graph
- Alarm: Alert if error rate > 5%

**5. Average Scraping Duration**
- Metric: `scraping.avg_duration_seconds`
- Widget: Line graph
- Alarm: Alert if duration > 60 seconds

**6. Total Salary Calculated**
- Metric: `calculations.total_salary_calculated`
- Widget: Number widget
- Time range: Last 30 days

### CloudWatch Alarms

#### High CPU Usage
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name salary-tracker-high-cpu \
  --alarm-description "Alert on high CPU usage" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

#### Application Errors
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name salary-tracker-errors \
  --alarm-description "Alert on high error rate" \
  --metric-name ErrorRate \
  --namespace SalaryTracker \
  --statistic Average \
  --period 300 \
  --threshold 0.05 \
  --comparison-operator GreaterThanThreshold
```

## Lambda Monitoring

The `agent/lambda_monitor.py` Lambda function provides automated monitoring:

### Features
- Checks EC2 instance status every 5 minutes
- Monitors application health via SSM
- Collects CloudWatch metrics
- Sends SNS alerts on issues

### Setup

1. **Package Lambda:**
```bash
cd agent
zip lambda_monitor.zip lambda_monitor.py
```

2. **Deploy via Terraform:**
```bash
cd infra
terraform apply
```

3. **Or deploy manually:**
```bash
aws lambda create-function \
  --function-name salary-tracker-monitor \
  --runtime python3.9 \
  --role arn:aws:iam::ACCOUNT:role/lambda-monitor-role \
  --handler lambda_monitor.lambda_handler \
  --zip-file fileb://lambda_monitor.zip
```

## SNS Alerts

### Subscribe to Alerts

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT:salary-tracker-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

### Alert Types
- High CPU usage (>80%)
- Instance status check failures
- Application health check failures
- Scraping failures

## Performance Monitoring

### Using Decorators

The application includes performance monitoring decorators:

```python
from backend.observability import monitor_performance

@monitor_performance("operation_name")
def my_function():
    # Your code
    pass
```

### Using Context Managers

```python
from backend.observability import time_operation, get_structured_logger

logger = get_structured_logger(__name__)

with time_operation("scraping", logger):
    # Your code
    scrape_data()
```

## Best Practices

1. **Log Levels**: Use appropriate log levels
   - INFO for normal operations
   - WARNING for recoverable issues
   - ERROR for failures

2. **Structured Data**: Always include context in logs
   ```python
   logger.info("Operation completed", 
               operation="scraping",
               records_count=20,
               duration_seconds=5.2)
   ```

3. **Metrics**: Update metrics after operations
   ```python
   metrics.record_scraping(duration, records_count, success=True)
   ```

4. **Alarms**: Set up alarms for critical metrics
   - Application health
   - Error rates
   - Performance degradation

## Troubleshooting

### Logs Not Appearing in CloudWatch
- Check IAM permissions for EC2 instance
- Verify log group exists
- Check CloudWatch Logs agent is running

### Metrics Not Updating
- Verify `/api/metrics` endpoint is accessible
- Check application is running
- Review application logs for errors

### Alarms Not Triggering
- Verify alarm configuration
- Check SNS topic subscriptions
- Review CloudWatch metrics data

