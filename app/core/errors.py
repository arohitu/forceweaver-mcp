"""
Error handling for ForceWeaver MCP API
"""

from flask import jsonify, request
import logging
import traceback

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base API error class."""
    status_code = 500
    message = "Internal server error"
    
    def __init__(self, message=None, status_code=None):
        super().__init__()
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code

class ValidationError(APIError):
    """Validation error."""
    status_code = 400
    message = "Validation error"

class AuthenticationError(APIError):
    """Authentication error."""
    status_code = 401
    message = "Authentication required"

class AuthorizationError(APIError):
    """Authorization error."""
    status_code = 403
    message = "Access denied"

class NotFoundError(APIError):
    """Not found error."""
    status_code = 404
    message = "Resource not found"

class SalesforceError(APIError):
    """Salesforce-related error."""
    status_code = 502
    message = "Salesforce service error"

def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors."""
        response = {
            "error": {
                "message": error.message,
                "status_code": error.status_code,
                "type": error.__class__.__name__
            }
        }
        
        if app.debug:
            response["error"]["traceback"] = traceback.format_exc()
        
        logger.error(f"API Error: {error.message}", extra={
            "status_code": error.status_code,
            "path": request.path,
            "method": request.method
        })
        
        return jsonify(response), error.status_code
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors."""
        return jsonify({
            "error": {
                "message": "Bad request",
                "status_code": 400,
                "type": "BadRequest"
            }
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle unauthorized errors."""
        return jsonify({
            "error": {
                "message": "Unauthorized",
                "status_code": 401,
                "type": "Unauthorized"
            }
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle forbidden errors."""
        return jsonify({
            "error": {
                "message": "Forbidden",
                "status_code": 403,
                "type": "Forbidden"
            }
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors."""
        return jsonify({
            "error": {
                "message": "Not found",
                "status_code": 404,
                "type": "NotFound"
            }
        }), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors."""
        response = {
            "error": {
                "message": "Internal server error",
                "status_code": 500,
                "type": "InternalServerError"
            }
        }
        
        if app.debug:
            response["error"]["traceback"] = traceback.format_exc()
        
        logger.error(f"Internal Server Error: {str(error)}", extra={
            "path": request.path,
            "method": request.method
        })
        
        return jsonify(response), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected errors."""
        response = {
            "error": {
                "message": "An unexpected error occurred",
                "status_code": 500,
                "type": "UnexpectedError"
            }
        }
        
        if app.debug:
            response["error"]["traceback"] = traceback.format_exc()
            response["error"]["details"] = str(error)
        
        logger.error(f"Unexpected Error: {str(error)}", extra={
            "path": request.path,
            "method": request.method
        })
        
        return jsonify(response), 500 