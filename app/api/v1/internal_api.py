"""
Internal API endpoints for MCP server integration
These endpoints are used by the MCP server for validation and authentication
"""
from flask import Blueprint, request, jsonify, current_app
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app import limiter
import time

bp = Blueprint('internal_api', __name__)

@bp.route('/validate', methods=['POST'])
@limiter.limit("1000 per hour")  # High limit for internal API
def validate_api_key():
    """
    Validate API key and return Salesforce org credentials
    Used by MCP server for authentication
    """
    start_time = time.time()
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'JSON payload required'
            }), 400
        
        api_key_value = data.get('api_key')
        org_identifier = data.get('org_id')
        
        if not api_key_value:
            return jsonify({
                'error': 'Missing API key',
                'message': 'api_key is required'
            }), 400
        
        if not org_identifier:
            return jsonify({
                'error': 'Missing org identifier',
                'message': 'org_id is required'
            }), 400
        
        # Validate API key
        api_key = APIKey.get_by_key(api_key_value)
        if not api_key:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'API key not found or inactive'
            }), 401
        
        # Update API key usage
        api_key.update_usage()
        
        # Get Salesforce org
        salesforce_org = SalesforceOrg.get_user_org(api_key.user_id, org_identifier)
        if not salesforce_org:
            return jsonify({
                'error': 'Salesforce org not found',
                'message': f'No active Salesforce org found with identifier "{org_identifier}"'
            }), 404
        
        # Update org usage
        salesforce_org.update_usage()
        
        # Prepare response with decrypted credentials
        response_data = {
            'valid': True,
            'user_id': api_key.user_id,
            'api_key_id': api_key.id,
            'org_id': salesforce_org.id,
            'org_identifier': salesforce_org.org_identifier,
            'salesforce_credentials': {
                'instance_url': salesforce_org.instance_url,
                'client_id': salesforce_org.client_id,
                'client_secret': salesforce_org.get_client_secret(),
                'org_name': salesforce_org.org_name,
                'salesforce_org_id': salesforce_org.salesforce_org_id,
                'is_sandbox': salesforce_org.is_sandbox
            }
        }
        
        # Include cached tokens if available
        if salesforce_org.is_token_valid():
            response_data['salesforce_credentials'].update({
                'access_token': salesforce_org.get_access_token(),
                'refresh_token': salesforce_org.get_refresh_token(),
                'token_expires_at': salesforce_org.token_expires_at.isoformat()
            })
        
        execution_time = int((time.time() - start_time) * 1000)
        response_data['execution_time_ms'] = execution_time
        
        return jsonify(response_data), 200
    
    except Exception as e:
        current_app.logger.error(f"Internal API validation error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during validation'
        }), 500

@bp.route('/usage', methods=['POST'])
@limiter.limit("2000 per hour")  # High limit for usage logging
def log_usage():
    """
    Log API usage from MCP server
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'JSON payload required'
            }), 400
        
        # Required fields
        required_fields = ['user_id', 'api_key_id', 'tool_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'error': f'Missing {field}',
                    'message': f'{field} is required'
                }), 400
        
        # Optional fields
        usage_data = {
            'user_id': data['user_id'],
            'api_key_id': data['api_key_id'],
            'tool_name': data['tool_name'],
            'success': data.get('success', True),
            'execution_time_ms': data.get('execution_time_ms'),
            'error_message': data.get('error_message'),
            'cost_cents': data.get('cost_cents', 1),  # Default 1 cent
            'salesforce_org_id': data.get('salesforce_org_id'),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr
        }
        
        # Create usage log
        usage_log = UsageLog.log_usage(**usage_data)
        
        return jsonify({
            'success': True,
            'usage_log_id': usage_log.id,
            'message': 'Usage logged successfully'
        }), 201
    
    except Exception as e:
        current_app.logger.error(f"Usage logging error: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred during usage logging'
        }), 500

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for MCP server"""
    try:
        # Basic health check - verify database connection
        from app import db
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'service': 'ForceWeaver Internal API',
            'version': '1.0.0',
            'timestamp': time.time()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500 