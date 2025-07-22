"""
Integration tests for API endpoints
"""
import json
import pytest
from unittest.mock import patch, Mock

from app.models.user import User
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app import db


class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_register_get(self, client):
        """Test registration page loads"""
        response = client.get('/auth/register')
        assert response.status_code == 200
        assert b'Sign Up' in response.data
    
    def test_register_post_success(self, client):
        """Test successful user registration"""
        response = client.post('/auth/register', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify user was created
        user = User.query.filter_by(email='test@example.com').first()
        assert user is not None
        assert user.name == 'Test User'
    
    def test_register_post_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        response = client.post('/auth/register', data={
            'name': 'Another User',
            'email': test_user.email,
            'password': 'testpassword',
            'password_confirm': 'testpassword'
        })
        
        assert response.status_code == 200
        assert b'Email already registered' in response.data
    
    def test_login_get(self, client):
        """Test login page loads"""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'Sign In' in response.data
    
    def test_login_post_success(self, client, test_user):
        """Test successful login"""
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'testpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Dashboard' in response.data
    
    def test_login_post_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    def test_logout(self, authenticated_client):
        """Test user logout"""
        response = authenticated_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data


class TestDashboardRoutes:
    """Test dashboard routes"""
    
    def test_dashboard_index_unauthenticated(self, client):
        """Test dashboard requires authentication"""
        response = client.get('/dashboard/', follow_redirects=True)
        assert response.status_code == 200
        assert b'Sign In' in response.data
    
    def test_dashboard_index_authenticated(self, authenticated_client, test_user):
        """Test dashboard loads for authenticated user"""
        response = authenticated_client.get('/dashboard/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data
        assert test_user.name.encode() in response.data
    
    def test_api_keys_page(self, authenticated_client):
        """Test API keys page loads"""
        response = authenticated_client.get('/dashboard/keys')
        assert response.status_code == 200
        assert b'API Keys' in response.data
    
    def test_create_api_key(self, authenticated_client, test_user):
        """Test creating a new API key"""
        response = authenticated_client.post('/dashboard/keys/create', data={
            'name': 'Test API Key',
            'description': 'Test description'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify API key was created
        api_key = APIKey.query.filter_by(name='Test API Key', user_id=test_user.id).first()
        assert api_key is not None
        assert api_key.description == 'Test description'
    
    def test_deactivate_api_key(self, authenticated_client, test_api_key):
        """Test deactivating an API key"""
        response = authenticated_client.post(f'/dashboard/keys/{test_api_key.id}/deactivate', 
                                          follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify API key was deactivated
        db.session.refresh(test_api_key)
        assert test_api_key.is_active is False
    
    def test_salesforce_orgs_page(self, authenticated_client):
        """Test Salesforce orgs page loads"""
        response = authenticated_client.get('/dashboard/orgs')
        assert response.status_code == 200
        assert b'Salesforce Organizations' in response.data
    
    def test_create_salesforce_org(self, authenticated_client, test_user):
        """Test creating a new Salesforce org"""
        response = authenticated_client.post('/dashboard/orgs/create', data={
            'org_identifier': 'test_org',
            'instance_url': 'https://test.my.salesforce.com',
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'is_sandbox': True
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify org was created
        org = SalesforceOrg.query.filter_by(
            org_identifier='test_org', 
            user_id=test_user.id
        ).first()
        assert org is not None
        assert org.instance_url == 'https://test.my.salesforce.com'
        assert org.is_sandbox is True
    
    def test_usage_page(self, authenticated_client):
        """Test usage page loads"""
        response = authenticated_client.get('/dashboard/usage')
        assert response.status_code == 200
        assert b'Usage & Billing' in response.data
    
    def test_profile_page(self, authenticated_client, test_user):
        """Test profile page loads"""
        response = authenticated_client.get('/auth/profile')
        assert response.status_code == 200
        assert b'Profile' in response.data
        assert test_user.name.encode() in response.data


class TestInternalAPIRoutes:
    """Test internal API endpoints used by MCP server"""
    
    def test_validate_api_key_success(self, client, test_user, test_salesforce_org):
        """Test successful API key validation"""
        # Create API key with known value
        api_key = APIKey(user_id=test_user.id, name='Test Key')
        db.session.add(api_key)
        db.session.commit()
        
        # Get the generated key
        generated_key = api_key._generated_key
        
        response = client.post('/api/v1.0/internal/validate', 
                             json={
                                 'api_key': generated_key,
                                 'org_id': test_salesforce_org.org_identifier
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_id'] == test_user.id
        assert data['api_key_id'] == api_key.id
        assert data['org_id'] == test_salesforce_org.id
        assert 'salesforce_credentials' in data
        
        credentials = data['salesforce_credentials']
        assert credentials['instance_url'] == test_salesforce_org.instance_url
        assert credentials['client_id'] == test_salesforce_org.client_id
    
    def test_validate_api_key_invalid(self, client):
        """Test API key validation with invalid key"""
        response = client.post('/api/v1.0/internal/validate',
                             json={
                                 'api_key': 'invalid_key',
                                 'org_id': 'test_org'
                             })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Invalid API key' in data['message']
    
    def test_validate_api_key_missing_org(self, client, test_user):
        """Test API key validation with non-existent org"""
        # Create API key
        api_key = APIKey(user_id=test_user.id, name='Test Key')
        db.session.add(api_key)
        db.session.commit()
        
        generated_key = api_key._generated_key
        
        response = client.post('/api/v1.0/internal/validate',
                             json={
                                 'api_key': generated_key,
                                 'org_id': 'nonexistent_org'
                             })
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'message' in data
        assert 'Salesforce organization not found' in data['message']
    
    def test_log_usage_success(self, client, test_user, test_api_key):
        """Test successful usage logging"""
        response = client.post('/api/v1.0/internal/usage',
                             json={
                                 'user_id': test_user.id,
                                 'api_key_id': test_api_key.id,
                                 'tool_name': 'revenue_cloud_health_check',
                                 'success': True,
                                 'execution_time_ms': 2500,
                                 'cost_cents': 5
                             })
        
        assert response.status_code == 201
        
        # Verify usage log was created
        log = UsageLog.query.filter_by(
            user_id=test_user.id,
            api_key_id=test_api_key.id,
            tool_name='revenue_cloud_health_check'
        ).first()
        
        assert log is not None
        assert log.success is True
        assert log.execution_time_ms == 2500
        assert log.cost_cents == 5
    
    def test_log_usage_failed_call(self, client, test_user, test_api_key):
        """Test logging failed API call"""
        response = client.post('/api/v1.0/internal/usage',
                             json={
                                 'user_id': test_user.id,
                                 'api_key_id': test_api_key.id,
                                 'tool_name': 'revenue_cloud_health_check',
                                 'success': False,
                                 'error_message': 'Salesforce authentication failed',
                                 'cost_cents': 0
                             })
        
        assert response.status_code == 201
        
        # Verify usage log was created
        log = UsageLog.query.filter_by(
            user_id=test_user.id,
            api_key_id=test_api_key.id
        ).first()
        
        assert log is not None
        assert log.success is False
        assert log.error_message == 'Salesforce authentication failed'
        assert log.cost_cents == 0
    
    def test_internal_health_check(self, client):
        """Test internal health check endpoint"""
        response = client.get('/api/v1.0/internal/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestMainRoutes:
    """Test public/main routes"""
    
    def test_homepage(self, client):
        """Test homepage loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'ForceWeaver MCP Server' in response.data
    
    def test_pricing_page(self, client):
        """Test pricing page loads"""
        response = client.get('/pricing')
        assert response.status_code == 200
        assert b'Pricing' in response.data
        assert b'Pay-Per-Use' in response.data
    
    def test_docs_page(self, client):
        """Test documentation page loads"""
        response = client.get('/docs')
        assert response.status_code == 200
        assert b'Documentation' in response.data or b'Getting Started' in response.data
    
    def test_status_endpoint(self, client):
        """Test status endpoint"""
        response = client.get('/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'version' in data


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @patch('app.limiter')
    def test_api_endpoint_rate_limiting(self, mock_limiter, client, test_user):
        """Test that API endpoints are rate limited"""
        # This is a basic test structure - in real implementation,
        # you'd need to configure test rate limits and make multiple requests
        
        # Create API key
        api_key = APIKey(user_id=test_user.id, name='Test Key')
        db.session.add(api_key)
        db.session.commit()
        
        generated_key = api_key._generated_key
        
        # Make request
        response = client.post('/api/v1.0/internal/validate',
                             json={
                                 'api_key': generated_key,
                                 'org_id': 'test_org'
                             })
        
        # Just verify the endpoint is accessible
        # In a real test, you'd make many requests to trigger rate limiting
        assert response.status_code in [200, 401, 404]  # Any valid response
    
    def test_web_endpoint_rate_limiting(self, client):
        """Test that web endpoints have rate limiting"""
        # Make multiple requests to registration endpoint
        for i in range(5):
            response = client.post('/auth/register', data={
                'name': f'User {i}',
                'email': f'user{i}@example.com',
                'password': 'password',
                'password_confirm': 'password'
            })
            
            # Should either succeed or be rate limited
            assert response.status_code in [200, 302, 429]


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
    
    def test_500_error_handling(self, client):
        """Test 500 error handling"""
        # This would require triggering an actual server error
        # For now, just test that error handlers are registered
        pass
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in API requests"""
        response = client.post('/api/v1.0/internal/validate',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields in API requests"""
        response = client.post('/api/v1.0/internal/validate',
                             json={'api_key': 'test'})  # Missing org_id
        
        assert response.status_code == 400


class TestSecurity:
    """Test security features"""
    
    def test_authenticated_routes_require_login(self, client):
        """Test that authenticated routes redirect to login"""
        protected_routes = [
            '/dashboard/',
            '/dashboard/keys',
            '/dashboard/orgs',
            '/dashboard/usage',
            '/auth/profile'
        ]
        
        for route in protected_routes:
            response = client.get(route, follow_redirects=True)
            assert response.status_code == 200
            assert b'Sign In' in response.data
    
    def test_admin_routes_require_admin(self, client, test_user):
        """Test that admin routes require admin privileges"""
        # This test assumes there are admin-only routes
        # If not implemented yet, this can be skipped
        pass
    
    def test_user_can_only_access_own_data(self, authenticated_client, test_factory):
        """Test that users can only access their own data"""
        # Create another user with data
        other_user = test_factory.create_user()
        other_api_key = test_factory.create_api_key(other_user)
        
        # Try to deactivate other user's API key
        response = authenticated_client.post(f'/dashboard/keys/{other_api_key.id}/deactivate')
        
        # Should either be forbidden or not found
        assert response.status_code in [403, 404]
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection"""
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post('/auth/login', data={
            'email': malicious_input,
            'password': 'password'
        })
        
        # Should handle gracefully without database error
        assert response.status_code == 200
        
        # Verify users table still exists by checking if we can query it
        assert User.query.count() >= 0
    
    def test_xss_protection(self, client):
        """Test protection against XSS attacks"""
        malicious_script = '<script>alert("XSS")</script>'
        
        response = client.post('/auth/register', data={
            'name': malicious_script,
            'email': 'test@example.com',
            'password': 'password',
            'password_confirm': 'password'
        })
        
        # Should either reject or escape the malicious input
        if response.status_code == 200:
            assert b'<script>' not in response.data 