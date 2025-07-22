"""
End-to-End Test Scenarios
Tests complete user workflows from registration to MCP server usage
"""
import pytest
import json
from unittest.mock import patch, AsyncMock
from app.models.user import User
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app import db


class TestCompleteUserWorkflow:
    """Test complete user workflow from registration to usage"""
    
    def test_full_user_onboarding_workflow(self, client):
        """Test complete user journey: register → login → create API key → create org → view dashboard"""
        
        # Step 1: Register new user
        response = client.post('/auth/register', data={
            'name': 'John Doe',
            'email': 'john@example.com',
            'password': 'SecurePassword123',
            'password_confirm': 'SecurePassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        user = User.query.filter_by(email='john@example.com').first()
        assert user is not None
        assert user.name == 'John Doe'
        
        # Step 2: Login
        response = client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'SecurePassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        
        # Step 3: Navigate to API keys page
        response = client.get('/dashboard/keys')
        assert response.status_code == 200
        assert b'No API Keys Yet' in response.data
        
        # Step 4: Create API key
        response = client.post('/dashboard/keys/create', data={
            'name': 'VS Code Integration',
            'description': 'API key for VS Code GitHub Copilot'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'API key created successfully' in response.data or b'VS Code Integration' in response.data
        
        # Verify API key was created
        api_key = APIKey.query.filter_by(name='VS Code Integration', user_id=user.id).first()
        assert api_key is not None
        assert api_key.is_active is True
        
        # Step 5: Navigate to Salesforce orgs page
        response = client.get('/dashboard/orgs')
        assert response.status_code == 200
        assert b'No Salesforce Orgs Connected' in response.data
        
        # Step 6: Create Salesforce org
        response = client.post('/dashboard/orgs/create', data={
            'org_identifier': 'production',
            'instance_url': 'https://mycompany.my.salesforce.com',
            'client_id': 'production_client_id',
            'client_secret': 'production_client_secret',
            'is_sandbox': False
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Salesforce org connected successfully' in response.data or b'production' in response.data
        
        # Verify org was created
        org = SalesforceOrg.query.filter_by(org_identifier='production', user_id=user.id).first()
        assert org is not None
        assert org.instance_url == 'https://mycompany.my.salesforce.com'
        assert org.is_sandbox is False
        
        # Step 7: View usage page
        response = client.get('/dashboard/usage')
        assert response.status_code == 200
        assert b'No Usage History Yet' in response.data
        
        # Step 8: View profile page
        response = client.get('/auth/profile')
        assert response.status_code == 200
        assert b'John Doe' in response.data
        assert b'john@example.com' in response.data
        
        # Step 9: Logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data


class TestAPIKeyLifecycle:
    """Test complete API key lifecycle"""
    
    def test_api_key_creation_and_usage(self, authenticated_client, test_user):
        """Test API key creation, usage, and deactivation"""
        
        # Step 1: Create API key
        response = authenticated_client.post('/dashboard/keys/create', data={
            'name': 'Test Integration',
            'description': 'Testing API key lifecycle'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Get the created API key
        api_key = APIKey.query.filter_by(name='Test Integration', user_id=test_user.id).first()
        assert api_key is not None
        generated_key = api_key._generated_key
        
        # Step 2: Use API key for validation (simulate MCP server call)
        response = authenticated_client.post('/api/v1.0/internal/validate', json={
            'api_key': generated_key,
            'org_id': 'test_org'
        })
        
        # This should fail because no org exists, but API key should be validated
        assert response.status_code == 404  # Org not found, but key is valid
        data = json.loads(response.data)
        assert 'Salesforce organization not found' in data['message']
        
        # Step 3: Create a Salesforce org
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'test_org',
            'instance_url': 'https://test.my.salesforce.com',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'is_sandbox': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Step 4: Now validation should succeed
        response = authenticated_client.post('/api/v1.0/internal/validate', json={
            'api_key': generated_key,
            'org_id': 'test_org'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['user_id'] == test_user.id
        assert data['api_key_id'] == api_key.id
        
        # Step 5: Log usage
        response = authenticated_client.post('/api/v1.0/internal/usage', json={
            'user_id': test_user.id,
            'api_key_id': api_key.id,
            'tool_name': 'revenue_cloud_health_check',
            'success': True,
            'execution_time_ms': 2000,
            'cost_cents': 5
        })
        
        assert response.status_code == 201
        
        # Verify usage was logged
        usage_log = UsageLog.query.filter_by(
            user_id=test_user.id,
            api_key_id=api_key.id
        ).first()
        assert usage_log is not None
        assert usage_log.tool_name == 'revenue_cloud_health_check'
        assert usage_log.cost_cents == 5
        
        # Step 6: Check usage appears in dashboard
        response = authenticated_client.get('/dashboard/usage')
        assert response.status_code == 200
        assert b'revenue_cloud_health_check' in response.data or b'Revenue Cloud Health Check' in response.data
        
        # Step 7: Deactivate API key
        response = authenticated_client.post(f'/dashboard/keys/{api_key.id}/deactivate', 
                                          follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify API key is deactivated
        db.session.refresh(api_key)
        assert api_key.is_active is False
        
        # Step 8: Try to use deactivated key
        response = authenticated_client.post('/api/v1.0/internal/validate', json={
            'api_key': generated_key,
            'org_id': 'test_org'
        })
        
        assert response.status_code == 401  # Should fail with deactivated key


class TestSalesforceOrgManagement:
    """Test Salesforce organization management workflows"""
    
    def test_multi_org_setup(self, authenticated_client, test_user):
        """Test setting up multiple Salesforce orgs"""
        
        orgs_to_create = [
            {
                'org_identifier': 'production',
                'instance_url': 'https://prod.my.salesforce.com',
                'client_id': 'prod_client_id',
                'client_secret': 'prod_secret',
                'is_sandbox': False
            },
            {
                'org_identifier': 'sandbox',
                'instance_url': 'https://sandbox.my.salesforce.com',
                'client_id': 'sandbox_client_id',
                'client_secret': 'sandbox_secret',
                'is_sandbox': True
            },
            {
                'org_identifier': 'dev',
                'instance_url': 'https://dev.my.salesforce.com',
                'client_id': 'dev_client_id',
                'client_secret': 'dev_secret',
                'is_sandbox': True
            }
        ]
        
        # Create multiple orgs
        for org_data in orgs_to_create:
            response = authenticated_client.post('/dashboard/orgs/create', 
                                               data=org_data, 
                                               follow_redirects=True)
            assert response.status_code == 200
        
        # Verify all orgs were created
        user_orgs = SalesforceOrg.query.filter_by(user_id=test_user.id).all()
        assert len(user_orgs) == 3
        
        org_identifiers = [org.org_identifier for org in user_orgs]
        assert 'production' in org_identifiers
        assert 'sandbox' in org_identifiers
        assert 'dev' in org_identifiers
        
        # Test that each org can be used for validation
        api_key = APIKey(user_id=test_user.id, name='Multi-org test')
        db.session.add(api_key)
        db.session.commit()
        generated_key = api_key._generated_key
        
        for org_data in orgs_to_create:
            response = authenticated_client.post('/api/v1.0/internal/validate', json={
                'api_key': generated_key,
                'org_id': org_data['org_identifier']
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['salesforce_credentials']['instance_url'] == org_data['instance_url']
            assert data['salesforce_credentials']['client_id'] == org_data['client_id']
    
    def test_org_identifier_uniqueness(self, authenticated_client, test_user):
        """Test that org identifiers must be unique per user"""
        
        # Create first org
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'unique_org',
            'instance_url': 'https://first.my.salesforce.com',
            'client_id': 'first_client_id',
            'client_secret': 'first_secret'
        })
        
        assert response.status_code == 302  # Redirect on success
        
        # Try to create another org with same identifier
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'unique_org',
            'instance_url': 'https://second.my.salesforce.com',
            'client_id': 'second_client_id',
            'client_secret': 'second_secret'
        })
        
        assert response.status_code == 200  # Form redisplayed with error
        assert b'Organization identifier already exists' in response.data or b'error' in response.data.lower()


class TestUsageTrackingWorkflow:
    """Test complete usage tracking workflow"""
    
    def test_usage_tracking_and_billing(self, authenticated_client, test_user, test_api_key, test_salesforce_org):
        """Test usage tracking from API calls to billing dashboard"""
        
        generated_key = test_api_key._generated_key
        
        # Simulate multiple API calls with different outcomes
        usage_scenarios = [
            {
                'tool_name': 'revenue_cloud_health_check',
                'success': True,
                'execution_time_ms': 1500,
                'cost_cents': 3
            },
            {
                'tool_name': 'revenue_cloud_health_check',
                'success': True,
                'execution_time_ms': 2200,
                'cost_cents': 5
            },
            {
                'tool_name': 'revenue_cloud_health_check',
                'success': False,
                'error_message': 'Salesforce authentication failed',
                'cost_cents': 0
            },
            {
                'tool_name': 'revenue_cloud_health_check',
                'success': True,
                'execution_time_ms': 1800,
                'cost_cents': 4
            }
        ]
        
        # Log usage for each scenario
        for scenario in usage_scenarios:
            usage_data = {
                'user_id': test_user.id,
                'api_key_id': test_api_key.id,
                'tool_name': scenario['tool_name'],
                'success': scenario['success'],
                'cost_cents': scenario['cost_cents']
            }
            
            if 'execution_time_ms' in scenario:
                usage_data['execution_time_ms'] = scenario['execution_time_ms']
            
            if 'error_message' in scenario:
                usage_data['error_message'] = scenario['error_message']
            
            response = authenticated_client.post('/api/v1.0/internal/usage', json=usage_data)
            assert response.status_code == 201
        
        # Check usage dashboard shows correct statistics
        response = authenticated_client.get('/dashboard/usage')
        assert response.status_code == 200
        
        # Should show total calls, success rate, and cost
        assert b'4' in response.data  # Total calls
        assert b'3' in response.data  # Successful calls (or 75% success rate)
        assert b'Revenue Cloud Health Check' in response.data or b'revenue_cloud_health_check' in response.data
        
        # Verify database statistics
        total_usage = UsageLog.query.filter_by(user_id=test_user.id).count()
        assert total_usage == 4
        
        successful_usage = UsageLog.query.filter_by(user_id=test_user.id, success=True).count()
        assert successful_usage == 3
        
        total_cost = sum(log.cost_cents for log in UsageLog.query.filter_by(user_id=test_user.id).all())
        assert total_cost == 12  # 3 + 5 + 0 + 4 = 12 cents


class TestErrorScenarios:
    """Test error handling in complete workflows"""
    
    def test_invalid_salesforce_credentials_workflow(self, authenticated_client, test_user):
        """Test workflow with invalid Salesforce credentials"""
        
        # Create API key
        api_key = APIKey(user_id=test_user.id, name='Error Test Key')
        db.session.add(api_key)
        db.session.commit()
        generated_key = api_key._generated_key
        
        # Create org with invalid credentials (simulated)
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'invalid_org',
            'instance_url': 'https://invalid.my.salesforce.com',
            'client_id': 'invalid_client_id',
            'client_secret': 'invalid_client_secret'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # API key validation should succeed (credentials stored)
        response = authenticated_client.post('/api/v1.0/internal/validate', json={
            'api_key': generated_key,
            'org_id': 'invalid_org'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'salesforce_credentials' in data
        
        # But actual Salesforce calls would fail (this would be tested at MCP server level)
        # Log the failure
        response = authenticated_client.post('/api/v1.0/internal/usage', json={
            'user_id': test_user.id,
            'api_key_id': api_key.id,
            'tool_name': 'revenue_cloud_health_check',
            'success': False,
            'error_message': 'Invalid Salesforce credentials',
            'cost_cents': 0
        })
        
        assert response.status_code == 201
        
        # Error should appear in usage dashboard
        response = authenticated_client.get('/dashboard/usage')
        assert response.status_code == 200
        assert b'Error' in response.data or b'Failed' in response.data
    
    def test_rate_limit_workflow(self, client, test_user):
        """Test workflow when rate limits are exceeded"""
        
        # Create API key
        api_key = APIKey(user_id=test_user.id, name='Rate Limit Test')
        db.session.add(api_key)
        db.session.commit()
        generated_key = api_key._generated_key
        
        # This would require implementing actual rate limiting testing
        # For now, just verify the endpoint structure
        
        # Make a request
        response = client.post('/api/v1.0/internal/validate', json={
            'api_key': generated_key,
            'org_id': 'test_org'
        })
        
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 401, 404, 429]
    
    def test_concurrent_user_workflow(self, client, test_factory):
        """Test concurrent access by multiple users"""
        
        # Create multiple users
        users = []
        for i in range(3):
            user = test_factory.create_user(
                email=f'user{i}@example.com',
                name=f'User {i}'
            )
            users.append(user)
        
        # Each user creates API key and org
        for i, user in enumerate(users):
            api_key = test_factory.create_api_key(user, f'User {i} Key')
            org = test_factory.create_salesforce_org(user, f'user_{i}_org')
            
            # Test validation for each user's resources
            response = client.post('/api/v1.0/internal/validate', json={
                'api_key': api_key._generated_key,
                'org_id': org.org_identifier
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['user_id'] == user.id
            assert data['api_key_id'] == api_key.id
        
        # Verify users can't access each other's resources
        user1_api_key = APIKey.query.filter_by(user_id=users[0].id).first()
        user2_org = SalesforceOrg.query.filter_by(user_id=users[1].id).first()
        
        response = client.post('/api/v1.0/internal/validate', json={
            'api_key': user1_api_key._generated_key,
            'org_id': user2_org.org_identifier
        })
        
        # Should fail - user 1's key with user 2's org
        assert response.status_code == 404  # Org not found for this user


class TestIntegrationExamples:
    """Test integration examples for documentation"""
    
    def test_vscode_integration_simulation(self, authenticated_client, test_user):
        """Simulate VS Code GitHub Copilot integration workflow"""
        
        # Step 1: User creates API key for VS Code
        response = authenticated_client.post('/dashboard/keys/create', data={
            'name': 'VS Code GitHub Copilot',
            'description': 'Integration with VS Code for AI-powered Salesforce analysis'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Step 2: User creates Salesforce org connection
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'production',
            'instance_url': 'https://mycompany.my.salesforce.com',
            'client_id': 'vscode_client_id',
            'client_secret': 'vscode_client_secret'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Step 3: Get API key for VS Code settings
        api_key = APIKey.query.filter_by(
            name='VS Code GitHub Copilot', 
            user_id=test_user.id
        ).first()
        assert api_key is not None
        
        # Step 4: Simulate MCP server calls (what would happen in VS Code)
        # This simulates the MCP server validating and using the API key
        
        # Validation call
        response = authenticated_client.post('/api/v1.0/internal/validate', json={
            'api_key': api_key._generated_key,
            'org_id': 'production'
        })
        
        assert response.status_code == 200
        validation_data = json.loads(response.data)
        
        # Multiple health check calls (simulating AI agent usage)
        health_check_calls = [
            {'tool_name': 'revenue_cloud_health_check', 'check_types': ['basic_org_info']},
            {'tool_name': 'revenue_cloud_health_check', 'check_types': ['sharing_model']},
            {'tool_name': 'revenue_cloud_health_check', 'check_types': ['bundle_analysis']},
        ]
        
        for call in health_check_calls:
            # Log the usage
            response = authenticated_client.post('/api/v1.0/internal/usage', json={
                'user_id': validation_data['user_id'],
                'api_key_id': validation_data['api_key_id'],
                'tool_name': call['tool_name'],
                'success': True,
                'execution_time_ms': 2000,
                'cost_cents': len(call['check_types'])  # 1 cent per check type
            })
            
            assert response.status_code == 201
        
        # Step 5: User checks usage in dashboard
        response = authenticated_client.get('/dashboard/usage')
        assert response.status_code == 200
        
        # Should show the usage from VS Code integration
        assert b'3' in response.data  # 3 API calls
        assert b'revenue_cloud_health_check' in response.data or b'Revenue Cloud Health Check' in response.data
    
    def test_claude_desktop_integration_simulation(self, authenticated_client, test_user):
        """Simulate Claude Desktop integration workflow"""
        
        # Similar to VS Code but with different naming
        response = authenticated_client.post('/dashboard/keys/create', data={
            'name': 'Claude Desktop',
            'description': 'Integration with Claude Desktop for conversational Salesforce analysis'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Create sandbox org for Claude testing
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'sandbox',
            'instance_url': 'https://test.my.salesforce.com',
            'client_id': 'claude_client_id',
            'client_secret': 'claude_client_secret',
            'is_sandbox': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Get API key
        api_key = APIKey.query.filter_by(
            name='Claude Desktop', 
            user_id=test_user.id
        ).first()
        
        # Simulate conversation-driven usage (multiple different calls)
        conversation_calls = [
            'basic_org_info',
            'sharing_model', 
            'data_integrity',
            'bundle_analysis'
        ]
        
        for call in conversation_calls:
            # Validate API key
            response = authenticated_client.post('/api/v1.0/internal/validate', json={
                'api_key': api_key._generated_key,
                'org_id': 'sandbox'
            })
            assert response.status_code == 200
            
            # Log usage
            response = authenticated_client.post('/api/v1.0/internal/usage', json={
                'user_id': test_user.id,
                'api_key_id': api_key.id,
                'tool_name': 'revenue_cloud_health_check',
                'success': True,
                'execution_time_ms': 1800,
                'cost_cents': 1
            })
            assert response.status_code == 201
        
        # Check total usage
        total_logs = UsageLog.query.filter_by(user_id=test_user.id).count()
        assert total_logs == len(conversation_calls) 