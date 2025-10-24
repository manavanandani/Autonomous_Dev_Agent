#!/usr/bin/env python3
"""
Comprehensive test script for the Autonomous Dev Agent
Tests both CLI and UI functionality
"""

import os
import sys
import tempfile
import subprocess
import time

def test_cli_dry_run():
    """Test CLI dry-run functionality"""
    print("🧪 Testing CLI Dry-Run...")
    
    # Create a test requirement file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Create a Python calculator that can add, subtract, multiply, and divide two numbers")
        req_file = f.name
    
    try:
        # Run the CLI in dry-run mode
        result = subprocess.run([
            sys.executable, '-m', 'autonomous_dev_agent.src.main',
            '--requirements', req_file,
            '--output', 'test_output',
            '--dry-run'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ CLI Dry-Run: SUCCESS")
            return True
        else:
            print(f"❌ CLI Dry-Run: FAILED")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ CLI Dry-Run: TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ CLI Dry-Run: ERROR - {e}")
        return False
    finally:
        os.unlink(req_file)

def test_ui_functionality():
    """Test UI functionality by simulating a request"""
    print("🧪 Testing UI Functionality...")
    
    try:
        # Test if we can import the UI components
        sys.path.insert(0, '.')
        import autonomous_dev_agent.src.ui.app
        from autonomous_dev_agent.src.config.config import settings
        
        # Test dry-run setting
        settings.DRY_RUN = True
        from autonomous_dev_agent.src.main import process_requirements
        
        result = process_requirements("Create a simple hello world program", "ui-test")
        
        if isinstance(result, dict) and 'status' in result:
            print("✅ UI Functionality: SUCCESS")
            return True
        else:
            print("❌ UI Functionality: FAILED - Invalid result format")
            return False
            
    except Exception as e:
        print(f"❌ UI Functionality: ERROR - {e}")
        return False

def test_streamlit_server():
    """Test if Streamlit server is running"""
    print("🧪 Testing Streamlit Server...")
    
    try:
        import requests
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit Server: RUNNING")
            return True
        else:
            print(f"❌ Streamlit Server: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Streamlit Server: ERROR - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Comprehensive Tests for Autonomous Dev Agent")
    print("=" * 60)
    
    tests = [
        test_cli_dry_run,
        test_ui_functionality,
        test_streamlit_server
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
        print()
    
    print("=" * 60)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("🎉 ALL TESTS PASSED! The system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
