#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AWS Lambda Function for Monitoring Salary Tracker Application

ניטור אוטומטי של:
- מצב EC2 instance
- שימוש במשאבים (CPU, Memory)
- זמינות האפליקציה
- שגיאות בלוגים
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from typing import Dict, List

# AWS Clients
ec2 = boto3.client('ec2', region_name=os.getenv('AWS_REGION', 'us-east-1'))
cloudwatch = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', 'us-east-1'))
sns = boto3.client('sns', region_name=os.getenv('AWS_REGION', 'us-east-1'))
ssm = boto3.client('ssm', region_name=os.getenv('AWS_REGION', 'us-east-1'))


def get_ec2_instance_status() -> Dict:
    """בודק מצב EC2 instances"""
    try:
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': ['salary-tracker-server']},
                {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
            ]
        )
        
        instances = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instances.append({
                    'InstanceId': instance['InstanceId'],
                    'State': instance['State']['Name'],
                    'InstanceType': instance['InstanceType'],
                    'PublicIp': instance.get('PublicIpAddress', 'N/A'),
                    'LaunchTime': instance['LaunchTime'].isoformat()
                })
        
        return {
            'status': 'success',
            'instances': instances,
            'count': len(instances)
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def check_application_health(instance_id: str) -> Dict:
    """בודק בריאות האפליקציה דרך SSM"""
    try:
        # Try to run a health check command via SSM
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                'commands': [
                    'curl -f http://localhost:5000/api/health || echo "HEALTH_CHECK_FAILED"'
                ]
            }
        )
        
        command_id = response['Command']['CommandId']
        
        # Wait a bit and check result
        import time
        time.sleep(2)
        
        result = ssm.get_command_invocation(
            CommandId=command_id,
            InstanceId=instance_id
        )
        
        output = result.get('StandardOutputContent', '')
        is_healthy = 'HEALTH_CHECK_FAILED' not in output
        
        return {
            'status': 'success',
            'healthy': is_healthy,
            'output': output
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'healthy': False
        }


def get_cloudwatch_metrics(instance_id: str, metric_name: str, minutes: int = 15) -> Dict:
    """מביא מטריקות מ-CloudWatch"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'InstanceId', 'Value': instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,  # 5 minutes
            Statistics=['Average', 'Maximum']
        )
        
        datapoints = response.get('Datapoints', [])
        if datapoints:
            latest = max(datapoints, key=lambda x: x['Timestamp'])
            return {
                'status': 'success',
                'value': latest.get('Average', 0),
                'maximum': latest.get('Maximum', 0),
                'timestamp': latest['Timestamp'].isoformat()
            }
        else:
            return {
                'status': 'no_data',
                'message': 'No datapoints available'
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def send_alert(message: str, subject: str = "Salary Tracker Alert"):
    """שולח התראה דרך SNS (אם מוגדר)"""
    sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
    if not sns_topic_arn:
        return {'status': 'skipped', 'reason': 'SNS_TOPIC_ARN not configured'}
    
    try:
        response = sns.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject=subject
        )
        return {
            'status': 'success',
            'message_id': response['MessageId']
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }


def lambda_handler(event, context):
    """
    Lambda handler - נקרא אוטומטית על ידי CloudWatch Events
    """
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # 1. Check EC2 instances
    ec2_status = get_ec2_instance_status()
    results['checks']['ec2'] = ec2_status
    
    # 2. Check each instance
    if ec2_status['status'] == 'success' and ec2_status['instances']:
        for instance in ec2_status['instances']:
            instance_id = instance['InstanceId']
            
            # Check health if running
            if instance['State'] == 'running':
                health = check_application_health(instance_id)
                results['checks'][f'{instance_id}_health'] = health
                
                # Get metrics
                cpu_metrics = get_cloudwatch_metrics(instance_id, 'CPUUtilization')
                results['checks'][f'{instance_id}_cpu'] = cpu_metrics
                
                # Alert if CPU is high
                if cpu_metrics.get('status') == 'success' and cpu_metrics.get('value', 0) > 80:
                    send_alert(
                        f"High CPU usage detected on {instance_id}: {cpu_metrics.get('value')}%",
                        "High CPU Alert"
                    )
                
                # Alert if unhealthy
                if not health.get('healthy', True):
                    send_alert(
                        f"Application health check failed on {instance_id}",
                        "Health Check Failed"
                    )
    
    # Return results
    return {
        'statusCode': 200,
        'body': json.dumps(results, indent=2, default=str)
    }


# For local testing
if __name__ == "__main__":
    test_event = {}
    test_context = type('Context', (), {
        'function_name': 'test',
        'memory_limit_in_mb': 128,
        'invoked_function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:test'
    })()
    
    result = lambda_handler(test_event, test_context)
    print(json.dumps(json.loads(result['body']), indent=2))

