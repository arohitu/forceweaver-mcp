#!/usr/bin/env python3
"""
ForceWeaver Deployment Script
Simplifies deployment to staging and production environments
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

class ForceWeaverDeployer:
    def __init__(self):
        self.environments = {
            'staging': {
                'app_name': 'forceweaver-mcp-staging',
                'branch': 'staging',
                'domains': [
                    'staging-healthcheck.forceweaver.com',
                    'staging-api.forceweaver.com'
                ],
                'required_env_vars': {
                    'IS_STAGING': 'true',
                    'FLASK_ENV': 'staging'
                }
            },
            'production': {
                'app_name': 'forceweaver-mcp-api',
                'branch': 'main',
                'domains': [
                    'healthcheck.forceweaver.com',
                    'api.forceweaver.com'
                ],
                'required_env_vars': {
                    'IS_STAGING': 'false',
                    'FLASK_ENV': 'production'
                }
            }
        }
    
    def run_command(self, command, capture_output=False):
        """Execute a shell command"""
        print(f"🔧 Running: {command}")
        try:
            if capture_output:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                return result.returncode == 0, result.stdout.strip()
            else:
                result = subprocess.run(command, shell=True)
                return result.returncode == 0, ""
        except Exception as e:
            print(f"❌ Error running command: {e}")
            return False, str(e)
    
    def check_git_status(self):
        """Check if git working directory is clean"""
        print("\n🔍 Checking git status...")
        success, output = self.run_command("git status --porcelain", capture_output=True)
        
        if not success:
            print("❌ Failed to check git status")
            return False
        
        if output.strip():
            print("⚠️  Working directory has uncommitted changes:")
            print(output)
            response = input("Continue anyway? (y/N): ")
            return response.lower() == 'y'
        else:
            print("✅ Working directory is clean")
            return True
    
    def check_branch(self, target_branch):
        """Check if we're on the correct branch"""
        print(f"\n🌿 Checking current branch...")
        success, current_branch = self.run_command("git rev-parse --abbrev-ref HEAD", capture_output=True)
        
        if not success:
            print("❌ Failed to get current branch")
            return False
        
        print(f"Current branch: {current_branch}")
        print(f"Target branch: {target_branch}")
        
        if current_branch != target_branch:
            print(f"⚠️  Not on target branch '{target_branch}'")
            response = input(f"Switch to {target_branch}? (y/N): ")
            if response.lower() == 'y':
                success, _ = self.run_command(f"git checkout {target_branch}")
                return success
            else:
                return False
        else:
            print("✅ On correct branch")
            return True
    
    def check_heroku_app(self, app_name):
        """Check if Heroku app exists and is accessible"""
        print(f"\n☁️  Checking Heroku app '{app_name}'...")
        success, _ = self.run_command(f"heroku apps:info -a {app_name}", capture_output=True)
        
        if success:
            print("✅ Heroku app found")
            return True
        else:
            print(f"❌ Heroku app '{app_name}' not found or not accessible")
            return False
    
    def check_environment_vars(self, app_name, required_vars):
        """Check if required environment variables are set"""
        print(f"\n🔧 Checking environment variables for {app_name}...")
        
        success, output = self.run_command(f"heroku config -a {app_name}", capture_output=True)
        
        if not success:
            print("❌ Failed to get environment variables")
            return False
        
        config_lines = output.split('\n')
        config_dict = {}
        
        for line in config_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                config_dict[key.strip()] = value.strip()
        
        missing_vars = []
        incorrect_vars = []
        
        for var, expected_value in required_vars.items():
            if var not in config_dict:
                missing_vars.append(var)
            elif config_dict[var] != expected_value:
                incorrect_vars.append(f"{var} (expected: {expected_value}, got: {config_dict[var]})")
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        
        if incorrect_vars:
            print(f"❌ Incorrect environment variables: {', '.join(incorrect_vars)}")
        
        if not missing_vars and not incorrect_vars:
            print("✅ All required environment variables are correctly set")
            return True
        
        return False
    
    def deploy_to_heroku(self, environment):
        """Deploy to the specified environment"""
        config = self.environments[environment]
        app_name = config['app_name']
        branch = config['branch']
        
        print(f"\n🚀 Deploying to {environment.upper()}...")
        print(f"App: {app_name}")
        print(f"Branch: {branch}")
        
        # Add git remote if not exists
        success, _ = self.run_command(f"git remote get-url {environment}", capture_output=True)
        if not success:
            print(f"Adding git remote for {environment}...")
            heroku_git_url = f"https://git.heroku.com/{app_name}.git"
            self.run_command(f"git remote add {environment} {heroku_git_url}")
        
        # Deploy
        deploy_command = f"git push {environment} {branch}:main"
        success, _ = self.run_command(deploy_command)
        
        if not success:
            print(f"❌ Deployment to {environment} failed!")
            return False
        
        print(f"✅ Deployment to {environment} successful!")
        return True
    
    def run_database_migrations(self, app_name):
        """Run database initialization/migrations"""
        print(f"\n💾 Running database initialization for {app_name}...")
        success, _ = self.run_command(f"heroku run python init_db.py -a {app_name}")
        
        if success:
            print("✅ Database initialization completed")
            return True
        else:
            print("❌ Database initialization failed")
            return False
    
    def test_deployment(self, environment):
        """Test the deployment"""
        config = self.environments[environment]
        domains = config['domains']
        
        print(f"\n🧪 Testing {environment} deployment...")
        
        for domain in domains:
            print(f"Testing {domain}...")
            success, _ = self.run_command(f"curl -I https://{domain}/health", capture_output=True)
            if success:
                print(f"✅ {domain} is responding")
            else:
                print(f"⚠️  {domain} may not be ready yet (or DNS not propagated)")
    
    def deploy(self, environment, skip_checks=False, run_migrations=True, test_after_deploy=True):
        """Full deployment process"""
        print(f"\n🎯 Starting deployment to {environment.upper()}")
        print(f"{'='*50}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if environment not in self.environments:
            print(f"❌ Unknown environment: {environment}")
            print(f"Available environments: {', '.join(self.environments.keys())}")
            return False
        
        config = self.environments[environment]
        app_name = config['app_name']
        branch = config['branch']
        required_vars = config['required_env_vars']
        
        # Pre-deployment checks
        if not skip_checks:
            print("\n📋 Pre-deployment checks...")
            
            checks = [
                self.check_git_status(),
                self.check_branch(branch),
                self.check_heroku_app(app_name),
                self.check_environment_vars(app_name, required_vars)
            ]
            
            if not all(checks):
                print("❌ Pre-deployment checks failed!")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
        
        # Deploy
        if not self.deploy_to_heroku(environment):
            return False
        
        # Run migrations
        if run_migrations:
            if not self.run_database_migrations(app_name):
                print("⚠️  Database migration failed, but deployment may still be functional")
        
        # Test deployment
        if test_after_deploy:
            self.test_deployment(environment)
        
        print(f"\n🎉 Deployment to {environment.upper()} completed!")
        print(f"Dashboard: https://{config['domains'][0]}")
        print(f"API: https://{config['domains'][1]}")
        
        return True
    
    def status(self, environment):
        """Check status of an environment"""
        if environment not in self.environments:
            print(f"❌ Unknown environment: {environment}")
            return
        
        config = self.environments[environment]
        app_name = config['app_name']
        
        print(f"\n📊 Status for {environment.upper()}")
        print(f"{'='*40}")
        
        # App status
        print("\n🏗️  App Status:")
        self.run_command(f"heroku ps -a {app_name}")
        
        # Recent logs
        print(f"\n📝 Recent Logs:")
        self.run_command(f"heroku logs --tail -n 10 -a {app_name}")

def main():
    parser = argparse.ArgumentParser(description='ForceWeaver Deployment Tool')
    parser.add_argument('action', choices=['deploy', 'status'], help='Action to perform')
    parser.add_argument('environment', choices=['staging', 'production'], help='Target environment')
    parser.add_argument('--skip-checks', action='store_true', help='Skip pre-deployment checks')
    parser.add_argument('--no-migrations', action='store_true', help='Skip database migrations')
    parser.add_argument('--no-test', action='store_true', help='Skip post-deployment tests')
    
    args = parser.parse_args()
    
    deployer = ForceWeaverDeployer()
    
    if args.action == 'deploy':
        success = deployer.deploy(
            args.environment,
            skip_checks=args.skip_checks,
            run_migrations=not args.no_migrations,
            test_after_deploy=not args.no_test
        )
        sys.exit(0 if success else 1)
    
    elif args.action == 'status':
        deployer.status(args.environment)

if __name__ == "__main__":
    main() 