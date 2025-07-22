"""
Validation Client for MCP Server
Handles API key validation and credential retrieval from the web app
"""
import asyncio
import aiohttp
import json
import time
from typing import Optional, Dict, Any
import os
import logging

class ValidationClient:
    """Client for validating API keys and retrieving Salesforce credentials"""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.environ.get('VALIDATION_URL', 'http://localhost:5000')
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache = {}  # Simple in-memory cache
        self.cache_ttl = 300  # 5 minutes cache
        self.logger = logging.getLogger(__name__)
    
    async def _get_session(self):
        """Get or create HTTP session"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': 'ForceWeaver-MCP-Server/1.0'}
            )
        return self.session
    
    async def validate_api_key(self, api_key: str, org_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate API key and get Salesforce credentials
        Returns None if invalid, credentials dict if valid
        """
        # Check cache first
        cache_key = f"{api_key}:{org_id}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data['timestamp'] < self.cache_ttl:
                self.logger.debug("Using cached validation result")
                return cached_data['data']
        
        try:
            session = await self._get_session()
            
            validation_data = {
                'api_key': api_key,
                'org_id': org_id
            }
            
            async with session.post(
                f"{self.base_url}/api/v1.0/internal/validate",
                json=validation_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Cache successful validation
                    self.cache[cache_key] = {
                        'data': result,
                        'timestamp': time.time()
                    }
                    
                    self.logger.info(f"API key validation successful for user {result.get('user_id')}")
                    return result
                
                elif response.status == 401:
                    error_data = await response.json()
                    self.logger.warning(f"API key validation failed: {error_data.get('message')}")
                    return None
                
                elif response.status == 404:
                    error_data = await response.json()
                    self.logger.warning(f"Salesforce org not found: {error_data.get('message')}")
                    return None
                
                else:
                    error_text = await response.text()
                    self.logger.error(f"Validation API error {response.status}: {error_text}")
                    return None
        
        except asyncio.TimeoutError:
            self.logger.error("Validation request timed out")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"Validation request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}")
            return None
    
    async def log_usage(self, user_id: str, api_key_id: str, tool_name: str, 
                       success: bool = True, execution_time_ms: Optional[int] = None,
                       error_message: Optional[str] = None, cost_cents: int = 1,
                       salesforce_org_id: Optional[str] = None) -> bool:
        """
        Log usage to the web app
        Returns True if successful, False otherwise
        """
        try:
            session = await self._get_session()
            
            usage_data = {
                'user_id': user_id,
                'api_key_id': api_key_id,
                'tool_name': tool_name,
                'success': success,
                'execution_time_ms': execution_time_ms,
                'error_message': error_message,
                'cost_cents': cost_cents,
                'salesforce_org_id': salesforce_org_id
            }
            
            async with session.post(
                f"{self.base_url}/api/v1.0/internal/usage",
                json=usage_data
            ) as response:
                
                if response.status == 201:
                    self.logger.debug("Usage logged successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Usage logging failed {response.status}: {error_text}")
                    return False
        
        except Exception as e:
            self.logger.error(f"Usage logging error: {e}")
            return False
    
    async def health_check(self) -> bool:
        """
        Check if the validation service is healthy
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/api/v1.0/internal/health") as response:
                return response.status == 200
        
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close() 