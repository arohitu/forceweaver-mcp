"""
Salesforce Client for MCP Server
Handles OAuth authentication and Salesforce API calls
"""
import asyncio
import aiohttp
import json
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class SalesforceClient:
    """Async Salesforce API client with OAuth support"""
    
    def __init__(self, instance_url: str, client_id: str, client_secret: str, api_version: str = "v64.0"):
        self.instance_url = instance_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_version = api_version
        
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': 'ForceWeaver-MCP-Server/2.0'}
            )
        return self.session
    
    async def authenticate(self) -> bool:
        """Authenticate using OAuth client credentials flow"""
        try:
            session = await self._get_session()
            
            # Determine the auth URL based on instance
            auth_url = f"{self.instance_url}/services/oauth2/token"
            
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            async with session.post(auth_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result['access_token']
                    
                    logger.info("Salesforce authentication successful")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Salesforce authentication failed {response.status}: {error_text}")
                    return False
        
        except Exception as e:
            logger.error(f"Salesforce authentication error: {e}")
            return False
    
    async def set_tokens(self, access_token: str, refresh_token: Optional[str] = None):
        """Set tokens from cached values"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        logger.info("Using cached Salesforce tokens")
    
    async def refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return await self.authenticate()
        
        try:
            session = await self._get_session()
            
            auth_url = f"{self.instance_url}/services/oauth2/token"
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            async with session.post(auth_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.access_token = result['access_token']
                    logger.info("Access token refreshed successfully")
                    return True
                else:
                    logger.warning("Token refresh failed, falling back to full authentication")
                    return await self.authenticate()
        
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return await self.authenticate()
    
    async def api_call(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make authenticated API call to Salesforce"""
        if not self.access_token:
            if not await self.authenticate():
                raise Exception("Failed to authenticate with Salesforce")
        
        session = await self._get_session()
        
        # Construct full URL
        if endpoint.startswith('/'):
            url = f"{self.instance_url}{endpoint}"
        elif endpoint.startswith('http'):
            url = endpoint
        else:
            url = f"{self.instance_url}/services/data/{self.api_version}/{endpoint}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            kwargs = {'headers': headers}
            if data and method.upper() in ['POST', 'PUT', 'PATCH']:
                kwargs['json'] = data
            
            async with session.request(method, url, **kwargs) as response:
                
                # Handle token expiration
                if response.status == 401:
                    logger.info("Token expired, attempting refresh")
                    if await self.refresh_access_token():
                        # Retry with new token
                        headers['Authorization'] = f'Bearer {self.access_token}'
                        kwargs['headers'] = headers
                        async with session.request(method, url, **kwargs) as retry_response:
                            if retry_response.status < 400:
                                return await retry_response.json()
                            else:
                                error_text = await retry_response.text()
                                raise Exception(f"Salesforce API error {retry_response.status}: {error_text}")
                    else:
                        raise Exception("Failed to refresh Salesforce token")
                
                elif response.status < 400:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Salesforce API error {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            raise Exception(f"HTTP error during Salesforce API call: {e}")
    
    async def get_org_info(self) -> Dict[str, Any]:
        """Get organization information"""
        return await self.api_call('GET', 'sobjects/Organization/describe')
    
    async def query(self, soql: str) -> Dict[str, Any]:
        """Execute SOQL query"""
        return await self.api_call('GET', f"query?q={urlencode({'q': soql})['q']}")
    
    async def get_sobject_describe(self, sobject_name: str) -> Dict[str, Any]:
        """Get sObject description"""
        return await self.api_call('GET', f'sobjects/{sobject_name}/describe')
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        return await self.api_call('GET', 'sobjects/User/' + await self._get_current_user_id())
    
    async def _get_current_user_id(self) -> str:
        """Get current user ID from token info"""
        identity_url = f"{self.instance_url}/services/oauth2/userinfo"
        session = await self._get_session()
        
        headers = {'Authorization': f'Bearer {self.access_token}'}
        async with session.get(identity_url, headers=headers) as response:
            if response.status == 200:
                result = await response.json()
                return result['user_id']
            else:
                raise Exception("Failed to get user info")
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close() 