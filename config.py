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
    
    # Dynamic Salesforce OAuth Configuration
    @classmethod
    def get_salesforce_redirect_uri(cls):
        # First try to get from environment variable (set dynamically)
        env_redirect_uri = os.environ.get('SALESFORCE_REDIRECT_URI')
        if env_redirect_uri:
            return env_redirect_uri
        
        # Fallback to default URLs if environment variable is not set
        if cls.IS_STAGING:
            # Use Heroku app URL for staging (fallback)
            return 'https://forceweaver-mcp-staging-6b04df6045f5.herokuapp.com/api/auth/salesforce/callback'
        else:
            # Use custom domain for production (fallback)
            return 'https://api.forceweaver.com/api/auth/salesforce/callback'
    
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
        if cls.IS_STAGING:
            # Use Heroku app URL for staging
            return 'https://forceweaver-mcp-staging.herokuapp.com/auth/google/callback'
        else:
            # Use custom domain for production
            return 'https://healthcheck.forceweaver.com/auth/google/callback'
    
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