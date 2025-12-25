#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
סקריפט מהיר להרצת בדיקות בלבד
Quick script to run checks only
"""

import sys
from pathlib import Path

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agent.main_agent import AutomatedAgent

if __name__ == "__main__":
    agent = AutomatedAgent()
    report = agent.run_all_checks()
    agent.save_report()
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Issues found: {len(report['issues'])}")
    print(f"Improvements suggested: {len(report['improvements'])}")
    
    if report['issues']:
        print("\nIssues:")
        for issue in report['issues'][:10]:  # Show first 10
            print(f"  - {issue}")
    
    if report['improvements']:
        print("\nTop Improvements:")
        for imp in report['improvements'][:5]:  # Show first 5
            print(f"  - {imp}")
    
    print("\nFull report saved to: agent/report.json")
    print("="*60)
    
    sys.exit(0 if len(report['issues']) == 0 else 1)

