"""
Salesforce Service for MCP Server
Simplified version without Flask dependencies.
"""

import logging
import os
from typing import Dict, Any, Optional
from simple_salesforce import Salesforce
import requests

logger = logging.getLogger(__name__)


class SalesforceAPIClient:
    """Simplified Salesforce API client for MCP server."""
    
    def __init__(self, instance_url: str, access_token: str, api_version: str = "v64.0"):
        """Initialize the Salesforce client."""
        self.instance_url = instance_url.rstrip('/')
        self.access_token = access_token
        self.api_version = api_version
        
        # Create simple-salesforce instance
        self.sf = Salesforce(
            instance_url=instance_url,
            session_id=access_token,
            version=api_version.replace('v', '').replace('.0', '')
        )
    
    def get_org_info(self) -> Dict[str, Any]:
        """Get basic organization information."""
        try:
            # Query organization information
            result = self.sf.query("SELECT Id, Name, OrganizationType, InstanceName, Country FROM Organization LIMIT 1")
            if result['records']:
                return result['records'][0]
            else:
                return {'Name': 'Unknown Organization'}
        except Exception as e:
            logger.error(f"Failed to get org info: {e}")
            raise
    
    def query(self, soql: str) -> Dict[str, Any]:
        """Execute a SOQL query."""
        try:
            return self.sf.query(soql)
        except Exception as e:
            logger.error(f"SOQL query failed: {soql} - Error: {e}")
            raise
    
    def query_all(self, soql: str) -> Dict[str, Any]:
        """Execute a SOQL query with automatic pagination."""
        try:
            return self.sf.query_all(soql)
        except Exception as e:
            logger.error(f"SOQL query_all failed: {soql} - Error: {e}")
            raise
    
    def describe_sobject(self, sobject_type: str) -> Dict[str, Any]:
        """Describe an SObject type."""
        try:
            sobject = getattr(self.sf, sobject_type)
            return sobject.describe()
        except Exception as e:
            logger.error(f"Failed to describe {sobject_type}: {e}")
            raise
    
    def get_sobject(self, sobject_type: str, record_id: str) -> Dict[str, Any]:
        """Get a specific record."""
        try:
            sobject = getattr(self.sf, sobject_type)
            return sobject.get(record_id)
        except Exception as e:
            logger.error(f"Failed to get {sobject_type} record {record_id}: {e}")
            raise


class SalesforceConnectionManager:
    """Simplified connection manager for MCP server."""
    
    @staticmethod
    def create_client_from_env() -> SalesforceAPIClient:
        """Create a Salesforce client from environment variables."""
        instance_url = os.getenv('SALESFORCE_INSTANCE_URL')
        access_token = os.getenv('SALESFORCE_ACCESS_TOKEN')
        api_version = os.getenv('SALESFORCE_API_VERSION', 'v64.0')
        
        if not instance_url or not access_token:
            raise ValueError("Missing required Salesforce credentials in environment")
        
        return SalesforceAPIClient(instance_url, access_token, api_version)
    
    @staticmethod
    def refresh_token_if_needed(refresh_token: str, client_id: str, client_secret: str) -> Optional[Dict[str, str]]:
        """Refresh Salesforce access token if needed."""
        try:
            token_url = "https://login.salesforce.com/services/oauth2/token"
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': client_id,
                'client_secret': client_secret
            }
            
            response = requests.post(token_url, data=data)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token refresh failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None 