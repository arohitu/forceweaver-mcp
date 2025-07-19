#!/usr/bin/env python3
"""
ForceWeaver MCP API - Local Unit Testing Suite
Test all components locally without external dependencies
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import sqlite3
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# Set test environment variables
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
os.environ['ENCRYPTION_KEY'] = 'dGVzdC1lbmNyeXB0aW9uLWtleS1mb3ItdGVzdGluZy0xMjM0NTY3ODkwYWJjZGVmZw=='
os.environ['SALESFORCE_CLIENT_ID'] = 'test-client-id'
os.environ['SALESFORCE_CLIENT_SECRET'] = 'test-client-secret'
os.environ['SALESFORCE_REDIRECT_URI'] = 'http://localhost:5000/api/auth/salesforce/callback'

class TestForceWeaverMCPAPI(unittest.TestCase):
    """Test suite for ForceWeaver MCP API"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(delete=False)
        self.test_db.close()
        
        # Set database URL for testing
        os.environ['DATABASE_URL'] = f'sqlite:///{self.test_db.name}'
        
        # Import app after setting environment variables
        from app import create_app, db
        from app.models import Customer, APIKey, SalesforceConnection
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Store references
        self.db = db
        self.Customer = Customer
        self.APIKey = APIKey
        self.SalesforceConnection = SalesforceConnection
        
    def tearDown(self):
        """Clean up test environment"""
        self.db.session.remove()
        self.db.drop_all()
        self.app_context.pop()
        
        # Clean up temporary database
        try:
            os.unlink(self.test_db.name)
        except:
            pass
    
    def test_01_app_creation(self):
        """Test 1: Application creates successfully"""
        print("\n🧪 Test 1: Application Creation")
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.config['TESTING'])
        print("✅ Application created successfully")
    
    def test_02_database_models(self):
        """Test 2: Database models work correctly"""
        print("\n🧪 Test 2: Database Models")
        
        # Create test customer
        customer = self.Customer(email="test@example.com")
        self.db.session.add(customer)
        self.db.session.commit()
        
        # Verify customer created
        self.assertIsNotNone(customer.id)
        self.assertEqual(customer.email, "test@example.com")
        print("✅ Customer model works")
        
        # Create API key
        from app.core.security import generate_api_key, hash_api_key
        api_key_value = generate_api_key()
        api_key = self.APIKey(
            hashed_key=hash_api_key(api_key_value),
            customer_id=customer.id
        )
        self.db.session.add(api_key)
        self.db.session.commit()
        
        # Verify API key created
        self.assertIsNotNone(api_key.id)
        self.assertEqual(api_key.customer_id, customer.id)
        print("✅ APIKey model works")
        
        # Create Salesforce connection
        from app.core.security import encrypt_token
        encrypted_token = encrypt_token("test-refresh-token")
        connection = self.SalesforceConnection(
            salesforce_org_id="00D123456789ABC",
            encrypted_refresh_token=encrypted_token,
            instance_url="https://test.salesforce.com",
            customer_id=customer.id
        )
        self.db.session.add(connection)
        self.db.session.commit()
        
        # Verify connection created
        self.assertIsNotNone(connection.id)
        self.assertEqual(connection.customer_id, customer.id)
        print("✅ SalesforceConnection model works")
        
        # Test relationships
        self.assertEqual(customer.api_key.id, api_key.id)
        self.assertEqual(customer.salesforce_connection.id, connection.id)
        print("✅ Model relationships work")
    
    def test_03_encryption_decryption(self):
        """Test 3: Token encryption/decryption"""
        print("\n🧪 Test 3: Encryption/Decryption")
        
        from app.core.security import encrypt_token, decrypt_token
        
        # Test encryption/decryption
        original_token = "test-refresh-token-12345"
        encrypted_token = encrypt_token(original_token)
        decrypted_token = decrypt_token(encrypted_token)
        
        self.assertIsNotNone(encrypted_token)
        self.assertNotEqual(encrypted_token, original_token)
        self.assertEqual(decrypted_token, original_token)
        print("✅ Token encryption/decryption works")
        
        # Test with None values
        self.assertIsNone(encrypt_token(None))
        self.assertIsNone(decrypt_token(None))
        print("✅ Handles None values correctly")
    
    def test_04_api_key_generation(self):
        """Test 4: API key generation and hashing"""
        print("\n🧪 Test 4: API Key Generation")
        
        from app.core.security import generate_api_key, hash_api_key
        
        # Generate API key
        api_key1 = generate_api_key()
        api_key2 = generate_api_key()
        
        # Verify uniqueness
        self.assertNotEqual(api_key1, api_key2)
        self.assertTrue(len(api_key1) >= 32)
        print("✅ API key generation works")
        
        # Test hashing
        hash1 = hash_api_key(api_key1)
        hash2 = hash_api_key(api_key1)  # Same key
        hash3 = hash_api_key(api_key2)  # Different key
        
        self.assertEqual(hash1, hash2)  # Same input = same hash
        self.assertNotEqual(hash1, hash3)  # Different input = different hash
        self.assertEqual(len(hash1), 64)  # SHA-256 produces 64 character hex
        print("✅ API key hashing works")
    
    def test_05_basic_endpoints(self):
        """Test 5: Basic endpoints without authentication"""
        print("\n🧪 Test 5: Basic Endpoints")
        
        # Test root endpoint
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['service'], 'ForceWeaver MCP API')
        print("✅ Root endpoint works")
        
        # Test health endpoint
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        print("✅ Health endpoint works")
        
        # Test MCP tools endpoint
        response = self.client.get('/api/mcp/tools')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('tools', data)
        self.assertTrue(len(data['tools']) > 0)
        print("✅ MCP tools endpoint works")
    
    def test_06_api_key_authentication(self):
        """Test 6: API key authentication"""
        print("\n🧪 Test 6: API Key Authentication")
        
        from app.core.security import generate_api_key, hash_api_key
        
        # Create test customer with API key
        customer = self.Customer(email="test@example.com")
        self.db.session.add(customer)
        self.db.session.flush()
        
        api_key_value = generate_api_key()
        api_key = self.APIKey(
            hashed_key=hash_api_key(api_key_value),
            customer_id=customer.id
        )
        self.db.session.add(api_key)
        self.db.session.commit()
        
        # Test with valid API key
        headers = {'Authorization': f'Bearer {api_key_value}'}
        response = self.client.get('/api/mcp/status', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['customer_id'], customer.id)
        print("✅ Valid API key authentication works")
        
        # Test with invalid API key
        headers = {'Authorization': 'Bearer invalid-key'}
        response = self.client.get('/api/mcp/status', headers=headers)
        self.assertEqual(response.status_code, 401)
        print("✅ Invalid API key rejection works")
        
        # Test with missing authorization header
        response = self.client.get('/api/mcp/status')
        self.assertEqual(response.status_code, 401)
        print("✅ Missing authorization header rejection works")
    
    def test_07_salesforce_service_mocking(self):
        """Test 7: Salesforce service with mocking"""
        print("\n🧪 Test 7: Salesforce Service (Mocked)")
        
        from app.services.salesforce_service import get_salesforce_api_client
        from app.core.security import encrypt_token
        
        # Create mock connection
        mock_connection = Mock()
        mock_connection.encrypted_refresh_token = encrypt_token("mock-refresh-token")
        mock_connection.instance_url = "https://test.salesforce.com"
        
        # Mock Salesforce client
        with patch('app.services.salesforce_service.Salesforce') as mock_sf:
            mock_sf_instance = Mock()
            mock_sf.return_value = mock_sf_instance
            
            # Test client creation
            client = get_salesforce_api_client(mock_connection)
            
            # Verify Salesforce client was created with correct parameters
            mock_sf.assert_called_once()
            mock_sf_instance.refresh_token.assert_called_once()
            print("✅ Salesforce client creation works")
    
    def test_08_health_checker_mocking(self):
        """Test 8: Health checker with mocked Salesforce client"""
        print("\n🧪 Test 8: Health Checker (Mocked)")
        
        from app.services.health_checker_service import RevenueCloudHealthChecker
        
        # Create mock Salesforce client
        mock_sf_client = Mock()
        
        # Mock organization query
        mock_sf_client.query.return_value = {
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
        
        # Mock sharing query
        mock_sf_client.query_all.return_value = {
            'totalSize': 1,
            'records': [{
                'QualifiedApiName': 'Product2',
                'InternalSharingModel': 'ReadWrite',
                'Label': 'Product'
            }]
        }
        
        # Create health checker
        checker = RevenueCloudHealthChecker(mock_sf_client)
        
        # Test basic org info check
        checker.run_basic_org_info_check()
        self.assertEqual(len(checker.results), 1)
        self.assertEqual(checker.results[0].status, 'passed')
        print("✅ Basic org info check works")
        
        # Test OWD sharing check
        checker.run_owd_sharing_check()
        self.assertEqual(len(checker.results), 2)
        print("✅ OWD sharing check works")
    
    def test_09_oauth_flow_mocking(self):
        """Test 9: OAuth flow with mocking"""
        print("\n🧪 Test 9: OAuth Flow (Mocked)")
        
        with patch('app.services.salesforce_service.requests.post') as mock_post:
            # Mock token exchange response
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'access_token': 'mock-access-token',
                'refresh_token': 'mock-refresh-token',
                'instance_url': 'https://test.salesforce.com'
            }
            
            from app.services.salesforce_service import exchange_code_for_tokens
            
            # Test token exchange
            tokens = exchange_code_for_tokens('mock-code', 'http://localhost:5000/callback')
            
            self.assertEqual(tokens['access_token'], 'mock-access-token')
            self.assertEqual(tokens['refresh_token'], 'mock-refresh-token')
            print("✅ Token exchange works")
    
    def test_10_complete_workflow(self):
        """Test 10: Complete workflow simulation"""
        print("\n🧪 Test 10: Complete Workflow")
        
        from app.core.security import generate_api_key, hash_api_key, encrypt_token
        
        # Step 1: Create customer
        customer = self.Customer(email="workflow@test.com")
        self.db.session.add(customer)
        self.db.session.flush()
        
        # Step 2: Create API key
        api_key_value = generate_api_key()
        api_key = self.APIKey(
            hashed_key=hash_api_key(api_key_value),
            customer_id=customer.id
        )
        self.db.session.add(api_key)
        
        # Step 3: Create Salesforce connection
        connection = self.SalesforceConnection(
            salesforce_org_id="00D123456789ABC",
            encrypted_refresh_token=encrypt_token("mock-refresh-token"),
            instance_url="https://test.salesforce.com",
            customer_id=customer.id
        )
        self.db.session.add(connection)
        self.db.session.commit()
        
        # Step 4: Test authenticated request
        headers = {'Authorization': f'Bearer {api_key_value}'}
        response = self.client.get('/api/mcp/status', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['customer_id'], customer.id)
        self.assertTrue(data['salesforce_connected'])
        self.assertEqual(data['salesforce_org_id'], "00D123456789ABC")
        print("✅ Complete workflow works")
    
    def test_11_error_handling(self):
        """Test 11: Error handling"""
        print("\n🧪 Test 11: Error Handling")
        
        from app.core.security import decrypt_token
        
        # Test decryption with invalid token
        result = decrypt_token("invalid-encrypted-token")
        self.assertIsNone(result)
        print("✅ Invalid token decryption handled gracefully")
        
        # Test API endpoint with malformed request
        response = self.client.post('/api/mcp/health-check', 
                                   headers={'Authorization': 'Bearer invalid'},
                                   json={'invalid': 'data'})
        self.assertEqual(response.status_code, 401)
        print("✅ Malformed requests handled gracefully")
    
    def test_12_mcp_compliance(self):
        """Test 12: MCP compliance"""
        print("\n🧪 Test 12: MCP Compliance")
        
        # Test tools endpoint structure
        response = self.client.get('/api/mcp/tools')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Verify MCP structure
        self.assertIn('tools', data)
        self.assertIn('capabilities', data)
        
        # Verify tool structure
        tool = data['tools'][0]
        self.assertIn('name', tool)
        self.assertIn('description', tool)
        self.assertIn('inputSchema', tool)
        print("✅ MCP compliance verified")

def run_local_tests():
    """Run all local tests"""
    print("🧪 ForceWeaver MCP API - Local Unit Testing Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestForceWeaverMCPAPI)
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your ForceWeaver MCP API is ready for local testing")
        return True
    else:
        print("❌ Some tests failed. Please check the output above.")
        return False

if __name__ == '__main__':
    success = run_local_tests()
    sys.exit(0 if success else 1) 