"""
API Key model for user authentication and access control
"""
import uuid
import secrets
import bcrypt
from datetime import datetime
from app import db

class APIKey(db.Model):
    """API Key model for user authentication"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # API key storage
    key_hash = db.Column(db.String(255), nullable=False)  # bcrypt hash of actual key
    key_prefix = db.Column(db.String(20), nullable=False)  # "fk_abc123" for display
    
    # Key metadata
    name = db.Column(db.String(100), nullable=False)  # User-given name
    description = db.Column(db.Text)  # Optional description
    
    # Key status and tracking
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Rate limiting tier (for future use)
    rate_limit_tier = db.Column(db.String(20), default='default', nullable=False)
    
    def __init__(self, user_id, name, description=None):
        self.user_id = user_id
        self.name = name.strip()
        self.description = description.strip() if description else None
        
        # Generate the API key
        self._generate_api_key()
    
    def __repr__(self):
        return f'<APIKey {self.key_prefix}... for {self.user_id}>'
    
    def _generate_api_key(self):
        """Generate a new API key and store its hash"""
        # Generate secure random key
        key_suffix = secrets.token_urlsafe(32)
        full_key = f"fk_{key_suffix}"
        
        # Store prefix for display (first 10 characters)
        self.key_prefix = full_key[:10]
        
        # Hash the full key for storage
        self.key_hash = bcrypt.hashpw(full_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Return the full key for one-time display
        self._generated_key = full_key
    
    def validate_key(self, provided_key):
        """Validate a provided API key against the stored hash"""
        if not self.is_active:
            return False
        
        try:
            return bcrypt.checkpw(provided_key.encode('utf-8'), self.key_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return False
    
    def update_usage(self):
        """Update usage statistics"""
        self.last_used = datetime.utcnow()
        self.usage_count += 1
        db.session.commit()
    
    def deactivate(self):
        """Deactivate this API key"""
        self.is_active = False
        db.session.commit()
    
    def reactivate(self):
        """Reactivate this API key"""
        self.is_active = True
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert API key to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'key_prefix': self.key_prefix,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'usage_count': self.usage_count,
            'rate_limit_tier': self.rate_limit_tier
        }
        
        # Include the full key only when initially created
        if include_sensitive and hasattr(self, '_generated_key'):
            data['api_key'] = self._generated_key
        
        return data
    
    @classmethod
    def create_api_key(cls, user_id, name, description=None):
        """Create a new API key for a user"""
        api_key = cls(user_id=user_id, name=name, description=description)
        db.session.add(api_key)
        db.session.commit()
        return api_key
    
    @classmethod
    def get_by_key(cls, provided_key):
        """Get API key by validating the provided key"""
        if not provided_key or not provided_key.startswith('fk_'):
            return None
        
        # Get the prefix to narrow down search
        key_prefix = provided_key[:10]
        
        # Find potential matches by prefix
        potential_keys = cls.query.filter_by(
            key_prefix=key_prefix,
            is_active=True
        ).all()
        
        # Validate against each potential match
        for api_key in potential_keys:
            if api_key.validate_key(provided_key):
                return api_key
        
        return None
    
    @classmethod
    def get_user_keys(cls, user_id, include_inactive=False):
        """Get all API keys for a user"""
        query = cls.query.filter_by(user_id=user_id)
        
        if not include_inactive:
            query = query.filter_by(is_active=True)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def cleanup_unused_keys(cls, days_unused=90):
        """Cleanup API keys that haven't been used in X days"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_unused)
        
        unused_keys = cls.query.filter(
            cls.last_used < cutoff_date,
            cls.is_active == True
        ).all()
        
        for key in unused_keys:
            key.deactivate()
        
        db.session.commit()
        return len(unused_keys) 