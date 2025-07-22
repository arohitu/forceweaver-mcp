#!/usr/bin/env python3
"""
ForceWeaver MCP Server Test Runner
Comprehensive test suite with coverage reporting
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(command, description, capture_output=False):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(command)}")
    
    try:
        if capture_output:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        else:
            subprocess.run(command, check=True)
            print(f"✅ {description} - PASSED")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if capture_output and e.stdout:
            print("STDOUT:", e.stdout)
        if capture_output and e.stderr:
            print("STDERR:", e.stderr)
        return None


def setup_test_environment():
    """Setup test environment"""
    print("🚀 Setting up test environment...")
    
    # Set test environment variables
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = 'true'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['ENCRYPTION_KEY'] = 'test-encryption-key-for-testing-only123456='
    
    print("✅ Test environment configured")


def run_unit_tests(verbose=False, coverage=True):
    """Run unit tests"""
    cmd = ['python3', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=app', '--cov=mcp_server', '--cov-report=html', '--cov-report=term'])
    
    cmd.extend([
        'tests/test_models.py',
        '--tb=short'
    ])
    
    run_command(cmd, "Unit Tests (Models)")


def run_api_tests(verbose=False):
    """Run API integration tests"""
    cmd = ['python3', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend([
        'tests/test_api_endpoints.py',
        '--tb=short'
    ])
    
    run_command(cmd, "API Integration Tests")


def run_mcp_tests(verbose=False):
    """Run MCP server tests"""
    cmd = ['python3', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend([
        'tests/test_mcp_server.py',
        '--tb=short'
    ])
    
    run_command(cmd, "MCP Server Tests")


def run_e2e_tests(verbose=False):
    """Run end-to-end tests"""
    cmd = ['python3', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend([
        'tests/test_e2e_workflows.py',
        '--tb=short'
    ])
    
    run_command(cmd, "End-to-End Workflow Tests")


def run_all_tests(verbose=False, coverage=True, stop_on_fail=False):
    """Run all tests in sequence"""
    print("🧪 Running ForceWeaver MCP Server Test Suite")
    print("=" * 80)
    
    setup_test_environment()
    
    test_suites = [
        ("Unit Tests", lambda: run_unit_tests(verbose, coverage)),
        ("API Tests", lambda: run_api_tests(verbose)),
        ("MCP Tests", lambda: run_mcp_tests(verbose)),
        ("E2E Tests", lambda: run_e2e_tests(verbose))
    ]
    
    passed = 0
    failed = 0
    
    for suite_name, test_func in test_suites:
        try:
            test_func()
            passed += 1
            print(f"✅ {suite_name} - PASSED")
        except subprocess.CalledProcessError:
            failed += 1
            print(f"❌ {suite_name} - FAILED")
            
            if stop_on_fail:
                print("\n🛑 Stopping on first failure")
                break
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("💥 SOME TESTS FAILED!")
        return False


def run_linting():
    """Run code linting"""
    linting_commands = [
        (['python', '-m', 'flake8', 'app/', 'mcp_server/', 'tests/', '--max-line-length=88', '--ignore=E203,W503'], 
         "Flake8 Linting"),
        (['python', '-m', 'black', '--check', 'app/', 'mcp_server/', 'tests/'], 
         "Black Code Formatting Check"),
        (['python', '-m', 'isort', '--check-only', 'app/', 'mcp_server/', 'tests/'], 
         "Import Sorting Check")
    ]
    
    for cmd, description in linting_commands:
        try:
            run_command(cmd, description)
        except FileNotFoundError:
            print(f"⚠️  Skipping {description} - tool not installed")


def run_security_checks():
    """Run security checks"""
    security_commands = [
        (['python', '-m', 'bandit', '-r', 'app/', 'mcp_server/', '-f', 'json'], 
         "Bandit Security Analysis"),
        (['python', '-m', 'safety', 'check'], 
         "Safety Vulnerability Check")
    ]
    
    for cmd, description in security_commands:
        try:
            run_command(cmd, description)
        except FileNotFoundError:
            print(f"⚠️  Skipping {description} - tool not installed")


def generate_test_report():
    """Generate comprehensive test report"""
    print("\n📋 Generating test report...")
    
    # Coverage report
    if Path("htmlcov/index.html").exists():
        print("✅ Coverage report generated: htmlcov/index.html")
    
    # Test results
    print("\n📊 Test Results Summary:")
    print("- Unit Tests: Database models, business logic")
    print("- API Tests: REST endpoints, authentication, validation")
    print("- MCP Tests: MCP server, Salesforce integration, health checks")
    print("- E2E Tests: Complete user workflows, integration scenarios")
    
    print("\n🔗 Next Steps:")
    print("1. Review coverage report: open htmlcov/index.html")
    print("2. Fix any failing tests")
    print("3. Add tests for new features")
    print("4. Run tests before deployment")


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="ForceWeaver MCP Server Test Runner")
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--mcp', action='store_true', help='Run MCP server tests only')
    parser.add_argument('--e2e', action='store_true', help='Run E2E tests only')
    parser.add_argument('--lint', action='store_true', help='Run linting checks')
    parser.add_argument('--security', action='store_true', help='Run security checks')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--stop-on-fail', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Determine what to run
    run_specific = args.unit or args.api or args.mcp or args.e2e or args.lint or args.security
    
    if args.unit:
        setup_test_environment()
        run_unit_tests(args.verbose, not args.no_coverage)
    elif args.api:
        setup_test_environment()
        run_api_tests(args.verbose)
    elif args.mcp:
        setup_test_environment()
        run_mcp_tests(args.verbose)
    elif args.e2e:
        setup_test_environment()
        run_e2e_tests(args.verbose)
    elif args.lint:
        run_linting()
    elif args.security:
        run_security_checks()
    elif not run_specific:
        # Run all tests
        success = run_all_tests(args.verbose, not args.no_coverage, args.stop_on_fail)
        generate_test_report()
        
        if not success:
            sys.exit(1)
    
    print("\n🏁 Testing complete!")


if __name__ == '__main__':
    main() 