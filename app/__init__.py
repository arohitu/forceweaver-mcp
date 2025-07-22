"""
ForceWeaver MCP Server - Flask Application Factory
"""
import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    """Application factory"""
    # Get the parent directory of the app package (project root)
    import os
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    
    app = Flask(__name__, template_folder=template_dir)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    database_url = os.getenv('DATABASE_URL', 'sqlite:///instance/forceweaver.db')
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'production')
    
    # **Enhanced Flask session configuration for HTTPS**
    # Temporarily disable HTTPS-only cookies for debugging
    app.config['SESSION_COOKIE_SECURE'] = False  # Allow over HTTP for debugging
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent XSS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # Database configuration
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Rate limiting configuration
    app.config['RATELIMIT_STORAGE_URL'] = os.environ.get('REDIS_URL', 'memory://')
    app.config['RATELIMIT_DEFAULT'] = "1000 per hour"
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = '/api/auth/login'  # Updated to match the new route structure
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Import models to ensure they're registered with SQLAlchemy
    from app.models import user, api_key, salesforce_org, usage_log, rate_configuration
    
    # Register blueprints
    from app.web.main_routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.web.auth_routes import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    from app.web.dashboard_routes import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    # API routes (JSON responses) - if they exist
    try:
        from app.api.v1 import auth_api, keys_api, orgs_api, usage_api, internal_api
        app.register_blueprint(auth_api.bp, url_prefix='/api/v1.0/auth')
        app.register_blueprint(keys_api.bp, url_prefix='/api/v1.0/keys')
        app.register_blueprint(orgs_api.bp, url_prefix='/api/v1.0/orgs')
        app.register_blueprint(usage_api.bp, url_prefix='/api/v1.0/usage')
        app.register_blueprint(internal_api.bp, url_prefix='/api/v1.0/internal')
    except ImportError:
        # API modules not yet implemented
        current_app.logger.info("API modules not found, skipping API blueprint registration")
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        current_app.logger.info(f"load_user called with user_id: {user_id} (type: {type(user_id)})")
        try:
            user = db.session.get(User, user_id)  # Updated to use modern SQLAlchemy syntax
            current_app.logger.info(f"load_user result: {user.email if user else 'None'}")
            return user
        except Exception as e:
            current_app.logger.error(f"load_user error: {e}")
            return None
    
    # Logging configuration
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)
        app.logger.info('ForceWeaver MCP Server startup')
    
    # Error handlers
    @app.errorhandler(429)
    def rate_limit_handler(e):
        return {'error': 'Rate limit exceeded', 'message': str(e)}, 429
    
    @app.errorhandler(404)
    def not_found_handler(e):
        return {'error': 'Not found', 'message': 'The requested resource was not found'}, 404
    
    @app.errorhandler(500)
    def internal_error_handler(e):
        return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500
    
    return app 