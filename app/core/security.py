from functools import wraps
from flask import request, abort, g
from werkzeug.security import check_password_hash
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
import hashlib
import os
import logging

# Import database for APIKey queries
from app import db

logger = logging.getLogger(__name__)

def _get_encryption_key():
    """Generate or retrieve the encryption key for Salesforce tokens."""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Generate a new key if not provided
        key = Fernet.generate_key()
        print(f"Generated new encryption key: {key.decode()}")
        print("Please set this as ENCRYPTION_KEY in your environment variables")
    else:
        key = key.encode()
    return key

def encrypt_token(token):
    """Encrypt a token using Fernet symmetric encryption."""
    if not token:
        return None
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        encrypted_token = f.encrypt(token.encode())
        return base64.b64encode(encrypted_token).decode()
    except Exception as e:
        logger.error(f"Error encrypting token: {e}")
        return None

def decrypt_token(encrypted_token):
    """Decrypt a token using Fernet symmetric encryption."""
    if not encrypted_token:
        return None
    
    try:
        key = _get_encryption_key()
        f = Fernet(key)
        decoded_token = base64.b64decode(encrypted_token.encode())
        decrypted_token = f.decrypt(decoded_token)
        return decrypted_token.decode()
    except Exception as e:
        logger.error(f"Error decrypting token: {e}")
        return None

def hash_api_key(api_key):
    """Hash an API key using SHA-256."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_api_key():
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)

def require_api_key(f):
    """Decorator to require API key authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.warning(f"Invalid authorization header from {request.remote_addr}")
                abort(401, 'Authorization header is missing or invalid.')

            api_key_str = auth_header.split(' ')[1]
            
            # Hash the provided API key
            hashed_key = hash_api_key(api_key_str)
            
            # Import here to avoid circular imports
            from app.models import APIKey
            
            # Find the API key in the database
            api_key = APIKey.query.filter_by(hashed_key=hashed_key).first()
            
            if not api_key:
                logger.warning(f"Invalid API key attempt from {request.remote_addr}")
                abort(401, 'Invalid API key.')
            
            # Attach the customer to the request context
            g.customer = api_key.customer
            g.api_key = api_key
            
            logger.info(f"API key authentication successful for customer {api_key.customer.email}")
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            abort(401, 'Authentication failed.')
    
    return decorated_function