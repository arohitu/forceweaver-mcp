"""
ForceWeaver MCP Server - Main Application Entry Point
"""
import os
import sys

# Add the project root to Python path for proper imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create the Flask application instance for Gunicorn
application = create_app()
app = application  # For compatibility with Gunicorn

if __name__ == "__main__":
    # Development server
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    app.run(host="0.0.0.0", port=port, debug=debug) 