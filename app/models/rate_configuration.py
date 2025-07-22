"""
Rate Configuration model for managing user rate limits
"""
import uuid
from datetime import datetime
from app import db

class RateConfiguration(db.Model):
    """Rate Configuration model for managing rate limits"""
    __tablename__ = 'rate_configurations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Tier identification
    tier_name = db.Column(db.String(50), unique=True, nullable=False)  # 'default', 'premium', 'enterprise'
    display_name = db.Column(db.String(100), nullable=False)  # 'Default Plan', 'Premium Plan'
    description = db.Column(db.Text)
    
    # Rate limiting settings
    calls_per_hour = db.Column(db.Integer, default=100, nullable=False)
    burst_limit = db.Column(db.Integer, default=20, nullable=False)  # Quick burst allowance
    calls_per_day = db.Column(db.Integer)  # Optional daily limit
    calls_per_month = db.Column(db.Integer)  # Optional monthly limit
    
    # Configuration metadata
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_rate_configs')
    
    def __init__(self, tier_name, display_name, calls_per_hour=100, burst_limit=20, 
                 description=None, created_by=None, is_default=False):
        self.tier_name = tier_name.lower().strip()
        self.display_name = display_name.strip()
        self.calls_per_hour = calls_per_hour
        self.burst_limit = burst_limit
        self.description = description
        self.created_by = created_by
        self.is_default = is_default
    
    def __repr__(self):
        return f'<RateConfiguration {self.tier_name}: {self.calls_per_hour}/hour>'
    
    def to_dict(self):
        """Convert rate configuration to dictionary"""
        return {
            'id': self.id,
            'tier_name': self.tier_name,
            'display_name': self.display_name,
            'description': self.description,
            'calls_per_hour': self.calls_per_hour,
            'burst_limit': self.burst_limit,
            'calls_per_day': self.calls_per_day,
            'calls_per_month': self.calls_per_month,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def update_limits(self, calls_per_hour=None, burst_limit=None, calls_per_day=None, calls_per_month=None):
        """Update rate limits"""
        if calls_per_hour is not None:
            self.calls_per_hour = calls_per_hour
        
        if burst_limit is not None:
            self.burst_limit = burst_limit
        
        if calls_per_day is not None:
            self.calls_per_day = calls_per_day
        
        if calls_per_month is not None:
            self.calls_per_month = calls_per_month
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_tier(cls, tier_name, display_name, calls_per_hour=100, burst_limit=20, 
                    description=None, created_by=None, is_default=False):
        """Create a new rate configuration tier"""
        # If this is being set as default, remove default from other tiers
        if is_default:
            cls.query.update({'is_default': False})
        
        tier = cls(
            tier_name=tier_name,
            display_name=display_name,
            calls_per_hour=calls_per_hour,
            burst_limit=burst_limit,
            description=description,
            created_by=created_by,
            is_default=is_default
        )
        
        db.session.add(tier)
        db.session.commit()
        return tier
    
    @classmethod
    def get_by_tier_name(cls, tier_name):
        """Get rate configuration by tier name"""
        return cls.query.filter_by(
            tier_name=tier_name.lower().strip(),
            is_active=True
        ).first()
    
    @classmethod
    def get_default_tier(cls):
        """Get the default rate configuration tier"""
        default_tier = cls.query.filter_by(is_default=True, is_active=True).first()
        
        # If no default tier exists, create one
        if not default_tier:
            default_tier = cls.create_tier(
                tier_name='default',
                display_name='Default Plan',
                description='Default rate limiting for all users',
                calls_per_hour=100,
                burst_limit=20,
                is_default=True
            )
        
        return default_tier
    
    @classmethod
    def get_active_tiers(cls):
        """Get all active rate configuration tiers"""
        return cls.query.filter_by(is_active=True).order_by(cls.calls_per_hour.asc()).all()
    
    @classmethod
    def set_default_tier(cls, tier_name):
        """Set a tier as the default"""
        # Remove default from all tiers
        cls.query.update({'is_default': False})
        
        # Set new default
        tier = cls.get_by_tier_name(tier_name)
        if tier:
            tier.is_default = True
            db.session.commit()
            return tier
        
        return None
    
    @classmethod
    def initialize_default_tiers(cls):
        """Initialize default rate configuration tiers"""
        default_tiers = [
            {
                'tier_name': 'default',
                'display_name': 'Default Plan',
                'description': 'Standard rate limiting for all users',
                'calls_per_hour': 100,
                'burst_limit': 20,
                'is_default': True
            },
            {
                'tier_name': 'premium',
                'display_name': 'Premium Plan',
                'description': 'Higher limits for premium users',
                'calls_per_hour': 500,
                'burst_limit': 50,
                'calls_per_day': 10000,
                'is_default': False
            },
            {
                'tier_name': 'enterprise',
                'display_name': 'Enterprise Plan',
                'description': 'Highest limits for enterprise customers',
                'calls_per_hour': 2000,
                'burst_limit': 200,
                'calls_per_day': 50000,
                'is_default': False
            }
        ]
        
        created_tiers = []
        for tier_data in default_tiers:
            # Check if tier already exists
            existing_tier = cls.get_by_tier_name(tier_data['tier_name'])
            if not existing_tier:
                tier = cls.create_tier(**tier_data)
                created_tiers.append(tier)
        
        return created_tiers 