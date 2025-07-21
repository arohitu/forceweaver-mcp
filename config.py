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
        base_domain = cls.get_api_domain()
        return f'https://{base_domain}/api/auth/salesforce/callback'
    
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
        base_domain = cls.get_dashboard_domain()
        return f'https://{base_domain}/auth/google/callback'
    
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