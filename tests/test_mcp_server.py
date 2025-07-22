"""
Tests for MCP server functionality
"""
import asyncio
import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
from mcp import types

# Import MCP server components
from mcp_server.enhanced_server import ForceWeaverMCPServer
from mcp_server.validation_client import ValidationClient
from mcp_server.salesforce_client import SalesforceClient
from mcp_server.health_checker import RevenueCloudHealthChecker


class TestValidationClient:
    """Test ValidationClient functionality"""
    
    @pytest.fixture
    def validation_client(self):
        """Create a ValidationClient instance"""
        return ValidationClient(base_url='http://localhost:5000')
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, validation_client):
        """Test successful API key validation"""
        mock_response_data = {
            'user_id': 'user123',
            'api_key_id': 'key123',
            'org_id': 'org123',
            'salesforce_credentials': {
                'instance_url': 'https://test.my.salesforce.com',
                'client_id': 'test_client_id',
                'client_secret': 'test_secret',
                'org_name': 'Test Org'
            }
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Setup mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_context
            
            # Test validation
            result = await validation_client.validate_api_key('fk_test_key', 'production')
            
            assert result is not None
            assert result['user_id'] == 'user123'
            assert result['api_key_id'] == 'key123'
            assert 'salesforce_credentials' in result
    
    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, validation_client):
        """Test API key validation with invalid key"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Setup mock response for invalid key
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.json = AsyncMock(return_value={'message': 'Invalid API key'})
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_context
            
            # Test validation
            result = await validation_client.validate_api_key('invalid_key', 'production')
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_validate_api_key_caching(self, validation_client):
        """Test API key validation caching"""
        mock_response_data = {
            'user_id': 'user123',
            'api_key_id': 'key123',
            'org_id': 'org123',
            'salesforce_credentials': {}
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_context
            
            # First call
            result1 = await validation_client.validate_api_key('fk_test_key', 'production')
            
            # Second call should use cache (no additional HTTP request)
            result2 = await validation_client.validate_api_key('fk_test_key', 'production')
            
            assert result1 == result2
            assert mock_post.call_count == 1  # Only called once due to caching
    
    @pytest.mark.asyncio
    async def test_log_usage_success(self, validation_client):
        """Test successful usage logging"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_context
            
            # Test logging
            result = await validation_client.log_usage(
                user_id='user123',
                api_key_id='key123',
                tool_name='test_tool',
                success=True,
                execution_time_ms=1500,
                cost_cents=5
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_health_check(self, validation_client):
        """Test health check"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_get.return_value = mock_context
            
            # Test health check
            result = await validation_client.health_check()
            
            assert result is True


class TestSalesforceClient:
    """Test SalesforceClient functionality"""
    
    @pytest.fixture
    def sf_client(self):
        """Create a SalesforceClient instance"""
        return SalesforceClient(
            instance_url='https://test.my.salesforce.com',
            client_id='test_client_id',
            client_secret='test_client_secret'
        )
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, sf_client):
        """Test successful Salesforce authentication"""
        mock_auth_response = {
            'access_token': 'mock_access_token',
            'token_type': 'Bearer'
        }
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_auth_response)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_context
            
            # Test authentication
            result = await sf_client.authenticate()
            
            assert result is True
            assert sf_client.access_token == 'mock_access_token'
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self, sf_client):
        """Test failed Salesforce authentication"""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_response.text = AsyncMock(return_value='Authentication failed')
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_post.return_value = mock_context
            
            # Test authentication
            result = await sf_client.authenticate()
            
            assert result is False
            assert sf_client.access_token is None
    
    @pytest.mark.asyncio
    async def test_api_call_success(self, sf_client):
        """Test successful API call"""
        sf_client.access_token = 'test_token'
        
        mock_api_response = {
            'records': [{'Id': '001', 'Name': 'Test Account'}],
            'totalSize': 1
        }
        
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_api_response)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_request.return_value = mock_context
            
            # Test API call
            result = await sf_client.api_call('GET', 'query?q=SELECT Id FROM Account LIMIT 1')
            
            assert result == mock_api_response
            assert result['totalSize'] == 1
    
    @pytest.mark.asyncio
    async def test_api_call_token_refresh(self, sf_client):
        """Test API call with token refresh"""
        sf_client.access_token = 'expired_token'
        sf_client.refresh_token = 'refresh_token'
        
        # Mock token refresh response
        mock_refresh_response = {
            'access_token': 'new_access_token'
        }
        
        mock_api_response = {
            'records': [],
            'totalSize': 0
        }
        
        with patch('aiohttp.ClientSession.request') as mock_request, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            # First call returns 401, second call succeeds
            mock_401_response = AsyncMock()
            mock_401_response.status = 401
            
            mock_success_response = AsyncMock()
            mock_success_response.status = 200
            mock_success_response.json = AsyncMock(return_value=mock_api_response)
            
            mock_refresh_resp = AsyncMock()
            mock_refresh_resp.status = 200
            mock_refresh_resp.json = AsyncMock(return_value=mock_refresh_response)
            
            # Setup context managers
            mock_401_context = AsyncMock()
            mock_401_context.__aenter__ = AsyncMock(return_value=mock_401_response)
            mock_401_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_success_context = AsyncMock()
            mock_success_context.__aenter__ = AsyncMock(return_value=mock_success_response)
            mock_success_context.__aexit__ = AsyncMock(return_value=None)
            
            mock_refresh_context = AsyncMock()
            mock_refresh_context.__aenter__ = AsyncMock(return_value=mock_refresh_resp)
            mock_refresh_context.__aexit__ = AsyncMock(return_value=None)
            
            # First request returns 401, second request succeeds
            mock_request.side_effect = [mock_401_context, mock_success_context]
            mock_post.return_value = mock_refresh_context
            
            # Test API call
            result = await sf_client.api_call('GET', 'query?q=SELECT Id FROM Account LIMIT 1')
            
            assert result == mock_api_response
            assert sf_client.access_token == 'new_access_token'
    
    @pytest.mark.asyncio
    async def test_query_method(self, sf_client):
        """Test SOQL query method"""
        sf_client.access_token = 'test_token'
        
        with patch.object(sf_client, 'api_call') as mock_api_call:
            mock_api_call.return_value = {'records': [], 'totalSize': 0}
            
            await sf_client.query('SELECT Id FROM Account')
            
            mock_api_call.assert_called_once()
            args = mock_api_call.call_args[0]
            assert 'query?q=' in args[1]


class TestRevenueCloudHealthChecker:
    """Test RevenueCloudHealthChecker functionality"""
    
    @pytest.fixture
    def mock_sf_client(self):
        """Create a mock SalesforceClient"""
        return Mock(spec=SalesforceClient)
    
    @pytest.fixture
    def health_checker(self, mock_sf_client):
        """Create a RevenueCloudHealthChecker instance"""
        return RevenueCloudHealthChecker(mock_sf_client)
    
    @pytest.mark.asyncio
    async def test_basic_org_info_check(self, health_checker, mock_sf_client, mock_org_query_response):
        """Test basic org info health check"""
        mock_sf_client.query = AsyncMock(return_value=mock_org_query_response)
        
        result = await health_checker._check_basic_org_info()
        
        assert result['status'] in ['healthy', 'warning', 'critical']
        assert 'score' in result
        assert 'details' in result
        assert isinstance(result['details'], list)
        assert len(result['details']) > 0
    
    @pytest.mark.asyncio
    async def test_sharing_model_check(self, health_checker, mock_sf_client):
        """Test sharing model health check"""
        # Mock organization-wide defaults response
        mock_owd_response = {
            'records': [{
                'SobjectType': 'Account',
                'DefaultAccountAccess': 'Private'
            }],
            'totalSize': 1
        }
        
        mock_sharing_rules_response = {
            'totalSize': 5
        }
        
        mock_sf_client.query = AsyncMock(side_effect=[mock_owd_response, mock_sharing_rules_response])
        
        result = await health_checker._check_sharing_model()
        
        assert result['status'] in ['healthy', 'warning', 'critical']
        assert 'score' in result
        assert 'details' in result
    
    @pytest.mark.asyncio
    async def test_bundle_analysis_check(self, health_checker, mock_sf_client):
        """Test bundle analysis health check"""
        # Mock count responses for different objects
        mock_count_responses = [
            {'totalSize': 10},  # Products
            {'totalSize': 15},  # PricebookEntries
            {'totalSize': 5},   # Quotes
            {'totalSize': 8},   # QuoteLineItems
            {'totalSize': 3},   # Contracts
            {'totalSize': 12},  # Orders
            {'totalSize': 20}   # OrderItems
        ]
        
        mock_sf_client.query = AsyncMock(side_effect=mock_count_responses)
        
        result = await health_checker._check_bundle_analysis()
        
        assert result['status'] in ['healthy', 'warning', 'critical']
        assert 'score' in result
        assert 'details' in result
    
    @pytest.mark.asyncio
    async def test_data_integrity_check(self, health_checker, mock_sf_client):
        """Test data integrity health check"""
        # Mock responses for integrity checks
        mock_responses = [
            {'totalSize': 2},   # Duplicate accounts
            {'totalSize': 0},   # Missing close dates
            {'totalSize': 1}    # Orphaned contacts
        ]
        
        mock_sf_client.query = AsyncMock(side_effect=mock_responses)
        
        result = await health_checker._check_data_integrity()
        
        assert result['status'] in ['healthy', 'warning', 'critical']
        assert 'score' in result
        assert 'details' in result
        assert 'recommendations' in result
    
    @pytest.mark.asyncio
    async def test_run_checks_multiple_types(self, health_checker, mock_sf_client, mock_org_query_response):
        """Test running multiple check types"""
        # Mock various responses
        mock_sf_client.query = AsyncMock(return_value=mock_org_query_response)
        
        check_types = ['basic_org_info', 'sharing_model']
        results = await health_checker.run_checks(check_types)
        
        assert 'basic_org_info' in results
        assert 'sharing_model' in results
        assert 'overall_score' in results
        
        # Verify each check has required fields
        for check_type in check_types:
            check_result = results[check_type]
            assert 'status' in check_result
            assert 'score' in check_result
    
    @pytest.mark.asyncio
    async def test_run_checks_with_error(self, health_checker, mock_sf_client):
        """Test handling of check errors"""
        mock_sf_client.query = AsyncMock(side_effect=Exception('Salesforce API error'))
        
        results = await health_checker.run_checks(['basic_org_info'])
        
        assert 'basic_org_info' in results
        
        check_result = results['basic_org_info']
        assert check_result['status'] == 'error'
        assert check_result['score'] == 0
        assert 'error' in check_result


class TestForceWeaverMCPServer:
    """Test ForceWeaverMCPServer functionality"""
    
    @pytest.fixture
    def mcp_server(self):
        """Create a ForceWeaverMCPServer instance"""
        with patch.object(ValidationClient, '__init__', return_value=None):
            server = ForceWeaverMCPServer()
            server.validation_client = Mock(spec=ValidationClient)
            return server
    
    @pytest.mark.asyncio
    async def test_handle_health_check_success(self, mcp_server):
        """Test successful health check tool call"""
        # Mock validation response
        mock_auth_data = {
            'user_id': 'user123',
            'api_key_id': 'key123',
            'org_id': 'org123',
            'salesforce_credentials': {
                'instance_url': 'https://test.my.salesforce.com',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret'
            }
        }
        
        # Mock health check results
        mock_health_results = {
            'basic_org_info': {
                'status': 'healthy',
                'score': 85,
                'details': ['Organization: Test Org'],
                'recommendations': []
            },
            'overall_score': 85
        }
        
        mcp_server.validation_client.validate_api_key = AsyncMock(return_value=mock_auth_data)
        mcp_server.validation_client.log_usage = AsyncMock(return_value=True)
        
        # Mock Salesforce client and health checker
        with patch('mcp_server.enhanced_server.SalesforceClient') as mock_sf_client_class, \
             patch('mcp_server.enhanced_server.RevenueCloudHealthChecker') as mock_health_checker_class:
            
            mock_sf_client = AsyncMock()
            mock_sf_client_class.return_value = mock_sf_client
            
            mock_health_checker = AsyncMock()
            mock_health_checker.run_checks = AsyncMock(return_value=mock_health_results)
            mock_health_checker_class.return_value = mock_health_checker
            
            # Test tool call
            arguments = {
                'forceweaver_api_key': 'fk_test_key',
                'salesforce_org_id': 'production',
                'check_types': ['basic_org_info']
            }
            
            result = await mcp_server._handle_health_check(arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Health Check Report" in result[0].text
            assert "Overall Health Score: 85%" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_health_check_invalid_api_key(self, mcp_server):
        """Test health check with invalid API key"""
        mcp_server.validation_client.validate_api_key = AsyncMock(return_value=None)
        
        arguments = {
            'forceweaver_api_key': 'invalid_key',
            'salesforce_org_id': 'production'
        }
        
        result = await mcp_server._handle_health_check(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Authentication Error" in result[0].text
        assert "Invalid API key" in result[0].text
    
    @pytest.mark.asyncio
    async def test_handle_health_check_missing_parameters(self, mcp_server):
        """Test health check with missing required parameters"""
        arguments = {
            'salesforce_org_id': 'production'
            # Missing forceweaver_api_key
        }
        
        result = await mcp_server._handle_health_check(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Error" in result[0].text
        assert "API key is required" in result[0].text
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, mcp_server):
        """Test cost calculation for different check types"""
        # Test basic checks
        basic_cost = mcp_server._calculate_cost(['basic_org_info', 'sharing_model'])
        assert basic_cost == 2  # 1 cent each
        
        # Test premium checks
        premium_cost = mcp_server._calculate_cost(['performance_metrics', 'security_audit'])
        assert premium_cost == 10  # 5 cents each
        
        # Test mixed checks
        mixed_cost = mcp_server._calculate_cost(['basic_org_info', 'performance_metrics'])
        assert mixed_cost == 6  # 1 + 5 cents
    
    def test_health_grade_calculation(self, mcp_server):
        """Test health grade calculation"""
        assert mcp_server._get_health_grade(95) == "A"
        assert mcp_server._get_health_grade(85) == "B"
        assert mcp_server._get_health_grade(75) == "C"
        assert mcp_server._get_health_grade(65) == "D"
        assert mcp_server._get_health_grade(45) == "F"
    
    @pytest.mark.asyncio
    async def test_format_health_check_results(self, mcp_server):
        """Test health check results formatting"""
        mock_results = {
            'basic_org_info': {
                'status': 'healthy',
                'score': 85,
                'details': ['Organization: Test Org', 'Users: 10'],
                'recommendations': ['Consider adding more users']
            },
            'overall_score': 85
        }
        
        mock_sf_creds = {
            'org_name': 'Test Organization',
            'is_sandbox': False
        }
        
        formatted = mcp_server._format_health_check_results(mock_results, mock_sf_creds, 1500)
        
        assert "ForceWeaver Revenue Cloud Health Check Report" in formatted
        assert "Overall Health Score: 85% (Grade: B)" in formatted
        assert "Organization: Test Organization (Production)" in formatted
        assert "Execution Time: 1500ms" in formatted
        assert "Basic Org Info" in formatted
        assert "Status: Healthy" in formatted
        assert "Consider adding more users" in formatted 