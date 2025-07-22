"""
ForceWeaver MCP Server Test Configuration
Pytest fixtures and test configuration
"""
import os
import pytest
import tempfile
from datetime import datetime, timedelta

from app import create_app, db
from app.models.user import User
from app.models.api_key import APIKey
from app.models.salesforce_org import SalesforceOrg
from app.models.usage_log import UsageLog
from app.models.rate_configuration import RateConfiguration


@pytest.fixture(scope="session")
def app():
    """Create test Flask application"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    # Test configuration - use SQLite for local testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',  # Changed from PostgreSQL to SQLite
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'ENCRYPTION_KEY': 'test-encryption-key-for-testing-only123456=',
        'RATELIMIT_STORAGE_URL': 'memory://',
    }
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        db.create_all()
        # Create default rate configurations
        try:
            RateConfiguration.initialize_default_tiers()
        except Exception:
            # Handle case where default tiers might already exist
            pass
        yield app
        
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Test client for making HTTP requests"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Application context for database operations"""
    with app.app_context():
        yield app


@pytest.fixture
def test_user(app_context):
    """Create a test user"""
    user = User(
        email='test@example.com',
        name='Test User'
    )
    user.set_password('testpassword')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_user(app_context):
    """Create an admin user"""
    user = User(
        email='admin@example.com',
        name='Admin User',
        is_admin=True
    )
    user.set_password('adminpassword')
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def test_api_key(test_user):
    """Create a test API key"""
    api_key = APIKey(
        user_id=test_user.id,
        name='Test API Key',
        description='Test key for unit testing'
    )
    db.session.add(api_key)
    db.session.commit()
    return api_key


@pytest.fixture
def test_salesforce_org(test_user):
    """Create a test Salesforce org"""
    org = SalesforceOrg(
        user_id=test_user.id,
        org_identifier='test_org',
        instance_url='https://test.my.salesforce.com',
        client_id='test_client_id',
        is_sandbox=True
    )
    org._encrypt_client_secret('test_client_secret')
    db.session.add(org)
    db.session.commit()
    return org


@pytest.fixture
def test_usage_log(test_user, test_api_key):
    """Create a test usage log"""
    log = UsageLog(
        user_id=test_user.id,
        api_key_id=test_api_key.id,
        tool_name='revenue_cloud_health_check',
        success=True,
        execution_time_ms=1500,
        cost_cents=5
    )
    db.session.add(log)
    db.session.commit()
    return log


@pytest.fixture
def authenticated_client(client, test_user):
    """Client with authenticated user session"""
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
        session['_fresh'] = True
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Client with authenticated admin session"""
    with client.session_transaction() as session:
        session['user_id'] = admin_user.id
        session['_fresh'] = True
    return client


@pytest.fixture
def mock_salesforce_response():
    """Mock Salesforce API response data"""
    return {
        'access_token': 'mock_access_token',
        'instance_url': 'https://test.my.salesforce.com',
        'id': 'https://login.salesforce.com/id/00Dxx0000000000EAA/005xx000000000TAAQ',
        'token_type': 'Bearer',
        'issued_at': '1234567890000',
        'signature': 'mock_signature'
    }


@pytest.fixture
def mock_org_query_response():
    """Mock Salesforce org query response"""
    return {
        'totalSize': 1,
        'done': True,
        'records': [
            {
                'Id': '00Dxx0000000000EAA',
                'Name': 'Test Organization',
                'OrganizationType': 'Developer Edition',
                'IsSandbox': True,
                'InstanceName': 'CS123',
                'LanguageLocaleKey': 'en_US',
                'TimeZoneSidKey': 'America/Los_Angeles',
                'DefaultCurrencyIsoCode': 'USD',
                'UsersCount': 5
            }
        ]
    }


# Test data generators
class TestDataFactory:
    """Factory for generating test data"""
    
    @staticmethod
    def create_user(email=None, name=None, is_admin=False):
        """Create a test user"""
        email = email or f'user{datetime.utcnow().microsecond}@example.com'
        name = name or f'Test User {datetime.utcnow().microsecond}'
        
        user = User(email=email, name=name, is_admin=is_admin)
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def create_api_key(user, name=None):
        """Create a test API key"""
        name = name or f'Test Key {datetime.utcnow().microsecond}'
        
        api_key = APIKey(
            user_id=user.id,
            name=name,
            description=f'Test key created at {datetime.utcnow()}'
        )
        db.session.add(api_key)
        db.session.commit()
        return api_key
    
    @staticmethod
    def create_salesforce_org(user, org_identifier=None):
        """Create a test Salesforce org"""
        org_identifier = org_identifier or f'test_org_{datetime.utcnow().microsecond}'
        
        org = SalesforceOrg(
            user_id=user.id,
            org_identifier=org_identifier,
            instance_url='https://test.my.salesforce.com',
            client_id='test_client_id',
            is_sandbox=True
        )
        org._encrypt_client_secret('test_client_secret')
        db.session.add(org)
        db.session.commit()
        return org


@pytest.fixture
def test_factory():
    """Test data factory fixture"""
    return TestDataFactory 