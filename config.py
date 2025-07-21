import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Environment detection
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')
    IS_STAGING = os.environ.get('IS_STAGING', 'false').lower() == 'true'
    
    # Get the database URL and replace 'postgres://' with 'postgresql://'
    # This is a common fix for Heroku deployment issues with SQLAlchemy
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://localhost/forceweaver_mcp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Environment-specific domain configuration
    @classmethod
    def get_api_domain(cls):
        if cls.IS_STAGING:
            return 'staging-api.forceweaver.com'
        return 'api.forceweaver.com'
    
    @classmethod
    def get_dashboard_domain(cls):
        if cls.IS_STAGING:
            return 'staging-healthcheck.forceweaver.com'
        return 'healthcheck.forceweaver.com'
    
    @classmethod
    def get_environment_name(cls):
        if cls.IS_STAGING:
            return 'staging'
        return 'production'

    # External URL helper methods for redirects
    @classmethod
    def get_dashboard_url(cls, path=''):
        """Get the full dashboard URL with optional path"""
        dashboard_domain = cls.get_dashboard_domain()
        if path and not path.startswith('/'):
            path = '/' + path
        return f'https://{dashboard_domain}{path}'

    @classmethod
    def get_api_url(cls, path=''):
        """Get the full API URL with optional path"""
        api_domain = cls.get_api_domain()
        if path and not path.startswith('/'):
            path = '/' + path
        return f'https://{api_domain}{path}'
    
    # Dynamic Salesforce OAuth Configuration
    @classmethod
    def get_salesforce_redirect_uri(cls):
        # First try to get from environment variable (set dynamically)
        env_redirect_uri = os.environ.get('SALESFORCE_REDIRECT_URI')
        
        # DEBUG: Log what we're getting
        import sys
        print(f"DEBUG: IS_STAGING = {cls.IS_STAGING}", file=sys.stderr)
        print(f"DEBUG: SALESFORCE_REDIRECT_URI env var = {env_redirect_uri}", file=sys.stderr)
        
        if env_redirect_uri:
            print(f"DEBUG: Using env var value: {env_redirect_uri}", file=sys.stderr)
            return env_redirect_uri
        
        # Use the correct domain-based URLs
        api_domain = cls.get_api_domain()
        fallback_url = f'https://{api_domain}/api/auth/salesforce/callback'
        
        print(f"DEBUG: Using fallback value: {fallback_url}", file=sys.stderr)
        return fallback_url
    
    # Static OAuth Configuration (fallback)
    SALESFORCE_CLIENT_ID = os.environ.get('SALESFORCE_CLIENT_ID')
    SALESFORCE_CLIENT_SECRET = os.environ.get('SALESFORCE_CLIENT_SECRET')
    SALESFORCE_REDIRECT_URI = os.environ.get('SALESFORCE_REDIRECT_URI')  # Can be overridden by get_salesforce_redirect_uri()
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Dynamic Google OAuth redirect URI
    @classmethod
    def get_google_redirect_uri(cls):
        dashboard_domain = cls.get_dashboard_domain()
        return f'https://{dashboard_domain}/auth/google/callback'
    
    # Encryption
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # Optional: Redis for caching (if needed)
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # App configuration
    @classmethod
    def get_app_name(cls):
        env_suffix = " (Staging)" if cls.IS_STAGING else ""
        return f"ForceWeaver MCP API{env_suffix}"
    
    APP_NAME = "ForceWeaver MCP API"
    APP_VERSION = "1.0.0"
    
    # Web application configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Session cookie configuration for cross-subdomain support
    @classmethod 
    def get_session_cookie_domain(cls):
        """Get the appropriate session cookie domain for the environment"""
        if cls.IS_STAGING:
            return '.forceweaver.com'  # Allow cookies across staging-* subdomains
        else:
            return '.forceweaver.com'  # Allow cookies across production subdomains
    
    # Session cookie settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True  # Ensure HTTPS only
    SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-subdomain requests