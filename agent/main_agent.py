#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סוכן אוטומטי לבדיקה ושיפור התוכנה
Automated Agent for Software Quality Checks and Improvements

מבצע:
- בדיקות איכות קוד
- בדיקות אבטחה
- בדיקות ביצועים
- בדיקות תשתית AWS
- שיפורים אוטומטיים
"""

import os
import sys
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    BotoCoreError = Exception

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent/agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class QualityChecker:
    """בודק איכות קוד"""
    
    def __init__(self):
        self.issues = []
        self.improvements = []
    
    def check_python_syntax(self) -> Tuple[bool, List[str]]:
        """בודק תחביר Python"""
        logger.info("Checking Python syntax...")
        issues = []
        
        python_files = list(BASE_DIR.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f) and "__pycache__" not in str(f)]
        
        for py_file in python_files:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    issues.append(f"Syntax error in {py_file}: {result.stderr}")
            except Exception as e:
                issues.append(f"Error checking {py_file}: {e}")
        
        if issues:
            self.issues.extend(issues)
            return False, issues
        return True, []
    
    def check_imports(self) -> Tuple[bool, List[str]]:
        """בודק imports חסרים"""
        logger.info("Checking imports...")
        issues = []
        
        try:
            # Try to import main modules
            sys.path.insert(0, str(BASE_DIR))
            from backend import app, calculator, scraper, config
            logger.info("All imports successful")
        except ImportError as e:
            issues.append(f"Import error: {e}")
            self.issues.append(f"Import error: {e}")
            return False, issues
        
        return True, []
    
    def check_security(self) -> Tuple[bool, List[str]]:
        """בודק בעיות אבטחה בסיסיות"""
        logger.info("Checking security issues...")
        issues = []
        
        # Check for hardcoded credentials
        sensitive_patterns = [
            ("password", "="),
            ("secret", "="),
            ("api_key", "="),
            ("token", "="),
        ]
        
        python_files = list(BASE_DIR.rglob("*.py"))
        python_files = [f for f in python_files if "venv" not in str(f) and "agent" not in str(f)]
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern, operator in sensitive_patterns:
                    if pattern in content.lower() and operator in content:
                        # Check if it's in a comment or string literal (basic check)
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if pattern in line.lower() and operator in line:
                                # Skip if it's clearly a comment or env var usage
                                if not line.strip().startswith('#') and 'os.getenv' not in line:
                                    issues.append(f"Potential hardcoded credential in {py_file}:{i}")
            except Exception as e:
                logger.warning(f"Error checking {py_file}: {e}")
        
        if issues:
            self.issues.extend(issues)
            return False, issues
        return True, []
    
    def check_requirements(self) -> Tuple[bool, List[str]]:
        """בודק שהתלויות מותקנות"""
        logger.info("Checking requirements...")
        issues = []
        
        if not (BASE_DIR / "requirements.txt").exists():
            issues.append("requirements.txt not found")
            return False, issues
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                issues.append(f"Package conflicts: {result.stdout}")
        except Exception as e:
            logger.warning(f"Could not check packages: {e}")
        
        if issues:
            self.issues.extend(issues)
            return False, issues
        return True, []
    
    def run_tests(self) -> Tuple[bool, Dict]:
        """מריץ בדיקות"""
        logger.info("Running tests...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(BASE_DIR)
            )
            
            test_results = {
                "passed": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr
            }
            
            if result.returncode != 0:
                self.issues.append(f"Tests failed: {result.stderr}")
            
            return result.returncode == 0, test_results
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False, {"error": str(e)}


class AWSInfrastructureChecker:
    """בודק תשתית AWS"""
    
    def __init__(self):
        self.aws_issues = []
        self.aws_improvements = []
        if not AWS_AVAILABLE:
            logger.warning("boto3 not installed - AWS checks will be skipped")
            self.ec2 = None
            self.cloudwatch = None
            self.ssm = None
            return
        
        try:
            self.ec2 = boto3.client('ec2', region_name='us-east-1')
            self.cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
            self.ssm = boto3.client('ssm', region_name='us-east-1')
        except Exception as e:
            logger.warning(f"AWS credentials not configured: {e}")
            self.ec2 = None
            self.cloudwatch = None
            self.ssm = None
    
    def check_ec2_instances(self) -> Tuple[bool, List[Dict]]:
        """בודק מצב EC2 instances"""
        logger.info("Checking EC2 instances...")
        
        if not self.ec2 or not AWS_AVAILABLE:
            return False, [{"error": "AWS credentials not configured or boto3 not installed"}]
        
        try:
            response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': ['salary-tracker-server']}
                ]
            )
            
            instances = []
            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instances.append({
                        "id": instance['InstanceId'],
                        "state": instance['State']['Name'],
                        "type": instance['InstanceType'],
                        "public_ip": instance.get('PublicIpAddress', 'N/A'),
                        "tags": {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
            
            if not instances:
                self.aws_issues.append("No EC2 instances found with tag 'salary-tracker-server'")
                return False, []
            
            # Check if instances are running
            running = [i for i in instances if i['state'] == 'running']
            if not running:
                self.aws_issues.append("No running EC2 instances found")
                return False, instances
            
            return True, instances
        except ClientError as e:
            error_msg = f"AWS error checking EC2: {e}"
            logger.error(error_msg)
            self.aws_issues.append(error_msg)
            return False, [{"error": error_msg}]
    
    def check_security_groups(self) -> Tuple[bool, List[Dict]]:
        """בודק Security Groups"""
        logger.info("Checking Security Groups...")
        
        if not self.ec2 or not AWS_AVAILABLE:
            return False, [{"error": "AWS credentials not configured or boto3 not installed"}]
        
        try:
            response = self.ec2.describe_security_groups(
                Filters=[
                    {'Name': 'tag:Name', 'Values': ['salary-tracker-sg']}
                ]
            )
            
            sgs = []
            for sg in response.get('SecurityGroups', []):
                # Check for overly permissive rules
                issues = []
                for rule in sg.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        if ip_range.get('CidrIp') == '0.0.0.0/0':
                            if rule.get('FromPort') in [22, 80, 443]:
                                issues.append(f"Open port {rule.get('FromPort')} to 0.0.0.0/0")
                
                sgs.append({
                    "id": sg['GroupId'],
                    "name": sg['GroupName'],
                    "issues": issues
                })
                
                if issues:
                    self.aws_issues.extend(issues)
            
            return len([s for s in sgs if s['issues']]) == 0, sgs
        except ClientError as e:
            error_msg = f"AWS error checking Security Groups: {e}"
            logger.error(error_msg)
            return False, [{"error": error_msg}]
    
    def suggest_improvements(self) -> List[str]:
        """מציע שיפורים לתשתית AWS"""
        improvements = []
        
        improvements.append("Add CloudWatch alarms for CPU and memory usage")
        improvements.append("Enable CloudWatch Logs for application logs")
        improvements.append("Add Auto Scaling Group for high availability")
        improvements.append("Use Application Load Balancer for better distribution")
        improvements.append("Add S3 bucket for backup storage")
        improvements.append("Enable CloudWatch metrics for application health")
        improvements.append("Add Lambda function for automated backups")
        improvements.append("Use Systems Manager for secure access instead of SSH")
        
        return improvements


class CodeImprover:
    """משפר קוד אוטומטית"""
    
    def __init__(self):
        self.improvements_made = []
    
    def add_missing_docstrings(self) -> List[str]:
        """מוסיף docstrings חסרים"""
        logger.info("Adding missing docstrings...")
        improvements = []
        
        # This would require AST parsing - simplified version
        # For now, just log what could be improved
        improvements.append("Consider adding docstrings to all functions")
        
        return improvements
    
    def optimize_imports(self) -> List[str]:
        """מסדר imports"""
        logger.info("Optimizing imports...")
        improvements = []
        
        # Check for unused imports (simplified)
        improvements.append("Consider using tools like 'isort' and 'autoflake' to organize imports")
        
        return improvements
    
    def add_error_handling(self) -> List[str]:
        """מוסיף טיפול בשגיאות"""
        logger.info("Adding error handling...")
        improvements = []
        
        # Check for missing try-except blocks in critical areas
        improvements.append("Review error handling in scraper.py for better resilience")
        
        return improvements


class AutomatedAgent:
    """סוכן ראשי לבדיקה ושיפור אוטומטי"""
    
    def __init__(self):
        self.quality_checker = QualityChecker()
        self.aws_checker = AWSInfrastructureChecker()
        self.improver = CodeImprover()
        self.report = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "issues": [],
            "improvements": [],
            "aws_status": {}
        }
    
    def run_all_checks(self) -> Dict:
        """מריץ את כל הבדיקות"""
        logger.info("=" * 60)
        logger.info("Starting Automated Quality Checks")
        logger.info("=" * 60)
        
        # Code Quality Checks
        logger.info("\n[1/6] Code Quality Checks")
        syntax_ok, syntax_issues = self.quality_checker.check_python_syntax()
        self.report["checks"]["syntax"] = {"passed": syntax_ok, "issues": syntax_issues}
        
        imports_ok, import_issues = self.quality_checker.check_imports()
        self.report["checks"]["imports"] = {"passed": imports_ok, "issues": import_issues}
        
        security_ok, security_issues = self.quality_checker.check_security()
        self.report["checks"]["security"] = {"passed": security_ok, "issues": security_issues}
        
        requirements_ok, req_issues = self.quality_checker.check_requirements()
        self.report["checks"]["requirements"] = {"passed": requirements_ok, "issues": req_issues}
        
        # Tests
        logger.info("\n[2/6] Running Tests")
        tests_ok, test_results = self.quality_checker.run_tests()
        self.report["checks"]["tests"] = {"passed": tests_ok, "results": test_results}
        
        # AWS Infrastructure Checks
        logger.info("\n[3/6] AWS Infrastructure Checks")
        ec2_ok, ec2_info = self.aws_checker.check_ec2_instances()
        self.report["aws_status"]["ec2"] = {"ok": ec2_ok, "instances": ec2_info}
        
        sg_ok, sg_info = self.aws_checker.check_security_groups()
        self.report["aws_status"]["security_groups"] = {"ok": sg_ok, "groups": sg_info}
        
        # Collect all issues
        self.report["issues"] = (
            self.quality_checker.issues +
            self.aws_checker.aws_issues
        )
        
        # Get improvement suggestions
        logger.info("\n[4/6] Generating Improvement Suggestions")
        aws_improvements = self.aws_checker.suggest_improvements()
        code_improvements = self.improver.add_missing_docstrings()
        
        self.report["improvements"] = aws_improvements + code_improvements
        
        # Summary
        logger.info("\n[5/6] Generating Summary")
        total_checks = len([k for k, v in self.report["checks"].items() if v.get("passed", False)])
        total_issues = len(self.report["issues"])
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Summary:")
        logger.info(f"  Checks Passed: {total_checks}/{len(self.report['checks'])}")
        logger.info(f"  Issues Found: {total_issues}")
        logger.info(f"  Improvements Suggested: {len(self.report['improvements'])}")
        logger.info(f"{'='*60}\n")
        
        return self.report
    
    def save_report(self, filename: str = "agent/report.json"):
        """שומר דוח"""
        report_path = BASE_DIR / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to {report_path}")
    
    def apply_improvements(self):
        """מחיל שיפורים אוטומטיים (כאשר אפשר)"""
        logger.info("\n[6/6] Applying Automatic Improvements")
        
        # This would apply safe, automatic improvements
        # For now, we'll just log what could be improved
        logger.info("Review the improvements list in the report for manual fixes")
        logger.info("Some improvements require manual intervention or AWS console access")


def main():
    """פונקציה ראשית"""
    agent = AutomatedAgent()
    
    try:
        # Run all checks
        report = agent.run_all_checks()
        
        # Save report
        agent.save_report()
        
        # Apply improvements (where possible)
        agent.apply_improvements()
        
        # Exit with appropriate code
        if len(report["issues"]) > 0:
            logger.warning("Issues found - review the report")
            sys.exit(1)
        else:
            logger.info("All checks passed!")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


