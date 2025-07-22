"""
Salesforce Organization model for OAuth web server flow
"""
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
from app import db
import os

class SalesforceOrg(db.Model):
    """Salesforce Organization model for OAuth web server flow"""
    __tablename__ = 'salesforce_orgs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Org identification
    org_identifier = db.Column(db.String(100), nullable=False)  # User's friendly name like "prod", "sandbox"
    org_name = db.Column(db.String(255))  # From Salesforce API
    instance_url = db.Column(db.String(255))  # Will be populated after OAuth
    salesforce_org_id = db.Column(db.String(18))  # Salesforce org ID from OAuth response
    
    # OAuth tokens (encrypted)
    access_token_encrypted = db.Column(db.Text)
    refresh_token_encrypted = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    
    # Org type and status
    is_sandbox = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    oauth_completed = db.Column(db.Boolean, default=False, nullable=False)  # Track if OAuth flow is complete
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_auth = db.Column(db.DateTime)
    last_error = db.Column(db.Text)  # Last authentication error
    
    # Usage tracking
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Unique constraint on user_id + org_identifier
    __table_args__ = (
        db.UniqueConstraint('user_id', 'org_identifier', name='unique_user_org_identifier'),
    )
    
    def __init__(self, user_id, org_identifier, is_sandbox=False):
        """Initialize a new Salesforce org for OAuth flow"""
        self.user_id = user_id
        self.org_identifier = org_identifier.lower().strip()
        self.is_sandbox = is_sandbox
        self.oauth_completed = False
    
    def _get_fernet(self):
        """Get Fernet encryption instance"""
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        return Fernet(key.encode())
    
    def set_oauth_tokens(self, access_token, refresh_token, instance_url, org_id=None, org_name=None):
        """Set OAuth tokens and org info after successful authentication"""
        fernet = self._get_fernet()
        
        # Encrypt and store tokens
        self.access_token_encrypted = fernet.encrypt(access_token.encode()).decode()
        self.refresh_token_encrypted = fernet.encrypt(refresh_token.encode()).decode()
        
        # Update org information
        self.instance_url = instance_url
        if org_id:
            self.salesforce_org_id = org_id
        if org_name:
            self.org_name = org_name
            
        self.oauth_completed = True
        self.last_auth = datetime.utcnow()
        self.last_error = None
        
        db.session.commit()
    
    def get_access_token(self):
        """Get decrypted access token"""
        if not self.access_token_encrypted:
            return None
        fernet = self._get_fernet()
        return fernet.decrypt(self.access_token_encrypted.encode()).decode()
    
    def get_refresh_token(self):
        """Get decrypted refresh token"""
        if not self.refresh_token_encrypted:
            return None
        fernet = self._get_fernet()
        return fernet.decrypt(self.refresh_token_encrypted.encode()).decode()
    
    def update_tokens(self, access_token, refresh_token=None):
        """Update tokens after refresh"""
        fernet = self._get_fernet()
        self.access_token_encrypted = fernet.encrypt(access_token.encode()).decode()
        
        if refresh_token:
            self.refresh_token_encrypted = fernet.encrypt(refresh_token.encode()).decode()
            
        self.last_auth = datetime.utcnow()
        db.session.commit()
    
    def clear_error(self):
        """Clear any authentication errors"""
        self.last_error = None
        db.session.commit()
    
    def set_error(self, error_message):
        """Set an authentication error"""
        self.last_error = error_message
        db.session.commit()
    
    def deactivate(self):
        """Deactivate this org connection"""
        self.is_active = False
        db.session.commit()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'org_identifier': self.org_identifier,
            'org_name': self.org_name,
            'instance_url': self.instance_url,
            'salesforce_org_id': self.salesforce_org_id,
            'is_sandbox': self.is_sandbox,
            'is_active': self.is_active,
            'oauth_completed': self.oauth_completed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_auth': self.last_auth.isoformat() if self.last_auth else None,
            'usage_count': self.usage_count,
            'has_tokens': bool(self.access_token_encrypted)
        }
    
    @classmethod
    def create_for_oauth(cls, user_id, org_identifier, is_sandbox=False):
        """Create a new org entry for OAuth flow"""
        # Check if org_identifier already exists for this user
        existing = cls.query.filter_by(
            user_id=user_id, 
            org_identifier=org_identifier.lower().strip()
        ).first()
        
        if existing:
            raise ValueError(f"Org identifier '{org_identifier}' already exists for this user")
        
        org = cls(
            user_id=user_id,
            org_identifier=org_identifier,
            is_sandbox=is_sandbox
        )
        
        db.session.add(org)
        db.session.commit()
        return org
    
    @classmethod
    def get_user_orgs(cls, user_id, active_only=True):
        """Get all orgs for a user"""
        query = cls.query.filter_by(user_id=user_id)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_by_id_and_user(cls, org_id, user_id):
        """Get org by ID and user ID"""
        return cls.query.filter_by(id=org_id, user_id=user_id).first()
    
    @classmethod
    def get_by_identifier_and_user(cls, org_identifier, user_id):
        """Get org by identifier and user ID"""
        return cls.query.filter_by(
            org_identifier=org_identifier.lower().strip(),
            user_id=user_id
        ).first()
    
    def __repr__(self):
        return f'<SalesforceOrg {self.org_identifier} ({self.user_id})>' 