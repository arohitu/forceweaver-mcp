from flask import Blueprint, request, jsonify, g
from app.core.security import require_api_key
from app.services.salesforce_service import get_salesforce_api_client, update_connection_api_versions
from app.services.health_checker_service import RevenueCloudHealthChecker
import logging

mcp_bp = Blueprint('mcp', __name__)

# Debug endpoints removed for security reasons in production

# Debug endpoint removed for production security

@mcp_bp.route('/health-check', methods=['POST'])
@require_api_key
def perform_health_check():
    """MCP-compliant health check endpoint for AI agents."""
    try:
        # Parse the MCP tool call request
        data = request.get_json()
        if not data:
            return jsonify({
                "content": [{"type": "text", "text": "❌ Request body must be valid JSON"}],
                "isError": True,
                "error_type": "InvalidRequest"
            }), 400
        
        # Handle both MCP format and legacy format for flexibility
        if 'name' in data:
            # MCP format: {"name": "revenue_cloud_health_check", "arguments": {...}}
            tool_name = data.get('name')
            arguments = data.get('arguments', {})
            
            if tool_name != 'revenue_cloud_health_check':
                return jsonify({
                    "content": [{"type": "text", "text": f"❌ Unknown tool: {tool_name}. Only 'revenue_cloud_health_check' is supported."}],
                    "isError": True,
                    "error_type": "ToolNotFound"
                }), 404
        else:
            # Legacy/Direct format: {"check_types": [...], "api_version": "..."}
            arguments = data
        
        # g.customer is attached by the decorator
        connection = g.customer.salesforce_connection
        if not connection:
            return jsonify({
                "content": [{"type": "text", "text": "❌ No Salesforce connection found for this customer."}],
                "isError": True,
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
                    "content": [{"type": "text", "text": f"❌ Invalid check types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_check_types)}"}],
                    "isError": True,
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
                    "content": [{"type": "text", "text": f"❌ API version {api_version} not available. Available versions: {', '.join(available_versions[:5])}"}],
                    "isError": True,
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
            for check_type in check_types:
                if check_type == 'basic_org_info':
                    checker.run_basic_org_info_check()
                elif check_type == 'sharing_model':
                    checker.run_sharing_model_check()
                elif check_type == 'bundle_analysis':
                    checker.run_optimized_bundle_checks()
                elif check_type == 'attribute_integrity':
                    checker.run_attribute_picklist_integrity_check()
            
            # Get the results summary after running specific checks
            results = checker._calculate_health_score()
        else:
            # Run all checks (default behavior)
            results = checker.run_all_checks()

        # Format the response for MCP compliance
        # results is a dictionary with 'checks' and 'overall_health' keys
        checks_data = results.get('checks', {})
        overall_health = results.get('overall_health', {})
        
        # Build status summary text
        status_lines = []
        status_lines.append(f"✅ Revenue Cloud Health Check Completed")
        status_lines.append(f"")
        status_lines.append(f"📊 Overall Health Score: {overall_health.get('score', 0)}% (Grade: {overall_health.get('grade', 'F')})")
        status_lines.append(f"")
        
        summary = overall_health.get('summary', {})
        status_lines.append(f"📋 Summary:")
        status_lines.append(f"   • Total Checks: {summary.get('total_checks', 0)}")
        status_lines.append(f"   • Passed: {summary.get('ok', 0)}")
        status_lines.append(f"   • Warnings: {summary.get('warnings', 0)}")
        status_lines.append(f"   • Errors: {summary.get('errors', 0)}")
        status_lines.append(f"")
        
        # Add individual check results
        status_lines.append("🔍 Individual Check Results:")
        for check_name, check_data in checks_data.items():
            status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(check_data.get('status'), "❓")
            check_title = check_name.replace('_', ' ').title()
            status_lines.append(f"   {status_icon} {check_title}: {check_data.get('status', 'unknown').upper()}")
            if check_data.get('message'):
                status_lines.append(f"      └─ {check_data['message']}")

        # Return MCP-compliant response
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(status_lines)
                }
            ],
            "isError": False,
            "_meta": {
                "customer_id": g.customer.id,
                "salesforce_org_id": connection.salesforce_org_id,
                "api_version_used": effective_api_version,
                "checks_requested": check_types if check_types else ["all"],
                "total_checks": summary.get('total_checks', 0),
                "health_score": overall_health.get('score', 0),
                "health_grade": overall_health.get('grade', 'F')
            }
        })
    
    except Exception as e:
        logging.getLogger(__name__).error(f"Health check failed: {str(e)}", exc_info=True)
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

@mcp_bp.route('/tools', methods=['GET'])
def get_available_tools():
    """Return MCP-compliant tool definitions."""
    try:
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
        
        response_data = {
            "tools": tools,
            "capabilities": {
                "tools": {
                    "listChanged": false
                }
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Tools endpoint error: {str(e)}", exc_info=True)
        return jsonify({
            "error": {
                "message": f"Tools endpoint failed: {str(e)}",
                "status_code": 500,
                "type": "ToolsEndpointError"
            }
        }), 500

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