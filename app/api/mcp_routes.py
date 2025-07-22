from flask import Blueprint, request, jsonify, g
from app.core.security import require_api_key
from app.services.salesforce_service import get_salesforce_api_client, update_connection_api_versions
from app.services.health_checker_service import RevenueCloudHealthChecker

mcp_bp = Blueprint('mcp', __name__)

@mcp_bp.route('/test-api-versions', methods=['POST'])
@require_api_key
def test_api_versions():
    """Test which API versions are available for this org."""
    try:
        connection = g.customer.salesforce_connection
        if not connection:
            return jsonify({"error": "No Salesforce connection found for this customer."}), 400

        from app.core.security import decrypt_token
        from config import Config
        import requests
        
        # Get fresh access token
        decrypted_refresh_token = decrypt_token(connection.encrypted_refresh_token)
        
        if connection.is_sandbox:
            token_url = "https://test.salesforce.com/services/oauth2/token"
        else:
            token_url = "https://login.salesforce.com/services/oauth2/token"
        
        refresh_data = {
            'grant_type': 'refresh_token',
            'client_id': Config.SALESFORCE_CLIENT_ID,
            'client_secret': Config.SALESFORCE_CLIENT_SECRET,
            'refresh_token': decrypted_refresh_token
        }
        
        token_response = requests.post(token_url, data=refresh_data)
        token_response.raise_for_status()
        
        token_data = token_response.json()
        access_token = token_data['access_token']
        
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
        
        # Test /services/data endpoint first
        services_url = f"{connection.instance_url}/services/data"
        services_response = requests.get(services_url, headers=headers)
        
        results = {
            "instance_url": connection.instance_url,
            "services_data_endpoint": {
                "url": services_url,
                "status_code": services_response.status_code,
                "success": services_response.status_code == 200
            }
        }
        
        if services_response.status_code == 200:
            available_versions = services_response.json()
            results["available_versions"] = available_versions
            
            # Test specific versions
            test_versions = ["v58.0", "v59.0", "v60.0", "v61.0", "v62.0", "v63.0", "v64.0"]
            version_tests = {}
            
            for version in test_versions:
                version_url = f"{connection.instance_url}/services/data/{version}"
                version_response = requests.get(version_url, headers=headers)
                
                version_tests[version] = {
                    "url": version_url,
                    "status_code": version_response.status_code,
                    "success": version_response.status_code == 200
                }
                
                if version_response.status_code == 200:
                    version_data = version_response.json()
                    version_tests[version]["sobjects_url"] = version_data.get("sobjects")
                    version_tests[version]["query_url"] = version_data.get("query")
                    
            results["version_tests"] = version_tests
        else:
            results["error"] = f"Failed to access /services/data endpoint: {services_response.text}"
            
        return jsonify({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }), 500

@mcp_bp.route('/debug', methods=['POST'])
@require_api_key
def debug_connection():
    """Debug Salesforce connection and basic functionality."""
    try:
        # g.customer is attached by the decorator
        connection = g.customer.salesforce_connection
        if not connection:
            return jsonify({"error": "No Salesforce connection found for this customer."}), 400

        # Ensure we have API versions available
        try:
            update_connection_api_versions(connection)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not update API versions: {e}")

        # Get the effective API version to use
        api_version = connection.get_effective_api_version()
        
        debug_results = {
            "connection_info": {
                "org_id": connection.salesforce_org_id,
                "instance_url": connection.instance_url,
                "is_sandbox": connection.is_sandbox,
                "api_version": api_version,
                "preferred_api_version": connection.preferred_api_version
            },
            "api_tests": {}
        }
        
        # Test multiple API versions to identify compatibility issues
        test_versions = [api_version, "v58.0", "v59.0", "v60.0", "v64.0"]
        
        for test_version in test_versions:
            try:
                # Create Salesforce client with specific API version
                sf_client = get_salesforce_api_client(connection, api_version=test_version)
                
                # Basic client info
                client_info = {
                    "base_url": getattr(sf_client, 'base_url', 'Unknown'),
                    "version": getattr(sf_client, 'version', 'Unknown'),
                    "session_id_length": len(sf_client.session_id) if hasattr(sf_client, 'session_id') and sf_client.session_id else 0
                }
                
                # Test basic queries with this version
                version_tests = {}
                
                # Test 1: Simple User query
                try:
                    user_result = sf_client.query("SELECT Id FROM User LIMIT 1")
                    version_tests['user_query'] = {
                        'status': 'success',
                        'record_count': user_result['totalSize'],
                        'query_url': f"{client_info['base_url']}/query/?q=SELECT+Id+FROM+User+LIMIT+1"
                    }
                except Exception as e:
                    version_tests['user_query'] = {
                        'status': 'error',
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'query_url': f"{client_info['base_url']}/query/?q=SELECT+Id+FROM+User+LIMIT+1" if 'base_url' in client_info else 'Unknown'
                    }
                    
                    # Try to get more error details
                    if hasattr(e, 'response'):
                        version_tests['user_query']['http_status'] = getattr(e.response, 'status_code', 'N/A')
                        version_tests['user_query']['http_response'] = getattr(e.response, 'text', 'N/A')
                
                # Test 2: Organization query
                try:
                    org_result = sf_client.query("SELECT Id, Name FROM Organization LIMIT 1")
                    version_tests['org_query'] = {
                        'status': 'success', 
                        'record_count': org_result['totalSize']
                    }
                except Exception as e:
                    version_tests['org_query'] = {
                        'status': 'error',
                        'error': str(e),
                        'error_type': type(e).__name__
                    }
                
                # Test 3: Direct REST API call to validate endpoints
                try:
                    import requests
                    headers = {'Authorization': f'Bearer {sf_client.session_id}', 'Content-Type': 'application/json'}
                    
                    # Test the /services/data endpoint
                    services_url = f"{connection.instance_url}/services/data"
                    services_response = requests.get(services_url, headers=headers)
                    
                    version_tests['services_data_endpoint'] = {
                        'status': 'success' if services_response.status_code == 200 else 'error',
                        'status_code': services_response.status_code,
                        'url': services_url,
                        'response_sample': services_response.json()[:2] if services_response.status_code == 200 else services_response.text[:200]
                    }
                    
                    # Test the specific version endpoint
                    version_url = f"{connection.instance_url}/services/data/{test_version}"
                    version_response = requests.get(version_url, headers=headers)
                    
                    version_tests['version_endpoint'] = {
                        'status': 'success' if version_response.status_code == 200 else 'error',
                        'status_code': version_response.status_code,
                        'url': version_url,
                        'response_sample': version_response.json() if version_response.status_code == 200 else version_response.text[:200]
                    }
                    
                except Exception as e:
                    version_tests['direct_api_test'] = {
                        'status': 'error',
                        'error': str(e)
                    }
                
                debug_results["api_tests"][test_version] = {
                    "client_info": client_info,
                    "tests": version_tests
                }
                
            except Exception as e:
                debug_results["api_tests"][test_version] = {
                    "client_creation_error": str(e),
                    "error_type": type(e).__name__
                }
        
        # Test token refresh process
        try:
            from app.core.security import decrypt_token
            decrypted_refresh_token = decrypt_token(connection.encrypted_refresh_token)
            
            # Test token refresh manually
            if connection.is_sandbox:
                token_url = "https://test.salesforce.com/services/oauth2/token"
            else:
                token_url = "https://login.salesforce.com/services/oauth2/token"
            
            import requests
            from config import Config
            
            refresh_data = {
                'grant_type': 'refresh_token',
                'client_id': Config.SALESFORCE_CLIENT_ID,
                'client_secret': Config.SALESFORCE_CLIENT_SECRET,
                'refresh_token': decrypted_refresh_token
            }
            
            token_response = requests.post(token_url, data=refresh_data)
            
            debug_results["token_refresh_test"] = {
                "status": "success" if token_response.status_code == 200 else "error",
                "status_code": token_response.status_code,
                "token_url": token_url,
                "response_keys": list(token_response.json().keys()) if token_response.status_code == 200 else None,
                "error_response": token_response.text if token_response.status_code != 200 else None
            }
            
            if token_response.status_code == 200:
                token_data = token_response.json()
                debug_results["token_refresh_test"]["instance_url_match"] = token_data.get('instance_url') == connection.instance_url
                debug_results["token_refresh_test"]["new_instance_url"] = token_data.get('instance_url')
                
        except Exception as e:
            debug_results["token_refresh_test"] = {
                "status": "error",
                "error": str(e)
            }

        return jsonify({
            "success": True,
            "customer_id": g.customer.id,
            "debug_results": debug_results
        })
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Debug connection failed: {str(e)}", exc_info=True)
        
        return jsonify({
            "success": False,
            "error": f"Debug failed: {str(e)}",
            "error_type": type(e).__name__
        }), 500

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