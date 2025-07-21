import os
from cryptography.fernet import Fernet

class LocalConfig:
    SECRET_KEY = 'local-dev-secret-key-for-testing'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///forceweaver_local.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Environment detection
    ENVIRONMENT = 'development'
    IS_STAGING = True
    
    # Environment-specific domain configuration
    @classmethod
    def get_api_domain(cls):
        return 'staging-api.forceweaver.com'
    
    @classmethod
    def get_dashboard_domain(cls):
        return 'staging-healthcheck.forceweaver.com'
    
    @classmethod
    def get_environment_name(cls):
        return 'staging'
    
    # Dynamic Salesforce OAuth Configuration
    @classmethod
    def get_salesforce_redirect_uri(cls):
        base_domain = cls.get_api_domain()
        return f'https://{base_domain}/api/auth/salesforce/callback'
    
    # Static OAuth Configuration (dummy for local testing)
    SALESFORCE_CLIENT_ID = 'dummy_client_id'
    SALESFORCE_CLIENT_SECRET = 'dummy_client_secret'
    SALESFORCE_REDIRECT_URI = 'https://staging-api.forceweaver.com/api/auth/salesforce/callback'
    
    # Google OAuth Configuration (dummy for local testing)
    GOOGLE_CLIENT_ID = 'dummy_google_client_id'
    GOOGLE_CLIENT_SECRET = 'dummy_google_client_secret'
    
    # Dynamic Google OAuth redirect URI
    @classmethod
    def get_google_redirect_uri(cls):
        base_domain = cls.get_dashboard_domain()
        return f'https://{base_domain}/auth/google/callback'
    
    # Encryption (generate a valid key for testing)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    
    # Optional: Redis for caching (not needed for local testing)
    REDIS_URL = None
    
    # App configuration
    @classmethod
    def get_app_name(cls):
        return "ForceWeaver MCP API (Staging)"
    
    APP_NAME = "ForceWeaver MCP API"
    APP_VERSION = "1.0.0"
    
    # Web application configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours 