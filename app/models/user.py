"""
Simple User model for authentication
"""
import uuid
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from app import db
import bcrypt

class User(db.Model):
    """User model with simple password authentication"""
    __tablename__ = 'users'
    
    # Primary key
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User info
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy='dynamic')
    salesforce_orgs = db.relationship('SalesforceOrg', backref='user', lazy='dynamic')
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic')
    
    def __init__(self, email, name, password=None):
        """Initialize user"""
        self.id = str(uuid.uuid4())
        self.email = email.lower().strip()
        self.name = name.strip()
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Set password hash"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Hash password with bcrypt
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    
    def check_password(self, password):
        """Verify password"""
        if not password or not self.password_hash:
            return False
        
        try:
            password_bytes = password.encode('utf-8')
            hash_bytes = self.password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            print(f"Password check error: {e}")
            return False
    
    @classmethod
    def create_user(cls, email, name, password):
        """Create a new user"""
        if cls.query.filter_by(email=email.lower().strip()).first():
            raise ValueError("User with this email already exists")
        
        user = cls(email=email, name=name, password=password)
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def authenticate(cls, email, password):
        """Authenticate user by email and password"""
        user = cls.query.filter_by(email=email.lower().strip()).first()
        if user and user.is_active and user.check_password(password):
            return user
        return None
    
    def __repr__(self):
        return f'<User {self.email}>' 