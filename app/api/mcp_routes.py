from flask import Blueprint, request, jsonify, g
from app.core.security import require_api_key
from app.services.salesforce_service import get_salesforce_api_client, update_connection_api_versions
from app.services.health_checker_service import RevenueCloudHealthChecker

mcp_bp = Blueprint('mcp', __name__)

@mcp_bp.route('/health-check', methods=['POST'])
@require_api_key
def perform_health_check():
    """Perform a comprehensive health check on the customer's Salesforce Revenue Cloud setup."""
    try:
        # g.customer is attached by the decorator
        connection = g.customer.salesforce_connection
        if not connection:
            return jsonify({"error": "No Salesforce connection found for this customer."}), 400

        # Ensure we have API versions available (fetch if needed)
        try:
            update_connection_api_versions(connection)
        except Exception as e:
            # Log but don't fail - we can still proceed with default version
            import logging
            logging.getLogger(__name__).warning(f"Could not update API versions: {e}")

        # Get the effective API version to use
        api_version = connection.get_effective_api_version()
        
        # Create Salesforce client with the preferred API version
        sf_client = get_salesforce_api_client(connection, api_version=api_version)
        
        # Run health checks
        checker = RevenueCloudHealthChecker(sf_client)
        results = checker.run_all_checks()

        return jsonify({
            "success": True,
            "customer_id": g.customer.id,
            "salesforce_org_id": connection.salesforce_org_id,
            "api_version_used": api_version,
            "health_check_results": results
        })
    
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
            "description": "Perform a comprehensive health check on Salesforce Revenue Cloud configuration",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "check_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific types of checks to perform (optional, defaults to all)"
                    },
                    "api_version": {
                        "type": "string",
                        "description": "Salesforce API version to use (optional, defaults to customer's preferred version)"
                    }
                }
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