#!/usr/bin/env python3
"""
Simple script to run all tests.

Usage:
    python run_tests.py
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests using pytest."""
    print("🧪 Running all tests...")
    print("=" * 50)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", "-v"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Some tests failed (exit code: {result.returncode})")
            sys.exit(result.returncode)
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

def run_tests_with_coverage():
    """Run all tests with coverage report."""
    print("🧪 Running all tests with coverage...")
    print("=" * 50)
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", "-v", 
            "--cov=..", "--cov-report=term-missing"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
        else:
            print(f"\n❌ Some tests failed (exit code: {result.returncode})")
            sys.exit(result.returncode)
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        run_tests_with_coverage()
    else:
        run_tests() 