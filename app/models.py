from . import db
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """Web dashboard user model for human authentication"""
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))  # For email/password auth
    google_id = Column(String(100), unique=True)  # For Google OAuth
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    customer = relationship("Customer", uselist=False, back_populates="user")
    health_check_history = relationship("HealthCheckHistory", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email

class Customer(db.Model):
    """API Customer model for machine-to-machine authentication"""
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True, unique=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="customer")
    api_key = relationship("APIKey", uselist=False, back_populates="customer", cascade="all, delete-orphan")
    salesforce_connection = relationship("SalesforceConnection", uselist=False, back_populates="customer", cascade="all, delete-orphan")
    health_check_history = relationship("HealthCheckHistory", back_populates="customer", cascade="all, delete-orphan")

class APIKey(db.Model):
    """API Key model for machine-to-machine authentication"""
    id = Column(Integer, primary_key=True)
    hashed_key = Column(String(255), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    name = Column(String(100), default="Default API Key")  # User-friendly name
    
    customer = relationship("Customer", back_populates="api_key")

class SalesforceConnection(db.Model):
    """Salesforce OAuth connection for API customers"""
    id = Column(Integer, primary_key=True)
    salesforce_org_id = Column(String(100), unique=True, nullable=False)
    encrypted_refresh_token = Column(String(512), nullable=False)
    instance_url = Column(String(255), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional org information for dashboard
    org_name = Column(String(255))
    org_type = Column(String(50))  # Production, Sandbox, etc.
    is_sandbox = Column(Boolean, default=False)
    
    # API Version Configuration
    preferred_api_version = Column(String(10))  # e.g., "v59.0", defaults to latest if null
    available_api_versions = Column(Text)  # JSON array of available versions
    api_versions_last_updated = Column(DateTime)
    
    customer = relationship("Customer", back_populates="salesforce_connection")
    
    @property
    def available_versions_list(self):
        """Get available API versions as a list."""
        if self.available_api_versions:
            import json
            try:
                version_data = json.loads(self.available_api_versions)
                # Handle both old format (simple list) and new format (with labels)
                if isinstance(version_data, list):
                    return version_data  # Old format compatibility
                elif isinstance(version_data, dict) and 'versions' in version_data:
                    return version_data['versions']  # New format
            except (json.JSONDecodeError, TypeError):
                pass
        return []
    
    @available_versions_list.setter
    def available_versions_list(self, versions):
        """Set available API versions from a list."""
        import json
        self.available_api_versions = json.dumps(versions) if versions else None
        self.api_versions_last_updated = datetime.utcnow()
    
    def get_version_label(self, version):
        """Get the display label for a specific API version."""
        if self.available_api_versions:
            import json
            try:
                version_data = json.loads(self.available_api_versions)
                if isinstance(version_data, dict) and 'labels' in version_data:
                    return version_data['labels'].get(version, f"Version {version[1:]}")
            except (json.JSONDecodeError, TypeError):
                pass
        # Fallback to simple format
        return f"Version {version[1:]}" if version.startswith('v') else version
    
    def get_versions_with_labels(self):
        """Get versions with their labels for form display."""
        versions = self.available_versions_list
        if not versions:
            return []
        
        result = []
        for version in versions:
            label = self.get_version_label(version)
            result.append((version, f"{version} - {label}"))
        return result
    
    def get_effective_api_version(self):
        """Get the API version to use (preferred or latest available)."""
        if self.preferred_api_version:
            return self.preferred_api_version
        
        # If no preference set, use the latest available version
        versions = self.available_versions_list
        if versions:
            return versions[0]  # Assuming versions are sorted newest first
        
        # Fallback to a more recent default version
        return "v61.0"  # Summer '24 - more recent than v52.0

class HealthCheckHistory(db.Model):
    """Historical health check results for dashboard display"""
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'), nullable=False)
    salesforce_org_id = Column(String(100), nullable=False)
    
    # Health check results summary
    overall_health_score = Column(Integer)
    overall_health_grade = Column(String(2))
    checks_performed = Column(Integer)
    checks_passed = Column(Integer)
    checks_failed = Column(Integer)
    checks_warnings = Column(Integer)
    
    # Full results JSON
    full_results = Column(Text)  # JSON string of complete results
    
    # Metadata
    execution_time_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_by = Column(String(50), default='web_dashboard')  # 'web_dashboard', 'api_call', 'scheduled'
    
    # Relationships
    user = relationship("User", back_populates="health_check_history")
    customer = relationship("Customer", back_populates="health_check_history")