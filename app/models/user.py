"""
User model for authentication and user management
"""
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model with authentication support"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128))
    
    # User status and metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    salesforce_orgs = db.relationship('SalesforceOrg', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic')
    
    def __init__(self, email, name, password=None):
        self.email = email.lower().strip()
        self.name = name.strip()
        if password:
            self.set_password(password)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def get_active_api_keys(self):
        """Get all active API keys for this user"""
        return self.api_keys.filter_by(is_active=True).all()
    
    def get_salesforce_orgs(self):
        """Get all Salesforce orgs for this user"""
        return self.salesforce_orgs.filter_by(is_active=True).all()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'api_keys_count': self.api_keys.filter_by(is_active=True).count(),
            'orgs_count': self.salesforce_orgs.filter_by(is_active=True).count()
        }
        
        return data
    
    @classmethod
    def create_user(cls, email, name, password, is_admin=False):
        """Create a new user"""
        user = cls(email=email, name=name, password=password)
        user.is_admin = is_admin
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def get_by_email(cls, email):
        """Get user by email"""
        return cls.query.filter_by(email=email.lower().strip()).first()
    
    @classmethod
    def get_admin_users(cls):
        """Get all admin users"""
        return cls.query.filter_by(is_admin=True, is_active=True).all() 