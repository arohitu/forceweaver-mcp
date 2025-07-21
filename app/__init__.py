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
        app.logger.info(f"=== USER LOADER CALLED ===")
        app.logger.info(f"Loading user with ID: {user_id}")
        try:
            user = User.query.get(int(user_id))
            if user:
                app.logger.info(f"User loaded successfully: {user.email} (ID: {user.id})")
            else:
                app.logger.warning(f"No user found with ID: {user_id}")
            return user
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {str(e)}")
            app.logger.exception("User loader error details:")
            return None
    
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
        path = request.path
        method = request.method
        
        app.logger.info(f"=== REQUEST RECEIVED ===")
        app.logger.info(f"Host: {host}")
        app.logger.info(f"Path: {path}")
        app.logger.info(f"Method: {method}")
        app.logger.info(f"User Agent: {request.headers.get('User-Agent', 'Unknown')}")
        
        # Log current user status
        from flask_login import current_user
        if current_user.is_authenticated:
            app.logger.info(f"Request from authenticated user: {current_user.email} (ID: {current_user.id})")
        else:
            app.logger.info("Request from anonymous user")
        
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
        
        app.logger.info(f"Domain routing - Dashboard: {is_dashboard_domain}, API: {is_api_domain}, Localhost: {is_localhost}")
        
        # Route based on domain or path for localhost
        if is_dashboard_domain or (is_localhost and request.path.startswith('/dashboard')):
            app.logger.info("Routing to dashboard/web routes")
            # Web dashboard routes
            pass  # Will be handled by dashboard blueprint
        elif is_api_domain or (is_localhost and request.path.startswith('/api/')):
            app.logger.info("Routing to API routes")
            # API routes
            pass  # Will be handled by API blueprints
        elif is_localhost:
            app.logger.info("Localhost - allowing all routes")
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
        app.logger.info("=== ROOT INDEX ROUTE ===")
        host = request.headers.get('Host', '')
        app.logger.info(f"Root route accessed with host: {host}")
        
        # Dashboard domains (production and staging)
        dashboard_domains = [
            'healthcheck.forceweaver.com',
            'staging-healthcheck.forceweaver.com'
        ]
        
        is_dashboard_domain = any(domain in host for domain in dashboard_domains)
        is_localhost = 'localhost' in host or '127.0.0.1' in host
        
        app.logger.info(f"Domain check - Dashboard domain: {is_dashboard_domain}, Localhost: {is_localhost}")
        
        if is_dashboard_domain or is_localhost:
            app.logger.info("Processing dashboard/web request")
            # Web dashboard home - redirect to login or dashboard
            from flask import redirect, url_for
            from flask_login import current_user
            
            app.logger.info(f"Current user authenticated: {current_user.is_authenticated}")
            
            if current_user.is_authenticated:
                app.logger.info(f"Authenticated user {current_user.email} - redirecting to dashboard")
                dashboard_url = url_for('dashboard.index')
                app.logger.info(f"Dashboard redirect URL: {dashboard_url}")
                return redirect(dashboard_url)
            else:
                app.logger.info("Anonymous user - redirecting to login")
                login_url = url_for('web_auth.login')
                app.logger.info(f"Login redirect URL: {login_url}")
                return redirect(login_url)
        
        # API domain - return API info with environment context
        app.logger.info("Processing API request - returning service info")
        environment_name = Config.get_environment_name()
        app_name = Config.get_app_name()
        app.logger.info(f"API response - Environment: {environment_name}, App: {app_name}")
        
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