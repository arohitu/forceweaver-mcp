import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # Get the database URL and replace 'postgres://' with 'postgresql://'
    # This is a common fix for Heroku deployment issues with SQLAlchemy
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'postgresql://localhost/forceweaver_mcp'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SALESFORCE_CLIENT_ID = os.environ.get('SALESFORCE_CLIENT_ID')
    SALESFORCE_CLIENT_SECRET = os.environ.get('SALESFORCE_CLIENT_SECRET')
    SALESFORCE_REDIRECT_URI = os.environ.get('SALESFORCE_REDIRECT_URI')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    
    # Optional: Redis for caching (if needed)
    REDIS_URL = os.environ.get('REDIS_URL')
    
    # App configuration
    APP_NAME = "ForceWeaver MCP API"
    APP_VERSION = "1.0.0"