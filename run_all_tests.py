#!/usr/bin/env python3
"""
ForceWeaver MCP API - Master Test Runner
Runs all tests in sequence to verify the complete system
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def run_command(command, description, timeout=120):
    """Run a command and return success/failure"""
    print(f"\n🔄 {description}")
    print(f"💻 Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            print(f"✅ {description}: PASSED")
            if result.stdout:
                print(f"📄 Output:\n{result.stdout}")
            return True
        else:
            print(f"❌ {description}: FAILED")
            if result.stderr:
                print(f"🚨 Error:\n{result.stderr}")
            if result.stdout:
                print(f"📄 Output:\n{result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description}: TIMEOUT ({timeout}s)")
        return False
    except Exception as e:
        print(f"❌ {description}: ERROR - {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking Dependencies")
    print("=" * 30)
    
    dependencies = [
        ("Python", "python --version"),
        ("Flask", "python -c 'import flask; print(f\"Flask {flask.__version__}\")'"),
        ("SQLAlchemy", "python -c 'import sqlalchemy; print(f\"SQLAlchemy {sqlalchemy.__version__}\")'"),
        ("Cryptography", "python -c 'import cryptography; print(f\"Cryptography {cryptography.__version__}\")'"),
        ("Requests", "python -c 'import requests; print(f\"Requests {requests.__version__}\")'"),
    ]
    
    missing = []
    
    for name, command in dependencies:
        if run_command(command, f"Checking {name}", timeout=10):
            pass
        else:
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies are installed!")
    return True

def run_all_tests():
    """Run all test suites"""
    print("\n🧪 ForceWeaver MCP API - Master Test Runner")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Track results
    test_results = []
    
    # Test 1: Check dependencies
    print("\n" + "=" * 60)
    print("🔍 PHASE 1: DEPENDENCY CHECK")
    print("=" * 60)
    
    deps_ok = check_dependencies()
    test_results.append(("Dependency Check", deps_ok))
    
    if not deps_ok:
        print("\n❌ Cannot proceed without required dependencies")
        return False
    
    # Test 2: Unit tests
    print("\n" + "=" * 60)
    print("🧪 PHASE 2: UNIT TESTS")
    print("=" * 60)
    
    unit_tests_ok = run_command(
        "python test_local.py",
        "Unit Tests (All Components)",
        timeout=180
    )
    test_results.append(("Unit Tests", unit_tests_ok))
    
    # Test 3: Setup test data
    print("\n" + "=" * 60)
    print("🔧 PHASE 3: TEST DATA SETUP")
    print("=" * 60)
    
    setup_ok = run_command(
        "python setup_test_data.py setup",
        "Test Data Setup",
        timeout=60
    )
    test_results.append(("Test Data Setup", setup_ok))
    
    # Test 4: Integration tests
    print("\n" + "=" * 60)
    print("🌐 PHASE 4: INTEGRATION TESTS")
    print("=" * 60)
    
    integration_ok = run_command(
        "python test_integration.py",
        "Integration Tests (Real Server)",
        timeout=300
    )
    test_results.append(("Integration Tests", integration_ok))
    
    # Test 5: Authentication tests
    print("\n" + "=" * 60)
    print("🔐 PHASE 5: AUTHENTICATION TESTS")
    print("=" * 60)
    
    auth_ok = run_command(
        "python test_auth.py",
        "Authentication System Tests",
        timeout=180
    )
    test_results.append(("Authentication Tests", auth_ok))
    
    # Test 6: Manual endpoint tests
    print("\n" + "=" * 60)
    print("🌍 PHASE 6: ENDPOINT TESTS")
    print("=" * 60)
    
    endpoint_ok = run_command(
        "python setup_test_data.py test",
        "Manual Endpoint Tests",
        timeout=60
    )
    test_results.append(("Endpoint Tests", endpoint_ok))
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"📈 Overall Results: {passed}/{total} test suites passed")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📋 Detailed Results:")
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    # Final verdict
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your ForceWeaver MCP API is fully tested and ready for deployment!")
        
        print("\n🚀 Next Steps:")
        print("1. Deploy to your chosen platform (Heroku, DigitalOcean, etc.)")
        print("2. Set up production environment variables")
        print("3. Create a real Salesforce Connected App")
        print("4. Test with actual customer data")
        
        return True
    else:
        print(f"\n❌ {total - passed} TEST SUITE(S) FAILED")
        print("Please review the output above and fix any issues before deployment.")
        
        print("\n🔧 Troubleshooting:")
        print("1. Check the error messages above")
        print("2. Ensure all dependencies are installed")
        print("3. Verify environment variables are set")
        print("4. Check if any ports are already in use")
        
        return False

def run_quick_test():
    """Run a quick test of core functionality"""
    print("\n⚡ Quick Test Mode")
    print("=" * 30)
    
    # Just run unit tests
    unit_tests_ok = run_command(
        "python test_local.py",
        "Unit Tests (Quick)",
        timeout=60
    )
    
    if unit_tests_ok:
        print("\n✅ Quick test passed! Core functionality is working.")
    else:
        print("\n❌ Quick test failed. Check unit tests.")
    
    return unit_tests_ok

def cleanup_all():
    """Clean up all test artifacts"""
    print("\n🧹 Cleaning Up All Test Data")
    print("=" * 30)
    
    cleanup_ok = run_command(
        "python setup_test_data.py cleanup",
        "Test Data Cleanup",
        timeout=30
    )
    
    if cleanup_ok:
        print("✅ All test data cleaned up!")
    else:
        print("❌ Some cleanup issues occurred")
    
    return cleanup_ok

def show_usage():
    """Show usage information"""
    print("🧪 ForceWeaver MCP API - Master Test Runner")
    print("=" * 50)
    print("\nUsage: python run_all_tests.py [command]")
    print("\nCommands:")
    print("  full     - Run all test suites (default)")
    print("  quick    - Run quick unit tests only")
    print("  cleanup  - Clean up all test data")
    print("  help     - Show this help message")
    print("\nExamples:")
    print("  python run_all_tests.py")
    print("  python run_all_tests.py full")
    print("  python run_all_tests.py quick")
    print("  python run_all_tests.py cleanup")

def main():
    """Main function"""
    
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "full"
    
    if command == "help":
        show_usage()
    elif command == "full":
        success = run_all_tests()
        sys.exit(0 if success else 1)
    elif command == "quick":
        success = run_quick_test()
        sys.exit(0 if success else 1)
    elif command == "cleanup":
        success = cleanup_all()
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Unknown command: {command}")
        show_usage()
        sys.exit(1)

if __name__ == '__main__':
    main() 