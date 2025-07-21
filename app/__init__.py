from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'web_auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Make CSRF token available in all templates
    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    # Setup logging
    from app.core.logging_config import setup_logging
    setup_logging(app)

    # Register error handlers
    from app.core.errors import register_error_handlers
    register_error_handlers(app)

    # Register blueprints based on domain
    @app.before_request
    def route_by_domain():
        # Route requests based on domain/subdomain
        host = request.headers.get('Host', '')
        
        # Dashboard domains (production and staging)
        dashboard_domains = [
            'healthcheck.forceweaver.com',
            'staging-healthcheck.forceweaver.com'
        ]
        
        # API domains (production and staging)  
        api_domains = [
            'api.forceweaver.com',
            'staging-api.forceweaver.com'
        ]
        
        is_dashboard_domain = any(domain in host for domain in dashboard_domains)
        is_api_domain = any(domain in host for domain in api_domains)
        is_localhost = 'localhost' in host or '127.0.0.1' in host
        
        # Route based on domain or path for localhost
        if is_dashboard_domain or (is_localhost and request.path.startswith('/dashboard')):
            # Web dashboard routes
            pass  # Will be handled by dashboard blueprint
        elif is_api_domain or (is_localhost and request.path.startswith('/api/')):
            # API routes
            pass  # Will be handled by API blueprints
        elif is_localhost:
            # Allow all routes on localhost for development
            pass
    
    # API Blueprints (for api.forceweaver.com)
    from app.api.auth_routes import auth_bp
    from app.api.mcp_routes import mcp_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(mcp_bp, url_prefix='/api/mcp')
    
    # Web Dashboard Blueprints (for healthcheck.forceweaver.com)
    from app.web.dashboard_routes import dashboard_bp
    from app.web.auth_routes import web_auth_bp
    
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(web_auth_bp, url_prefix='/auth')
    
    # Root endpoints - serve different content based on domain
    @app.route('/')
    def index():
        host = request.headers.get('Host', '')
        
        # Dashboard domains (production and staging)
        dashboard_domains = [
            'healthcheck.forceweaver.com',
            'staging-healthcheck.forceweaver.com'
        ]
        
        is_dashboard_domain = any(domain in host for domain in dashboard_domains)
        is_localhost = 'localhost' in host or '127.0.0.1' in host
        
        if is_dashboard_domain or is_localhost:
            # Web dashboard home - redirect to login or dashboard
            from flask import redirect, url_for
            from flask_login import current_user
            
            if current_user.is_authenticated:
                return redirect(url_for('dashboard.index'))
            else:
                return redirect(url_for('web_auth.login'))
        
        # API domain - return API info with environment context
        environment_name = Config.get_environment_name()
        app_name = Config.get_app_name()
        
        return {
            "service": app_name,
            "environment": environment_name,
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
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {"status": "healthy", "service": "forceweaver-mcp"}
    
    app.logger.info("ForceWeaver MCP API initialized successfully")
    return app