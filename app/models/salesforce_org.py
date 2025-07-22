"""
Salesforce Organization model for managing user Salesforce connections
"""
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
from app import db
import os

class SalesforceOrg(db.Model):
    """Salesforce Organization model for storing connection details"""
    __tablename__ = 'salesforce_orgs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Org identification
    org_identifier = db.Column(db.String(100), nullable=False)  # User's friendly name like "prod", "sandbox"
    org_name = db.Column(db.String(255))  # From Salesforce API
    instance_url = db.Column(db.String(255), nullable=False)
    salesforce_org_id = db.Column(db.String(18))  # Salesforce org ID
    
    # OAuth credentials (encrypted)
    client_id = db.Column(db.String(255), nullable=False)
    client_secret_encrypted = db.Column(db.Text, nullable=False)
    
    # OAuth tokens (if we cache them)
    access_token_encrypted = db.Column(db.Text)
    refresh_token_encrypted = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Org status and metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_sandbox = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_auth = db.Column(db.DateTime)
    last_error = db.Column(db.Text)  # Last authentication error
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Unique constraint on user_id + org_identifier
    __table_args__ = (
        db.UniqueConstraint('user_id', 'org_identifier', name='unique_user_org_identifier'),
    )
    
    def __init__(self, user_id, org_identifier, instance_url, client_id, client_secret, is_sandbox=False):
        self.user_id = user_id
        self.org_identifier = org_identifier.lower().strip()
        self.instance_url = instance_url.strip()
        self.client_id = client_id.strip()
        self.is_sandbox = is_sandbox
        
        # Encrypt and store client secret
        self._encrypt_client_secret(client_secret)
    
    def __repr__(self):
        return f'<SalesforceOrg {self.org_identifier} for {self.user_id}>'
    
    @property
    def _encryption_key(self):
        """Get encryption key from environment"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Generate a key for development (not for production!)
            key = Fernet.generate_key()
            os.environ['ENCRYPTION_KEY'] = key.decode()
        
        if isinstance(key, str):
            key = key.encode()
        
        return key
    
    def _get_fernet(self):
        """Get Fernet instance for encryption/decryption"""
        return Fernet(self._encryption_key)
    
    def _encrypt_client_secret(self, client_secret):
        """Encrypt and store client secret"""
        if not client_secret:
            raise ValueError("Client secret is required")
        
        fernet = self._get_fernet()
        encrypted_secret = fernet.encrypt(client_secret.encode())
        self.client_secret_encrypted = encrypted_secret.decode()
    
    def get_client_secret(self):
        """Decrypt and return client secret"""
        if not self.client_secret_encrypted:
            return None
        
        try:
            fernet = self._get_fernet()
            decrypted = fernet.decrypt(self.client_secret_encrypted.encode())
            return decrypted.decode()
        except Exception:
            return None
    
    def update_client_secret(self, new_client_secret):
        """Update the client secret"""
        self._encrypt_client_secret(new_client_secret)
        db.session.commit()
    
    def store_tokens(self, access_token, refresh_token=None, expires_in=3600):
        """Store OAuth tokens (encrypted)"""
        fernet = self._get_fernet()
        
        # Encrypt access token
        if access_token:
            self.access_token_encrypted = fernet.encrypt(access_token.encode()).decode()
        
        # Encrypt refresh token if provided
        if refresh_token:
            self.refresh_token_encrypted = fernet.encrypt(refresh_token.encode()).decode()
        
        # Set expiration
        from datetime import timedelta
        self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        self.last_auth = datetime.utcnow()
        self.last_error = None
        
        db.session.commit()
    
    def get_access_token(self):
        """Get decrypted access token"""
        if not self.access_token_encrypted:
            return None
        
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(self.access_token_encrypted.encode()).decode()
        except Exception:
            return None
    
    def get_refresh_token(self):
        """Get decrypted refresh token"""
        if not self.refresh_token_encrypted:
            return None
        
        try:
            fernet = self._get_fernet()
            return fernet.decrypt(self.refresh_token_encrypted.encode()).decode()
        except Exception:
            return None
    
    def is_token_valid(self):
        """Check if stored token is still valid"""
        if not self.access_token_encrypted or not self.token_expires_at:
            return False
        
        return datetime.utcnow() < self.token_expires_at
    
    def update_org_info(self, org_name, salesforce_org_id):
        """Update organization information from Salesforce API"""
        self.org_name = org_name
        self.salesforce_org_id = salesforce_org_id
        db.session.commit()
    
    def record_error(self, error_message):
        """Record an authentication error"""
        self.last_error = error_message
        db.session.commit()
    
    def update_usage(self):
        """Update usage statistics"""
        self.usage_count += 1
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert org to dictionary"""
        data = {
            'id': self.id,
            'org_identifier': self.org_identifier,
            'org_name': self.org_name,
            'instance_url': self.instance_url,
            'salesforce_org_id': self.salesforce_org_id,
            'client_id': self.client_id,
            'is_active': self.is_active,
            'is_sandbox': self.is_sandbox,
            'created_at': self.created_at.isoformat(),
            'last_auth': self.last_auth.isoformat() if self.last_auth else None,
            'usage_count': self.usage_count,
            'has_tokens': bool(self.access_token_encrypted),
            'token_valid': self.is_token_valid() if self.access_token_encrypted else False
        }
        
        if include_sensitive:
            data['client_secret'] = self.get_client_secret()
            data['access_token'] = self.get_access_token()
            data['refresh_token'] = self.get_refresh_token()
        
        if self.last_error:
            data['last_error'] = self.last_error
        
        return data
    
    @classmethod
    def create_org(cls, user_id, org_identifier, instance_url, client_id, client_secret, is_sandbox=False):
        """Create a new Salesforce org"""
        org = cls(
            user_id=user_id,
            org_identifier=org_identifier,
            instance_url=instance_url,
            client_id=client_id,
            client_secret=client_secret,
            is_sandbox=is_sandbox
        )
        db.session.add(org)
        db.session.commit()
        return org
    
    @classmethod
    def get_user_org(cls, user_id, org_identifier):
        """Get specific org for user"""
        return cls.query.filter_by(
            user_id=user_id,
            org_identifier=org_identifier.lower().strip(),
            is_active=True
        ).first()
    
    @classmethod
    def get_user_orgs(cls, user_id, include_inactive=False):
        """Get all orgs for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(cls.created_at.desc()).all() 