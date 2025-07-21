#!/usr/bin/env python3
"""
Environment Configuration Check Script
Validates staging and production environment settings
"""

import os
import requests
import json
from urllib.parse import urlparse

class EnvironmentChecker:
    def __init__(self):
        self.is_staging = os.environ.get('IS_STAGING', 'false').lower() == 'true'
        self.flask_env = os.environ.get('FLASK_ENV', 'development')
        self.current_environment = 'staging' if self.is_staging else 'production'
        
    def check_environment_variables(self):
        """Check if all required environment variables are set"""
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'ENCRYPTION_KEY',
            'SALESFORCE_CLIENT_ID',
            'SALESFORCE_CLIENT_SECRET',
            'GOOGLE_CLIENT_ID',
            'GOOGLE_CLIENT_SECRET'
        ]
        
        print(f"\n🔍 Checking Environment Variables for {self.current_environment.upper()}...")
        missing_vars = []
        
        for var in required_vars:
            value = os.environ.get(var)
            if value:
                # Show partial value for security
                if 'SECRET' in var or 'KEY' in var:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value[:50] + "..." if len(value) > 50 else value
                print(f"  ✅ {var}: {display_value}")
            else:
                missing_vars.append(var)
                print(f"  ❌ {var}: NOT SET")
        
        if missing_vars:
            print(f"\n⚠️  Missing required environment variables: {', '.join(missing_vars)}")
            return False
        else:
            print("\n✅ All required environment variables are set!")
            return True
    
    def check_domain_configuration(self):
        """Check if the application is configured for the correct domains"""
        from config import Config
        
        expected_api_domain = Config.get_api_domain()
        expected_dashboard_domain = Config.get_dashboard_domain()
        
        print(f"\n🌐 Domain Configuration Check for {self.current_environment.upper()}...")
        print(f"  Expected API Domain: {expected_api_domain}")
        print(f"  Expected Dashboard Domain: {expected_dashboard_domain}")
        
        # Check if domains match environment
        if self.is_staging:
            if 'staging' not in expected_api_domain or 'staging' not in expected_dashboard_domain:
                print("  ❌ Domain configuration doesn't match staging environment!")
                return False
        else:
            if 'staging' in expected_api_domain or 'staging' in expected_dashboard_domain:
                print("  ❌ Domain configuration doesn't match production environment!")
                return False
        
        print("  ✅ Domain configuration matches environment!")
        return True
    
    def test_local_endpoints(self):
        """Test local application endpoints"""
        print(f"\n🧪 Testing Local Endpoints...")
        
        base_url = "http://localhost:5000"  # Assuming local development server
        
        endpoints = [
            "/health",
            "/api/mcp/tools", 
            "/api/mcp/status"
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint}: OK ({response.status_code})")
                    results.append(True)
                else:
                    print(f"  ⚠️  {endpoint}: {response.status_code}")
                    results.append(False)
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {endpoint}: Connection failed - {str(e)}")
                results.append(False)
        
        return all(results)
    
    def test_remote_endpoints(self, domain=None):
        """Test remote application endpoints"""
        if not domain:
            from config import Config
            domain = Config.get_api_domain()
        
        print(f"\n🌍 Testing Remote Endpoints on {domain}...")
        
        base_url = f"https://{domain}"
        
        endpoints = [
            "/health",
            "/api/mcp/tools", 
            "/api/mcp/status",
            "/"  # Root endpoint should return environment info
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint}: OK ({response.status_code})")
                    
                    # For root endpoint, check environment info
                    if endpoint == "/" and response.headers.get('content-type', '').startswith('application/json'):
                        try:
                            data = response.json()
                            env = data.get('environment', 'unknown')
                            print(f"      Environment: {env}")
                            if env != self.current_environment:
                                print(f"      ⚠️  Environment mismatch! Expected: {self.current_environment}")
                        except json.JSONDecodeError:
                            pass
                    
                    results.append(True)
                else:
                    print(f"  ⚠️  {endpoint}: {response.status_code}")
                    results.append(False)
            except requests.exceptions.RequestException as e:
                print(f"  ❌ {endpoint}: Connection failed - {str(e)}")
                results.append(False)
        
        return all(results)
    
    def check_oauth_configuration(self):
        """Check OAuth redirect URIs"""
        print(f"\n🔐 OAuth Configuration Check...")
        
        from config import Config
        
        # Check Salesforce redirect URI
        sf_redirect = Config.get_salesforce_redirect_uri()
        print(f"  Salesforce Redirect URI: {sf_redirect}")
        
        # Check Google redirect URI
        google_redirect = Config.get_google_redirect_uri()
        print(f"  Google Redirect URI: {google_redirect}")
        
        # Validate they match the environment
        if self.is_staging:
            sf_valid = 'staging-api' in sf_redirect
            google_valid = 'staging-healthcheck' in google_redirect
        else:
            sf_valid = 'staging' not in sf_redirect and 'api.forceweaver.com' in sf_redirect
            google_valid = 'staging' not in google_redirect and 'healthcheck.forceweaver.com' in google_redirect
        
        if sf_valid and google_valid:
            print("  ✅ OAuth redirect URIs match environment!")
            return True
        else:
            print("  ❌ OAuth redirect URIs don't match environment!")
            return False
    
    def run_full_check(self, test_remote=False, remote_domain=None):
        """Run all environment checks"""
        print(f"🚀 ForceWeaver Environment Check - {self.current_environment.upper()}")
        print(f"{'='*50}")
        
        checks = []
        
        # Environment variables check
        checks.append(self.check_environment_variables())
        
        # Domain configuration check
        checks.append(self.check_domain_configuration())
        
        # OAuth configuration check
        checks.append(self.check_oauth_configuration())
        
        # Local endpoints test (optional)
        print(f"\n🤔 Would you like to test local endpoints? (requires local server running)")
        
        # Remote endpoints test
        if test_remote:
            checks.append(self.test_remote_endpoints(remote_domain))
        
        # Summary
        print(f"\n📊 Summary for {self.current_environment.upper()}")
        print(f"{'='*30}")
        
        passed = sum(checks)
        total = len(checks)
        
        if passed == total:
            print(f"✅ All checks passed! ({passed}/{total})")
            print(f"🎉 {self.current_environment.title()} environment is ready!")
            return True
        else:
            print(f"❌ Some checks failed ({passed}/{total})")
            print(f"⚠️  Please fix the issues before deploying to {self.current_environment}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check ForceWeaver environment configuration')
    parser.add_argument('--test-remote', action='store_true', help='Test remote endpoints')
    parser.add_argument('--domain', help='Specific domain to test (overrides environment detection)')
    parser.add_argument('--local-test', action='store_true', help='Test local endpoints')
    
    args = parser.parse_args()
    
    checker = EnvironmentChecker()
    
    if args.local_test:
        checker.test_local_endpoints()
    else:
        success = checker.run_full_check(test_remote=args.test_remote, remote_domain=args.domain)
        exit(0 if success else 1)

if __name__ == "__main__":
    main() 