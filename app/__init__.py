"""
ForceWeaver MCP Server - Flask Application Factory
"""
import os
import logging
from flask import Flask, request, current_app, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)

# Simple authentication helpers
def login_user(user):
    """Simple session-based login"""
    session['user_id'] = str(user.id)
    session['user_email'] = user.email
    session['authenticated'] = True
    session.permanent = True

def logout_user():
    """Clear user session"""
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('authenticated', None)

def get_current_user():
    """Get current authenticated user or None"""
    if not session.get('authenticated'):
        return None

    from app.models.user import User
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    """Decorator for routes that require authentication"""
    from functools import wraps
    from flask import redirect, url_for, request

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

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

    # **Standard Flask Session Configuration**
    # Use Flask's default session with proper cookie settings
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
    limiter.init_app(app)

    # Import models to ensure they're registered with SQLAlchemy
    from app.models import user, api_key, salesforce_org, usage_log, rate_configuration

    # Template context processor to provide current_user to all templates
    @app.context_processor
    def inject_user():
        return dict(current_user=get_current_user())

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