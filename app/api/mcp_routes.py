from flask import Blueprint, request, jsonify, g
from app.core.security import require_api_key
from app.services.salesforce_service import get_salesforce_api_client, update_connection_api_versions
from app.services.health_checker_service import RevenueCloudHealthChecker
import logging

mcp_bp = Blueprint('mcp', __name__)

# Debug endpoints removed for security reasons in production

# Debug endpoint removed for production security

@mcp_bp.route('/call-tool', methods=['POST'])
@require_api_key
def call_tool():
    """MCP-compliant tool invocation endpoint for AI agents."""
    try:
        # Parse the MCP tool call request
        data = request.get_json()
        if not data:
            return jsonify({
                "error": "Request body must be valid JSON",
                "error_type": "InvalidRequest"
            }), 400
        
        tool_name = data.get('name')
        arguments = data.get('arguments', {})
        
        if not tool_name:
            return jsonify({
                "error": "Tool name is required",
                "error_type": "InvalidRequest"
            }), 400
        
        # Route to the appropriate tool handler
        if tool_name == 'revenue_cloud_health_check':
            return handle_health_check_tool(arguments)
        else:
            return jsonify({
                "error": f"Unknown tool: {tool_name}",
                "error_type": "ToolNotFound"
            }), 404
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Tool call failed: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Tool execution failed: {str(e)}",
            "error_type": "ToolExecutionError"
        }), 500

def handle_health_check_tool(arguments):
    """Handle the revenue_cloud_health_check tool with MCP parameters."""
    try:
        # g.customer is attached by the decorator
        connection = g.customer.salesforce_connection
        if not connection:
            return jsonify({
                "error": "No Salesforce connection found for this customer.",
                "error_type": "ConfigurationError"
            }), 400

        # Extract and validate MCP tool arguments
        check_types = arguments.get('check_types', [])
        api_version = arguments.get('api_version')
        
        # Validate check_types if provided
        valid_check_types = [
            'basic_org_info', 
            'sharing_model', 
            'bundle_analysis', 
            'attribute_integrity'
        ]
        
        if check_types:
            invalid_types = [ct for ct in check_types if ct not in valid_check_types]
            if invalid_types:
                return jsonify({
                    "error": f"Invalid check types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_check_types)}",
                    "error_type": "InvalidArgument"
                }), 400

        # Ensure we have API versions available (fetch if needed)
        try:
            update_connection_api_versions(connection)
        except Exception as e:
            # Log but don't fail - we can still proceed with default version
            logging.getLogger(__name__).warning(f"Could not update API versions: {e}")

        # Get the effective API version to use (from argument or customer preference)
        if api_version:
            # Validate provided API version
            available_versions = connection.available_versions_list
            if available_versions and api_version not in available_versions:
                return jsonify({
                    "error": f"API version {api_version} not available. Available versions: {', '.join(available_versions[:5])}",
                    "error_type": "InvalidArgument"
                }), 400
            effective_api_version = api_version
        else:
            effective_api_version = connection.get_effective_api_version()
        
        # Create Salesforce client with the specified API version
        sf_client = get_salesforce_api_client(connection, api_version=effective_api_version)
        
        # Run health checks with optional filtering
        checker = RevenueCloudHealthChecker(sf_client)
        
        if check_types:
            # Run specific checks only
            results = []
            for check_type in check_types:
                if check_type == 'basic_org_info':
                    checker.run_basic_org_info_check()
                elif check_type == 'sharing_model':
                    checker.run_sharing_model_check()
                elif check_type == 'bundle_analysis':
                    checker.run_optimized_bundle_checks()
                elif check_type == 'attribute_integrity':
                    checker.run_attribute_picklist_integrity_check()
            results = checker.results
        else:
            # Run all checks (default behavior)
            results = checker.run_all_checks()

        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": f"✅ Revenue Cloud Health Check Completed\n\nExecuted {len(results)} health checks on Salesforce org {connection.salesforce_org_id} using API version {effective_api_version}.\n\n" +
                           "\n".join([f"• {result.get('check', 'Unknown')}: {result.get('status', 'unknown').upper()}" + 
                                    (f" - {result.get('message', '')}" if result.get('message') else "") 
                                    for result in results])
                }
            ],
            "isError": False,
            "_meta": {
                "customer_id": g.customer.id,
                "salesforce_org_id": connection.salesforce_org_id,
                "api_version_used": effective_api_version,
                "checks_requested": check_types if check_types else ["all"],
                "total_checks": len(results)
            }
        })
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Health check tool failed: {str(e)}", exc_info=True)
        return jsonify({
            "content": [
                {
                    "type": "text", 
                    "text": f"❌ Health check failed: {str(e)}"
                }
            ],
            "isError": True,
            "_meta": {
                "error_type": type(e).__name__
            }
        })

@mcp_bp.route('/health-check', methods=['POST'])
@require_api_key
def perform_health_check():
    """Legacy health check endpoint - redirects to MCP tool invocation."""
    try:
        # For backwards compatibility, convert to MCP tool call format
        data = request.get_json() or {}
        
        tool_call = {
            "name": "revenue_cloud_health_check",
            "arguments": {
                "check_types": data.get('check_types', []),
                "api_version": data.get('api_version')
            }
        }
        
        # Remove empty arguments
        tool_call["arguments"] = {k: v for k, v in tool_call["arguments"].items() if v}
        
        result = handle_health_check_tool(tool_call["arguments"])
        
        # Convert MCP response back to legacy format for compatibility
        if result[1] == 200:  # Success response
            mcp_response = result[0].get_json()
            if not mcp_response.get("isError", False):
                return jsonify({
                    "success": True,
                    "customer_id": mcp_response["_meta"]["customer_id"],
                    "salesforce_org_id": mcp_response["_meta"]["salesforce_org_id"],
                    "api_version_used": mcp_response["_meta"]["api_version_used"],
                    "health_check_results": [
                        {"message": content["text"]} 
                        for content in mcp_response.get("content", [])
                        if content["type"] == "text"
                    ]
                })
        
        # Handle error case
        return jsonify({
            "success": False,
            "error": "Health check failed"
        }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Health check failed: {str(e)}"
        }), 500

@mcp_bp.route('/tools', methods=['GET'])
def get_available_tools():
    """Return MCP-compliant tool definitions."""
    tools = [
        {
            "name": "revenue_cloud_health_check",
            "description": "Perform a comprehensive health check on Salesforce Revenue Cloud configuration. Analyzes org settings, sharing models, bundle configurations, and data integrity.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "check_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["basic_org_info", "sharing_model", "bundle_analysis", "attribute_integrity"]
                        },
                        "description": "Specific types of checks to perform. Options: basic_org_info (organization details), sharing_model (OWD settings), bundle_analysis (product bundle config), attribute_integrity (picklist validation). If not specified, all checks will be performed."
                    },
                    "api_version": {
                        "type": "string",
                        "pattern": "^v\\d+\\.0$",
                        "description": "Salesforce API version to use (e.g., 'v64.0'). If not specified, uses the customer's preferred version or the latest available."
                    }
                },
                "additionalProperties": false
            }
        }
    ]
    
    return jsonify({
        "tools": tools,
        "capabilities": {
            "tools": {
                "listChanged": False
            }
        }
    })

@mcp_bp.route('/status', methods=['GET'])
@require_api_key
def get_service_status():
    """Get the current status of the service for this customer."""
    try:
        connection = g.customer.salesforce_connection
        
        return jsonify({
            "service_status": "operational",
            "customer_id": g.customer.id,
            "salesforce_connected": connection is not None,
            "salesforce_org_id": connection.salesforce_org_id if connection else None,
            "instance_url": connection.instance_url if connection else None,
            "preferred_api_version": connection.preferred_api_version if connection else None,
            "effective_api_version": connection.get_effective_api_version() if connection else None,
            "available_api_versions": connection.available_versions_list if connection else []
        })
    
    except Exception as e:
        return jsonify({
            "service_status": "error",
            "error": str(e)
        }), 500