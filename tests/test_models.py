"""
Unit tests for database models
"""
import pytest
from datetime import datetime, timedelta

from app.models.user import User
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app.models.rate_configuration import RateConfiguration
from app import db


class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user(self, app_context):
        """Test user creation"""
        user = User(
            email='test@example.com',
            name='Test User'
        )
        user.set_password('testpassword')
        
        db.session.add(user)
        db.session.commit()
        
        assert user.id is not None
        assert user.email == 'test@example.com'
        assert user.name == 'Test User'
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_password_hashing(self, app_context):
        """Test password hashing and verification"""
        user = User(email='test@example.com', name='Test User')
        user.set_password('testpassword')
        
        # Password should be hashed, not stored as plain text
        assert user.password_hash != 'testpassword'
        assert user.password_hash is not None
        
        # Should verify correct password
        assert user.check_password('testpassword') is True
        assert user.check_password('wrongpassword') is False
    
    def test_user_relationships(self, test_user):
        """Test user model relationships"""
        # Test API keys relationship
        api_key = APIKey(user_id=test_user.id, name='Test Key')
        db.session.add(api_key)
        db.session.commit()
        
        assert len(test_user.api_keys.all()) == 1
        assert test_user.api_keys.first().name == 'Test Key'
        
        # Test Salesforce orgs relationship
        org = SalesforceOrg(
            user_id=test_user.id,
            org_identifier='test_org',
            instance_url='https://test.my.salesforce.com',
            client_id='test_client_id'
        )
        org._encrypt_client_secret('test_secret')
        db.session.add(org)
        db.session.commit()
        
        assert len(test_user.salesforce_orgs.all()) == 1
        assert test_user.salesforce_orgs.first().org_identifier == 'test_org'
    
    def test_user_unique_email(self, app_context):
        """Test email uniqueness constraint"""
        user1 = User(email='test@example.com', name='User 1')
        user1.set_password('password1')
        db.session.add(user1)
        db.session.commit()
        
        # Try to create another user with same email
        user2 = User(email='test@example.com', name='User 2')
        user2.set_password('password2')
        db.session.add(user2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db.session.commit()


class TestAPIKeyModel:
    """Test APIKey model functionality"""
    
    def test_create_api_key(self, test_user):
        """Test API key creation"""
        api_key = APIKey(
            user_id=test_user.id,
            name='Test API Key',
            description='Test description'
        )
        db.session.add(api_key)
        db.session.commit()
        
        assert api_key.id is not None
        assert api_key.user_id == test_user.id
        assert api_key.name == 'Test API Key'
        assert api_key.description == 'Test description'
        assert api_key.is_active is True
        assert api_key.key_prefix.startswith('fk_')
        assert len(api_key.key_prefix) == 10  # fk_ + 7 chars
        assert api_key.key_hash is not None
        assert api_key.usage_count == 0
        assert api_key.created_at is not None
    
    def test_api_key_generation(self, test_user):
        """Test API key generation and validation"""
        api_key = APIKey(user_id=test_user.id, name='Test Key')
        db.session.add(api_key)
        db.session.commit()
        
        # Generated key should be available immediately after creation
        generated_key = api_key._generated_key
        assert generated_key is not None
        assert generated_key.startswith('fk_')
        
        # Should validate correct key
        assert api_key.validate_key(generated_key) is True
        assert api_key.validate_key('wrong_key') is False
    
    def test_api_key_usage_tracking(self, test_api_key):
        """Test usage tracking functionality"""
        initial_count = test_api_key.usage_count
        initial_last_used = test_api_key.last_used
        
        test_api_key.increment_usage()
        
        assert test_api_key.usage_count == initial_count + 1
        assert test_api_key.last_used != initial_last_used
        assert test_api_key.last_used is not None
    
    def test_api_key_deactivation(self, test_api_key):
        """Test API key deactivation"""
        assert test_api_key.is_active is True
        
        test_api_key.deactivate()
        
        assert test_api_key.is_active is False
        assert test_api_key.deactivated_at is not None


class TestSalesforceOrgModel:
    """Test SalesforceOrg model functionality"""
    
    def test_create_salesforce_org(self, test_user):
        """Test Salesforce org creation"""
        org = SalesforceOrg(
            user_id=test_user.id,
            org_identifier='production',
            instance_url='https://myorg.my.salesforce.com',
            client_id='test_client_id',
            is_sandbox=False
        )
        org._encrypt_client_secret('test_client_secret')
        
        db.session.add(org)
        db.session.commit()
        
        assert org.id is not None
        assert org.user_id == test_user.id
        assert org.org_identifier == 'production'
        assert org.instance_url == 'https://myorg.my.salesforce.com'
        assert org.client_id == 'test_client_id'
        assert org.is_sandbox is False
        assert org.is_active is True
        assert org.client_secret_encrypted is not None
        assert org.created_at is not None
    
    def test_client_secret_encryption(self, test_user):
        """Test client secret encryption and decryption"""
        org = SalesforceOrg(
            user_id=test_user.id,
            org_identifier='test_org',
            instance_url='https://test.my.salesforce.com',
            client_id='test_client_id'
        )
        
        original_secret = 'super_secret_client_secret'
        org._encrypt_client_secret(original_secret)
        
        # Secret should be encrypted, not stored as plain text
        assert org.client_secret_encrypted != original_secret
        assert org.client_secret_encrypted is not None
        
        # Should decrypt to original value
        assert org.get_client_secret() == original_secret
    
    def test_token_encryption(self, test_salesforce_org):
        """Test access and refresh token encryption"""
        access_token = 'test_access_token'
        refresh_token = 'test_refresh_token'
        
        test_salesforce_org._encrypt_access_token(access_token)
        test_salesforce_org._encrypt_refresh_token(refresh_token)
        
        db.session.commit()
        
        # Tokens should be encrypted
        assert test_salesforce_org.access_token_encrypted != access_token
        assert test_salesforce_org.refresh_token_encrypted != refresh_token
        
        # Should decrypt correctly
        assert test_salesforce_org.get_access_token() == access_token
        assert test_salesforce_org.get_refresh_token() == refresh_token
    
    def test_org_unique_identifier_per_user(self, test_user):
        """Test org identifier uniqueness per user"""
        org1 = SalesforceOrg(
            user_id=test_user.id,
            org_identifier='production',
            instance_url='https://org1.my.salesforce.com',
            client_id='client_id_1'
        )
        org1._encrypt_client_secret('secret1')
        db.session.add(org1)
        db.session.commit()
        
        # Same identifier for same user should fail
        org2 = SalesforceOrg(
            user_id=test_user.id,
            org_identifier='production',
            instance_url='https://org2.my.salesforce.com',
            client_id='client_id_2'
        )
        org2._encrypt_client_secret('secret2')
        db.session.add(org2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db.session.commit()


class TestUsageLogModel:
    """Test UsageLog model functionality"""
    
    def test_create_usage_log(self, test_user, test_api_key):
        """Test usage log creation"""
        log = UsageLog(
            user_id=test_user.id,
            api_key_id=test_api_key.id,
            tool_name='revenue_cloud_health_check',
            success=True,
            execution_time_ms=2500,
            cost_cents=5
        )
        db.session.add(log)
        db.session.commit()
        
        assert log.id is not None
        assert log.user_id == test_user.id
        assert log.api_key_id == test_api_key.id
        assert log.tool_name == 'revenue_cloud_health_check'
        assert log.success is True
        assert log.execution_time_ms == 2500
        assert log.cost_cents == 5
        assert log.created_at is not None
    
    def test_usage_log_class_method(self, test_user, test_api_key):
        """Test UsageLog.log_usage class method"""
        log = UsageLog.log_usage(
            user_id=test_user.id,
            api_key_id=test_api_key.id,
            tool_name='test_tool',
            success=True,
            cost_cents=3,
            execution_time_ms=1000,
            error_message=None
        )
        
        assert log is not None
        assert log.user_id == test_user.id
        assert log.api_key_id == test_api_key.id
        assert log.tool_name == 'test_tool'
        assert log.cost_cents == 3
        assert log.execution_time_ms == 1000
    
    def test_failed_usage_log(self, test_user, test_api_key):
        """Test logging failed API calls"""
        log = UsageLog.log_usage(
            user_id=test_user.id,
            api_key_id=test_api_key.id,
            tool_name='test_tool',
            success=False,
            error_message='Test error message',
            cost_cents=0
        )
        
        assert log.success is False
        assert log.error_message == 'Test error message'
        assert log.cost_cents == 0
    
    def test_get_usage_stats(self, test_user, test_api_key):
        """Test usage statistics retrieval"""
        # Create multiple usage logs
        for i in range(5):
            UsageLog.log_usage(
                user_id=test_user.id,
                api_key_id=test_api_key.id,
                tool_name='test_tool',
                success=i < 4,  # 4 successful, 1 failed
                cost_cents=10 if i < 4 else 0
            )
        
        # Test statistics
        stats = UsageLog.get_usage_stats(
            user_id=test_user.id,
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow() + timedelta(days=1)
        )
        
        assert stats['total_calls'] == 5
        assert stats['successful_calls'] == 4
        assert stats['failed_calls'] == 1
        assert stats['success_rate'] == 80.0
        assert stats['total_cost_cents'] == 40


class TestRateConfigurationModel:
    """Test RateConfiguration model functionality"""
    
    def test_create_rate_configuration(self, app_context):
        """Test rate configuration creation"""
        config = RateConfiguration(
            tier_name='custom',
            calls_per_hour=200,
            burst_limit=50,
            is_default=False
        )
        db.session.add(config)
        db.session.commit()
        
        assert config.id is not None
        assert config.tier_name == 'custom'
        assert config.calls_per_hour == 200
        assert config.burst_limit == 50
        assert config.is_default is False
        assert config.created_at is not None
    
    def test_default_rate_configuration(self, app_context):
        """Test default rate configuration"""
        # Should already exist from conftest.py initialization
        default_config = RateConfiguration.get_default_configuration()
        
        assert default_config is not None
        assert default_config.is_default is True
        assert default_config.tier_name == 'default'
    
    def test_get_configuration_by_tier(self, app_context):
        """Test retrieving configuration by tier name"""
        # Create a custom tier
        custom_config = RateConfiguration(
            tier_name='premium',
            calls_per_hour=1000,
            burst_limit=100
        )
        db.session.add(custom_config)
        db.session.commit()
        
        # Test retrieval
        retrieved_config = RateConfiguration.get_by_tier('premium')
        assert retrieved_config is not None
        assert retrieved_config.tier_name == 'premium'
        assert retrieved_config.calls_per_hour == 1000
    
    def test_unique_tier_names(self, app_context):
        """Test tier name uniqueness"""
        config1 = RateConfiguration(tier_name='unique_tier', calls_per_hour=100)
        db.session.add(config1)
        db.session.commit()
        
        # Try to create another with same tier name
        config2 = RateConfiguration(tier_name='unique_tier', calls_per_hour=200)
        db.session.add(config2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            db.session.commit()
    
    def test_initialize_default_tiers(self, app_context):
        """Test default tier initialization"""
        # Clear existing configurations
        RateConfiguration.query.delete()
        db.session.commit()
        
        # Initialize default tiers
        RateConfiguration.initialize_default_tiers()
        
        # Verify tiers were created
        default_tier = RateConfiguration.query.filter_by(tier_name='default').first()
        premium_tier = RateConfiguration.query.filter_by(tier_name='premium').first()
        enterprise_tier = RateConfiguration.query.filter_by(tier_name='enterprise').first()
        
        assert default_tier is not None
        assert default_tier.is_default is True
        assert premium_tier is not None
        assert enterprise_tier is not None
        
        # Should have exactly one default tier
        default_count = RateConfiguration.query.filter_by(is_default=True).count()
        assert default_count == 1 