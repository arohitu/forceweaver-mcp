#!/usr/bin/env python3
"""
ForceWeaver MCP Server - Enhanced with Web App Integration
Integrates with Flask web app for API key validation and credential management
"""
import asyncio
import os
import sys
import time
import logging
from typing import Optional, List, Dict, Any

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp import Application, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import our custom modules
from validation_client import ValidationClient
from salesforce_client import SalesforceClient
from health_checker import RevenueCloudHealthChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ForceWeaverMCPServer:
    """Enhanced ForceWeaver MCP Server with web app integration"""
    
    def __init__(self):
        self.validation_client = ValidationClient()
        self.app = Application()
        
        # Current session data (set during tool calls)
        self.current_user_id: Optional[str] = None
        self.current_api_key_id: Optional[str] = None
        self.current_org_id: Optional[str] = None
        self.current_auth_data: Optional[Dict[str, Any]] = None
        
        # Setup MCP server
        self._setup_server()
    
    def _setup_server(self):
        """Setup MCP server with tools and handlers"""
        
        @self.app.get_server_info()
        async def get_server_info():
            return types.ServerInfo(
                name="ForceWeaver MCP Server",
                version="2.0.0"
            )
        
        @self.app.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="revenue_cloud_health_check",
                    description="Comprehensive Salesforce Revenue Cloud health check and analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "forceweaver_api_key": {
                                "type": "string",
                                "description": "Your ForceWeaver API key (starts with fk_)"
                            },
                            "salesforce_org_id": {
                                "type": "string", 
                                "description": "Salesforce org identifier (e.g., 'production', 'sandbox')"
                            },
                            "check_types": {
                                "type": "array",
                                "description": "Types of checks to perform",
                                "items": {
                                    "type": "string",
                                    "enum": [
                                        "basic_org_info",
                                        "sharing_model", 
                                        "bundle_analysis",
                                        "data_integrity",
                                        "performance_metrics",
                                        "security_audit"
                                    ]
                                },
                                "default": ["basic_org_info", "sharing_model"]
                            },
                            "api_version": {
                                "type": "string",
                                "description": "Salesforce API version to use",
                                "default": "v64.0"
                            }
                        },
                        "required": ["forceweaver_api_key", "salesforce_org_id"]
                    }
                )
            ]
        
        @self.app.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            
            if name == "revenue_cloud_health_check":
                return await self._handle_health_check(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_health_check(self, arguments: dict) -> list[types.TextContent]:
        """Handle revenue cloud health check tool call"""
        start_time = time.time()
        
        # Extract parameters
        api_key = arguments.get("forceweaver_api_key")
        org_id = arguments.get("salesforce_org_id")
        check_types = arguments.get("check_types", ["basic_org_info", "sharing_model"])
        api_version = arguments.get("api_version", "v64.0")
        
        # Validate required parameters
        if not api_key:
            error_msg = "ForceWeaver API key is required"
            await self._log_usage_if_possible("revenue_cloud_health_check", False, error_message=error_msg)
            return [types.TextContent(
                type="text",
                text=f"❌ Error: {error_msg}\n\nPlease provide your ForceWeaver API key. Get one from: https://mcp.forceweaver.com/dashboard/keys"
            )]
        
        if not org_id:
            error_msg = "Salesforce org identifier is required"
            await self._log_usage_if_possible("revenue_cloud_health_check", False, error_message=error_msg)
            return [types.TextContent(
                type="text", 
                text=f"❌ Error: {error_msg}\n\nPlease specify which Salesforce org to check (e.g., 'production', 'sandbox')"
            )]
        
        try:
            # Validate API key and get Salesforce credentials
            auth_data = await self.validation_client.validate_api_key(api_key, org_id)
            
            if not auth_data:
                error_msg = "Invalid API key or Salesforce org not found"
                return [types.TextContent(
                    type="text",
                    text=f"❌ Authentication Error: {error_msg}\n\n" +
                         f"Please check:\n" +
                         f"1. Your API key is correct: {api_key[:10]}...\n" +
                         f"2. Salesforce org '{org_id}' exists in your account\n" +
                         f"3. Visit https://mcp.forceweaver.com/dashboard to manage your credentials"
                )]
            
            # Store auth data for logging
            self.current_user_id = auth_data["user_id"]
            self.current_api_key_id = auth_data["api_key_id"]
            self.current_org_id = auth_data["org_id"]
            self.current_auth_data = auth_data
            
            # Get Salesforce credentials
            sf_creds = auth_data["salesforce_credentials"]
            
            # Create Salesforce client
            sf_client = SalesforceClient(
                instance_url=sf_creds["instance_url"],
                client_id=sf_creds["client_id"],
                client_secret=sf_creds["client_secret"],
                api_version=api_version
            )
            
            # Authenticate with Salesforce
            if "access_token" in sf_creds and sf_creds["access_token"]:
                # Use cached tokens if available
                await sf_client.set_tokens(
                    access_token=sf_creds["access_token"],
                    refresh_token=sf_creds.get("refresh_token")
                )
            else:
                # Perform OAuth client credentials flow
                await sf_client.authenticate()
            
            # Create health checker
            health_checker = RevenueCloudHealthChecker(sf_client)
            
            # Perform health checks
            results = await health_checker.run_checks(check_types)
            
            # Calculate execution time
            execution_time = int((time.time() - start_time) * 1000)
            
            # Log successful usage
            await self._log_usage(
                "revenue_cloud_health_check",
                success=True,
                execution_time_ms=execution_time,
                cost_cents=self._calculate_cost(check_types)
            )
            
            # Format results
            formatted_results = self._format_health_check_results(results, sf_creds, execution_time)
            
            return [types.TextContent(
                type="text",
                text=formatted_results
            )]
        
        except Exception as e:
            error_msg = str(e)
            execution_time = int((time.time() - start_time) * 1000)
            
            logger.error(f"Health check failed: {e}")
            
            # Log failed usage
            await self._log_usage(
                "revenue_cloud_health_check",
                success=False,
                execution_time_ms=execution_time,
                error_message=error_msg
            )
            
            return [types.TextContent(
                type="text",
                text=f"❌ Error during health check: {error_msg}\n\n" +
                     f"If this problem persists, please contact support or check your Salesforce credentials at https://mcp.forceweaver.com/dashboard/orgs"
            )]
    
    def _format_health_check_results(self, results: dict, sf_creds: dict, execution_time: int) -> str:
        """Format health check results for display"""
        output = []
        
        # Header
        org_name = sf_creds.get("org_name", "Unknown Organization")
        org_type = "Sandbox" if sf_creds.get("is_sandbox") else "Production"
        
        output.append("🔍 **ForceWeaver Revenue Cloud Health Check Report**")
        output.append("=" * 60)
        output.append(f"📊 Organization: {org_name} ({org_type})")
        output.append(f"⏱️  Execution Time: {execution_time}ms")
        output.append(f"📅 Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        output.append("")
        
        # Overall health score
        if "overall_score" in results:
            score = results["overall_score"]
            grade = self._get_health_grade(score)
            output.append(f"🎯 **Overall Health Score: {score}% (Grade: {grade})**")
            output.append("")
        
        # Individual check results
        for check_type, check_result in results.items():
            if check_type == "overall_score":
                continue
                
            output.append(f"### {check_type.replace('_', ' ').title()}")
            
            if isinstance(check_result, dict):
                if "status" in check_result:
                    status_emoji = "✅" if check_result["status"] == "healthy" else "⚠️" if check_result["status"] == "warning" else "❌"
                    output.append(f"{status_emoji} Status: {check_result['status'].title()}")
                
                if "score" in check_result:
                    output.append(f"📈 Score: {check_result['score']}%")
                
                if "details" in check_result:
                    for detail in check_result["details"]:
                        output.append(f"   • {detail}")
                
                if "recommendations" in check_result:
                    output.append("💡 Recommendations:")
                    for rec in check_result["recommendations"]:
                        output.append(f"   ➤ {rec}")
            
            output.append("")
        
        # Footer
        output.append("---")
        output.append("🔗 Manage your ForceWeaver settings: https://mcp.forceweaver.com/dashboard")
        
        return "\n".join(output)
    
    def _get_health_grade(self, score: int) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _calculate_cost(self, check_types: List[str]) -> int:
        """Calculate cost in cents based on check types"""
        # Basic pricing: 1 cent per check type
        base_cost = len(check_types) * 1
        
        # Premium checks cost more
        premium_checks = ["security_audit", "performance_metrics"]
        premium_count = sum(1 for check in check_types if check in premium_checks)
        premium_cost = premium_count * 4  # 5 cents total for premium checks
        
        return base_cost + premium_cost
    
    async def _log_usage(self, tool_name: str, success: bool = True, 
                        execution_time_ms: Optional[int] = None,
                        error_message: Optional[str] = None, 
                        cost_cents: int = 1):
        """Log usage to the web app"""
        if not all([self.current_user_id, self.current_api_key_id]):
            logger.warning("Cannot log usage: missing authentication data")
            return
        
        try:
            await self.validation_client.log_usage(
                user_id=self.current_user_id,
                api_key_id=self.current_api_key_id,
                tool_name=tool_name,
                success=success,
                execution_time_ms=execution_time_ms,
                error_message=error_message,
                cost_cents=cost_cents,
                salesforce_org_id=self.current_org_id
            )
        except Exception as e:
            logger.error(f"Failed to log usage: {e}")
    
    async def _log_usage_if_possible(self, tool_name: str, success: bool,
                                   error_message: Optional[str] = None):
        """Log usage if we have enough information"""
        try:
            if self.current_user_id and self.current_api_key_id:
                await self._log_usage(tool_name, success, error_message=error_message)
        except Exception:
            pass  # Don't let logging errors affect the main flow
    
    async def run(self):
        """Run the MCP server"""
        try:
            logger.info("Starting ForceWeaver MCP Server (Enhanced)")
            
            # Check if validation service is available
            if not await self.validation_client.health_check():
                logger.warning("Validation service is not available - some features may not work")
            
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.app.run(
                    read_stream, write_stream, InitializationOptions(
                        server_name="ForceWeaver MCP Server",
                        server_version="2.0.0",
                        capabilities={
                            "tools": {}
                        }
                    )
                )
        
        finally:
            await self.validation_client.close()

async def main():
    """Main entry point"""
    server = ForceWeaverMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main()) 