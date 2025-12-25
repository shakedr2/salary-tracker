#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to check what's wrong
"""
import sys
import os

# Set the path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

print(f"Current directory: {os.getcwd()}")
print(f"Base directory: {base_dir}")
print(f"Python path: {sys.path[:3]}")

try:
    print("\n1. Testing config import...")
    from backend import config
    print("   ✓ Config imported")
    
    print("\n2. Testing credentials...")
    username = config.YLM_USERNAME
    password = config.YLM_PASSWORD
    print(f"   YLM_USERNAME: {'SET' if username else 'NOT SET'}")
    print(f"   YLM_PASSWORD: {'SET' if password else 'NOT SET'}")
    
    print("\n3. Testing app import...")
    from backend.app import app
    print("   ✓ App imported")
    
    print("\n4. Testing Flask app...")
    print(f"   App name: {app.name}")
    print(f"   Debug mode: {app.debug}")
    
    print("\n✅ All imports successful!")
    print("\n5. Starting server...")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print(f"   Make sure you're in the correct directory")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

