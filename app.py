"""
ForceWeaver MCP Server - Main Application Entry Point
"""
import os
from app import create_app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    app.run(host="0.0.0.0", port=port, debug=debug) 