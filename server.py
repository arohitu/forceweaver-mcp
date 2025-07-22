#!/usr/bin/env python3
"""
ForceWeaver MCP Server
A Model Context Protocol compliant server for Salesforce Revenue Cloud health checking.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Union

import anyio
from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolRequest,
    ErrorCode,
    ListToolsRequest,
    McpError,
    Tool,
    TextContent,
    CallToolResult,
    ListToolsResult,
)

# Import our business logic
from services.salesforce_service import SalesforceConnectionManager, SalesforceAPIClient
from services.health_checker_service import RevenueCloudHealthChecker

# Configure logging to stderr (stdout is reserved for JSON-RPC)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("forceweaver")

# Global connection manager
connection_manager = None

def get_connection_from_env() -> dict:
    """Get Salesforce connection details from environment variables."""
    required_vars = [
        'SALESFORCE_INSTANCE_URL',
        'SALESFORCE_ACCESS_TOKEN',
        'SALESFORCE_REFRESH_TOKEN',
        'SALESFORCE_ORG_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return {
        'instance_url': os.getenv('SALESFORCE_INSTANCE_URL'),
        'access_token': os.getenv('SALESFORCE_ACCESS_TOKEN'),
        'refresh_token': os.getenv('SALESFORCE_REFRESH_TOKEN'),
        'org_id': os.getenv('SALESFORCE_ORG_ID'),
        'api_version': os.getenv('SALESFORCE_API_VERSION', 'v64.0')
    }

@mcp.tool()
async def revenue_cloud_health_check(
    check_types: Optional[List[str]] = None,
    api_version: Optional[str] = None
) -> str:
    """
    Perform a comprehensive health check on Salesforce Revenue Cloud configuration.
    
    Analyzes org settings, sharing models, bundle configurations, and data integrity.
    
    Args:
        check_types: Specific types of checks to perform. Options:
            - basic_org_info: Organization details and basic settings
            - sharing_model: OWD settings and sharing rules
            - bundle_analysis: Product bundle configuration
            - attribute_integrity: Picklist validation and data integrity
            If not specified, all checks will be performed.
        api_version: Salesforce API version to use (e.g., 'v64.0').
            If not specified, uses the configured version.
    
    Returns:
        Formatted health check results with scores, grades, and recommendations.
    """
    try:
        logger.info(f"Starting health check with check_types: {check_types}, api_version: {api_version}")
        
        # Get Salesforce connection from environment
        connection_config = get_connection_from_env()
        
        # Use provided API version or default
        effective_api_version = api_version or connection_config['api_version']
        
        # Create Salesforce client
        sf_client = SalesforceAPIClient(
            instance_url=connection_config['instance_url'],
            access_token=connection_config['access_token'],
            api_version=effective_api_version
        )
        
        # Validate connection
        try:
            org_info = sf_client.get_org_info()
            logger.info(f"Connected to Salesforce org: {org_info.get('Name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to connect to Salesforce: {e}")
            return f"❌ Failed to connect to Salesforce: {str(e)}"
        
        # Run health checks
        checker = RevenueCloudHealthChecker(sf_client)
        
        # Validate check types if provided
        valid_check_types = [
            'basic_org_info', 
            'sharing_model', 
            'bundle_analysis', 
            'attribute_integrity'
        ]
        
        if check_types:
            invalid_types = [ct for ct in check_types if ct not in valid_check_types]
            if invalid_types:
                return f"❌ Invalid check types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_check_types)}"
            
            # Run specific checks only
            for check_type in check_types:
                if check_type == 'basic_org_info':
                    checker.run_basic_org_info_check()
                elif check_type == 'sharing_model':
                    checker.run_owd_sharing_check()
                elif check_type == 'bundle_analysis':
                    checker.run_optimized_bundle_checks()
                elif check_type == 'attribute_integrity':
                    checker.run_attribute_picklist_integrity_check()
            
            # Get the results summary after running specific checks
            results = checker._calculate_health_score()
        else:
            # Run all checks (default behavior)
            results = checker.run_all_checks()
        
        # Format results for display
        return format_health_check_results(results, connection_config['org_id'], effective_api_version)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return f"❌ Health check failed: {str(e)}"

def format_health_check_results(results: dict, org_id: str, api_version: str) -> str:
    """Format health check results into a readable string."""
    checks_data = results.get('checks', {})
    overall_health = results.get('overall_health', {})
    
    # Build status summary
    lines = [
        "✅ Revenue Cloud Health Check Completed",
        "",
        f"📊 Overall Health Score: {overall_health.get('score', 0)}% (Grade: {overall_health.get('grade', 'F')}) ",
        "",
        f"🏢 Organization: {org_id}",
        f"📡 API Version: {api_version}",
        "",
    ]
    
    summary = overall_health.get('summary', {})
    lines.extend([
        "📋 Summary:",
        f"   • Total Checks: {summary.get('total_checks', 0)}",
        f"   • Passed: {summary.get('ok', 0)}",
        f"   • Warnings: {summary.get('warnings', 0)}",
        f"   • Errors: {summary.get('errors', 0)}",
        "",
    ])
    
    # Add individual check results
    lines.append("🔍 Individual Check Results:")
    for check_name, check_data in checks_data.items():
        status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(check_data.get('status'), "❓")
        check_title = check_name.replace('_', ' ').title()
        lines.append(f"   {status_icon} {check_title}: {check_data.get('status', 'unknown').upper()}")
        if check_data.get('message'):
            lines.append(f"      └─ {check_data['message']}")
    
    return "\n".join(lines)

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting ForceWeaver MCP Server")
    
    try:
        # Validate environment configuration
        get_connection_from_env()
        logger.info("Environment configuration validated")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Required environment variables:")
        logger.info("  - SALESFORCE_INSTANCE_URL")
        logger.info("  - SALESFORCE_ACCESS_TOKEN")
        logger.info("  - SALESFORCE_REFRESH_TOKEN")
        logger.info("  - SALESFORCE_ORG_ID")
        logger.info("  - SALESFORCE_API_VERSION (optional, defaults to v64.0)")
        sys.exit(1)
    
    # Run the MCP server with STDIO transport
    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main()) 