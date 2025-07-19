#!/usr/bin/env python3
"""
ForceWeaver MCP API - Integration Testing Suite
Tests complete workflows with real server running locally
"""

import os
import sys
import time
import requests
import json
import threading
import subprocess
from datetime import datetime

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key-for-integration-testing'
os.environ['DATABASE_URL'] = 'sqlite:///integration_test.db'
os.environ['ENCRYPTION_KEY'] = 'dGVzdC1lbmNyeXB0aW9uLWtleS1mb3ItaW50ZWdyYXRpb24tdGVzdGluZy0xMjM0NTY3ODkwYWJjZGVmZw=='
os.environ['SALESFORCE_CLIENT_ID'] = 'test-client-id'
os.environ['SALESFORCE_CLIENT_SECRET'] = 'test-client-secret'
os.environ['SALESFORCE_REDIRECT_URI'] = 'http://localhost:5000/api/auth/salesforce/callback'

class IntegrationTestServer:
    """Manages the test server for integration testing"""
    
    def __init__(self, port=5000):
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self.process = None
        self.running = False
        
    def start(self):
        """Start the test server"""
        print(f"🚀 Starting test server on port {self.port}...")
        
        # Initialize database first
        self._init_database()
        
        # Start server
        try:
            self.process = subprocess.Popen([
                sys.executable, 'run.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(30):  # 30 second timeout
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=1)
                    if response.status_code == 200:
                        self.running = True
                        print(f"✅ Server started successfully on {self.base_url}")
                        return True
                except:
                    time.sleep(1)
            
            print("❌ Server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop(self):
        """Stop the test server"""
        if self.process:
            print("🛑 Stopping test server...")
            self.process.terminate()
            self.process.wait()
            self.running = False
            print("✅ Server stopped")
            
        # Clean up database
        try:
            os.remove('integration_test.db')
        except:
            pass
    
    def _init_database(self):
        """Initialize the test database"""
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✅ Database initialized")

class IntegrationTestRunner:
    """Runs integration tests against the test server"""
    
    def __init__(self, server):
        self.server = server
        self.base_url = server.base_url
        self.test_customer_email = "integration-test@example.com"
        self.test_api_key = None
        self.test_customer_id = None
        
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n🧪 ForceWeaver MCP API - Integration Testing Suite")
        print("=" * 60)
        
        tests = [
            ("Basic Server Health", self.test_server_health),
            ("Database Initialization", self.test_database_init),
            ("Customer Creation", self.test_customer_creation),
            ("API Key Authentication", self.test_api_key_auth),
            ("Salesforce Connection Mock", self.test_salesforce_connection),
            ("Health Check Execution", self.test_health_check),
            ("Error Handling", self.test_error_handling),
            ("MCP Compliance", self.test_mcp_compliance),
            ("Complete Workflow", self.test_complete_workflow)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Test: {test_name}")
            try:
                result = test_func()
                if result:
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                failed += 1
        
        print(f"\n" + "=" * 60)
        print(f"📊 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Your ForceWeaver MCP API is ready for deployment!")
            return True
        else:
            print("❌ Some integration tests failed. Please check the output above.")
            return False
    
    def test_server_health(self):
        """Test 1: Basic server health"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.base_url}/health")
            if response.status_code != 200:
                return False
            
            data = response.json()
            if data.get('status') != 'healthy':
                return False
            
            # Test root endpoint
            response = requests.get(f"{self.base_url}/")
            if response.status_code != 200:
                return False
            
            data = response.json()
            if data.get('service') != 'ForceWeaver MCP API':
                return False
            
            print("   ✅ Server health endpoints working")
            return True
            
        except Exception as e:
            print(f"   ❌ Server health test failed: {e}")
            return False
    
    def test_database_init(self):
        """Test 2: Database initialization"""
        try:
            # Test that database is accessible by creating a customer
            from app import create_app, db
            from app.models import Customer
            
            app = create_app()
            with app.app_context():
                # Try to query customers table
                customers = Customer.query.all()
                print(f"   ✅ Database accessible, found {len(customers)} customers")
                return True
                
        except Exception as e:
            print(f"   ❌ Database initialization test failed: {e}")
            return False
    
    def test_customer_creation(self):
        """Test 3: Customer creation"""
        try:
            from app import create_app, db
            from app.models import Customer, APIKey
            from app.core.security import generate_api_key, hash_api_key
            
            app = create_app()
            with app.app_context():
                # Create test customer
                customer = Customer(email=self.test_customer_email)
                db.session.add(customer)
                db.session.flush()
                
                # Create API key
                api_key_value = generate_api_key()
                api_key = APIKey(
                    hashed_key=hash_api_key(api_key_value),
                    customer_id=customer.id
                )
                db.session.add(api_key)
                db.session.commit()
                
                # Store for later tests
                self.test_api_key = api_key_value
                self.test_customer_id = customer.id
                
                print(f"   ✅ Customer created (ID: {customer.id})")
                print(f"   ✅ API key generated: {api_key_value[:10]}...")
                return True
                
        except Exception as e:
            print(f"   ❌ Customer creation test failed: {e}")
            return False
    
    def test_api_key_auth(self):
        """Test 4: API key authentication"""
        try:
            if not self.test_api_key:
                print("   ❌ No API key available for testing")
                return False
            
            # Test with valid API key
            headers = {'Authorization': f'Bearer {self.test_api_key}'}
            response = requests.get(f"{self.base_url}/api/mcp/status", headers=headers)
            
            if response.status_code != 200:
                print(f"   ❌ API key auth failed: {response.status_code}")
                return False
            
            data = response.json()
            if data.get('customer_id') != self.test_customer_id:
                print(f"   ❌ Wrong customer ID returned: {data.get('customer_id')}")
                return False
            
            # Test with invalid API key
            headers = {'Authorization': 'Bearer invalid-key'}
            response = requests.get(f"{self.base_url}/api/mcp/status", headers=headers)
            
            if response.status_code != 401:
                print(f"   ❌ Invalid key should return 401, got {response.status_code}")
                return False
            
            print("   ✅ API key authentication working correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ API key auth test failed: {e}")
            return False
    
    def test_salesforce_connection(self):
        """Test 5: Salesforce connection mock"""
        try:
            from app import create_app, db
            from app.models import SalesforceConnection
            from app.core.security import encrypt_token
            
            app = create_app()
            with app.app_context():
                # Create mock Salesforce connection
                connection = SalesforceConnection(
                    salesforce_org_id="00D123456789MOCK",
                    encrypted_refresh_token=encrypt_token("mock-refresh-token"),
                    instance_url="https://test.salesforce.com",
                    customer_id=self.test_customer_id
                )
                db.session.add(connection)
                db.session.commit()
                
                print(f"   ✅ Salesforce connection created (Org: {connection.salesforce_org_id})")
                return True
                
        except Exception as e:
            print(f"   ❌ Salesforce connection test failed: {e}")
            return False
    
    def test_health_check(self):
        """Test 6: Health check execution"""
        try:
            # We'll mock the health check since we don't have real Salesforce
            from unittest.mock import patch
            
            with patch('app.services.salesforce_service.get_salesforce_api_client') as mock_client:
                # Mock the Salesforce client
                mock_sf = mock_client.return_value
                mock_sf.query.return_value = {
                    'totalSize': 1,
                    'records': [{
                        'Id': '00D123456789ABC',
                        'Name': 'Test Organization',
                        'OrganizationType': 'Production',
                        'InstanceName': 'NA1',
                        'IsSandbox': False,
                        'TrialExpirationDate': None
                    }]
                }
                mock_sf.query_all.return_value = {
                    'totalSize': 1,
                    'records': [{
                        'QualifiedApiName': 'Product2',
                        'InternalSharingModel': 'ReadWrite',
                        'Label': 'Product'
                    }]
                }
                
                # Test health check endpoint
                headers = {'Authorization': f'Bearer {self.test_api_key}'}
                response = requests.post(f"{self.base_url}/api/mcp/health-check", 
                                       headers=headers, timeout=30)
                
                if response.status_code != 200:
                    print(f"   ❌ Health check failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    return False
                
                data = response.json()
                if not data.get('success'):
                    print(f"   ❌ Health check not successful: {data}")
                    return False
                
                print("   ✅ Health check executed successfully")
                return True
                
        except Exception as e:
            print(f"   ❌ Health check test failed: {e}")
            return False
    
    def test_error_handling(self):
        """Test 7: Error handling"""
        try:
            # Test missing authorization
            response = requests.get(f"{self.base_url}/api/mcp/status")
            if response.status_code != 401:
                print(f"   ❌ Missing auth should return 401, got {response.status_code}")
                return False
            
            # Test invalid endpoint
            response = requests.get(f"{self.base_url}/api/nonexistent")
            if response.status_code != 404:
                print(f"   ❌ Invalid endpoint should return 404, got {response.status_code}")
                return False
            
            print("   ✅ Error handling working correctly")
            return True
            
        except Exception as e:
            print(f"   ❌ Error handling test failed: {e}")
            return False
    
    def test_mcp_compliance(self):
        """Test 8: MCP compliance"""
        try:
            # Test tools endpoint
            response = requests.get(f"{self.base_url}/api/mcp/tools")
            if response.status_code != 200:
                return False
            
            data = response.json()
            
            # Check MCP structure
            if 'tools' not in data or 'capabilities' not in data:
                print("   ❌ MCP structure missing")
                return False
            
            # Check tool structure
            if not data['tools']:
                print("   ❌ No tools defined")
                return False
            
            tool = data['tools'][0]
            required_fields = ['name', 'description', 'inputSchema']
            for field in required_fields:
                if field not in tool:
                    print(f"   ❌ Tool missing required field: {field}")
                    return False
            
            print("   ✅ MCP compliance verified")
            return True
            
        except Exception as e:
            print(f"   ❌ MCP compliance test failed: {e}")
            return False
    
    def test_complete_workflow(self):
        """Test 9: Complete workflow"""
        try:
            # Test the complete workflow from start to finish
            print("   📋 Testing complete workflow...")
            
            # 1. Check service status
            headers = {'Authorization': f'Bearer {self.test_api_key}'}
            response = requests.get(f"{self.base_url}/api/mcp/status", headers=headers)
            
            if response.status_code != 200:
                print(f"   ❌ Status check failed: {response.status_code}")
                return False
            
            status_data = response.json()
            print(f"   ✅ Service status: {status_data.get('service_status')}")
            
            # 2. Get available tools
            response = requests.get(f"{self.base_url}/api/mcp/tools")
            if response.status_code != 200:
                print(f"   ❌ Tools endpoint failed: {response.status_code}")
                return False
            
            tools_data = response.json()
            print(f"   ✅ Available tools: {len(tools_data.get('tools', []))}")
            
            # 3. The health check would normally be tested here, but we've already done that
            print("   ✅ Complete workflow verified")
            return True
            
        except Exception as e:
            print(f"   ❌ Complete workflow test failed: {e}")
            return False

def main():
    """Main function to run integration tests"""
    print("🧪 ForceWeaver MCP API - Integration Testing Suite")
    print("This will test the complete API with a real running server locally.\n")
    
    server = IntegrationTestServer()
    
    try:
        # Start server
        if not server.start():
            print("❌ Failed to start test server")
            return False
        
        # Run tests
        runner = IntegrationTestRunner(server)
        success = runner.run_all_tests()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    finally:
        # Always stop server
        server.stop()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 