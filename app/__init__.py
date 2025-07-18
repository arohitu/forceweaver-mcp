from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    # Setup logging
    from app.core.logging_config import setup_logging
    setup_logging(app)

    # Register error handlers
    from app.core.errors import register_error_handlers
    register_error_handlers(app)

    # Register blueprints
    from app.api.auth_routes import auth_bp
    from app.api.mcp_routes import mcp_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
    
    # Add a simple health check endpoint
    @app.route('/health')
    def health_check():
        return {"status": "healthy", "service": "forceweaver-mcp"}
    
    # Add a root endpoint
    @app.route('/')
    def index():
        return {
            "service": "ForceWeaver MCP API",
            "version": "1.0.0",
            "description": "Monetized Revenue Cloud Health Checker API for AI agents",
            "endpoints": {
                "auth": "/api/auth/salesforce/initiate?email=<your-email>",
                "health_check": "/api/mcp/health-check",
                "tools": "/api/mcp/tools",
                "status": "/api/mcp/status"
            },
            "documentation": {
                "auth_flow": "1. Navigate to /api/auth/salesforce/initiate?email=<your-email> to start OAuth flow",
                "api_usage": "Use the returned API key as 'Bearer <api_key>' in Authorization header",
                "mcp_compliance": "This API follows MCP (Model Context Protocol) standards"
            }
        }
    
    app.logger.info("ForceWeaver MCP API initialized successfully")
    return app