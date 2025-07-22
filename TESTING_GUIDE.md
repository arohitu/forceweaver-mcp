# ForceWeaver MCP Server - Testing Guide

This guide provides comprehensive instructions for testing the ForceWeaver MCP Server system, from unit tests to end-to-end validation.

## 🧪 Testing Overview

### Test Suite Architecture

```
tests/
├── conftest.py                 # Test configuration & fixtures
├── test_models.py             # Unit tests for database models
├── test_api_endpoints.py      # API integration tests
├── test_mcp_server.py         # MCP server functionality tests
└── test_e2e_workflows.py      # End-to-end workflow tests
```

### Testing Levels

1. **Unit Tests**: Test individual components (models, utilities)
2. **Integration Tests**: Test API endpoints and database interactions
3. **MCP Server Tests**: Test MCP protocol compliance and Salesforce integration
4. **End-to-End Tests**: Test complete user workflows

## 🚀 Quick Start

### Run All Tests

```bash
# Run the comprehensive test suite
python run_tests.py

# Run with verbose output
python run_tests.py --verbose

# Run without coverage reporting
python run_tests.py --no-coverage
```

### Run Specific Test Categories

```bash
# Unit tests only
python run_tests.py --unit

# API integration tests only
python run_tests.py --api

# MCP server tests only
python run_tests.py --mcp

# End-to-end tests only
python run_tests.py --e2e

# Code quality checks
python run_tests.py --lint

# Security checks
python run_tests.py --security
```

## 🔧 Test Environment Setup

### Prerequisites

```bash
# Install testing dependencies (already in requirements.txt)
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Optional: Install code quality tools
pip install flake8 black isort bandit safety
```

### Environment Configuration

The test suite automatically configures a test environment:

```python
# Automatic test configuration
FLASK_ENV=testing
TESTING=true
SECRET_KEY=test-secret-key
ENCRYPTION_KEY=test-encryption-key-for-testing-only123456=
```

### Database Setup

Tests use an in-memory SQLite database that's automatically created and destroyed:

- **Database**: Temporary SQLite file
- **Data**: Fresh database for each test session
- **Cleanup**: Automatic cleanup after tests complete

## 📋 Detailed Test Scenarios

### Phase 3: Testing & Validation

#### 1. Unit Tests (`test_models.py`)

**User Model Tests:**
```bash
# Test user creation, password hashing, relationships
pytest tests/test_models.py::TestUserModel -v
```

**API Key Model Tests:**
```bash
# Test key generation, validation, usage tracking
pytest tests/test_models.py::TestAPIKeyModel -v
```

**Salesforce Org Model Tests:**
```bash
# Test encryption, decryption, org management
pytest tests/test_models.py::TestSalesforceOrgModel -v
```

**Usage Log Model Tests:**
```bash
# Test usage tracking and statistics
pytest tests/test_models.py::TestUsageLogModel -v
```

#### 2. API Integration Tests (`test_api_endpoints.py`)

**Authentication Flow Tests:**
```bash
# Test registration, login, logout
pytest tests/test_api_endpoints.py::TestAuthRoutes -v
```

**Dashboard Tests:**
```bash
# Test dashboard functionality
pytest tests/test_api_endpoints.py::TestDashboardRoutes -v
```

**Internal API Tests:**
```bash
# Test MCP server integration endpoints
pytest tests/test_api_endpoints.py::TestInternalAPIRoutes -v
```

**Security Tests:**
```bash
# Test authentication, authorization, input validation
pytest tests/test_api_endpoints.py::TestSecurity -v
```

#### 3. MCP Server Tests (`test_mcp_server.py`)

**Validation Client Tests:**
```bash
# Test API key validation and caching
pytest tests/test_mcp_server.py::TestValidationClient -v
```

**Salesforce Client Tests:**
```bash
# Test OAuth flow and API calls
pytest tests/test_mcp_server.py::TestSalesforceClient -v
```

**Health Checker Tests:**
```bash
# Test Revenue Cloud health checking logic
pytest tests/test_mcp_server.py::TestRevenueCloudHealthChecker -v
```

**MCP Server Integration Tests:**
```bash
# Test complete MCP server functionality
pytest tests/test_mcp_server.py::TestForceWeaverMCPServer -v
```

#### 4. End-to-End Tests (`test_e2e_workflows.py`)

**Complete User Workflow:**
```bash
# Test registration → API key → org → usage
pytest tests/test_e2e_workflows.py::TestCompleteUserWorkflow::test_full_user_onboarding_workflow -v
```

**API Key Lifecycle:**
```bash
# Test create → use → deactivate
pytest tests/test_e2e_workflows.py::TestAPIKeyLifecycle -v
```

**Multi-Org Management:**
```bash
# Test multiple Salesforce org setup
pytest tests/test_e2e_workflows.py::TestSalesforceOrgManagement -v
```

**Integration Simulations:**
```bash
# Test VS Code and Claude Desktop workflows
pytest tests/test_e2e_workflows.py::TestIntegrationExamples -v
```

## 🎯 Critical Test Scenarios

### 1. User Registration & Authentication

**Test Scenario:**
```python
def test_user_registration_and_login():
    """Test complete user onboarding"""
    # 1. Register new user
    # 2. Verify email uniqueness
    # 3. Login with correct credentials
    # 4. Reject invalid credentials
    # 5. Access protected pages
```

**Expected Results:**
- ✅ User created successfully
- ✅ Password properly hashed
- ✅ Login session established
- ✅ Dashboard accessible

### 2. API Key Management

**Test Scenario:**
```python
def test_api_key_lifecycle():
    """Test API key creation and usage"""
    # 1. Create API key
    # 2. Verify key generation (fk_ prefix)
    # 3. Validate key authentication
    # 4. Track usage statistics
    # 5. Deactivate key
```

**Expected Results:**
- ✅ Unique API key generated
- ✅ Key validates correctly
- ✅ Usage tracked accurately
- ✅ Deactivation prevents further use

### 3. Salesforce Integration

**Test Scenario:**
```python
def test_salesforce_org_management():
    """Test Salesforce org connection"""
    # 1. Create org with encrypted credentials
    # 2. Validate credential encryption/decryption
    # 3. Test OAuth flow simulation
    # 4. Handle authentication errors
```

**Expected Results:**
- ✅ Credentials encrypted securely
- ✅ OAuth client credentials flow works
- ✅ API calls authenticated properly
- ✅ Error handling graceful

### 4. MCP Server Functionality

**Test Scenario:**
```python
def test_mcp_health_check():
    """Test complete health check flow"""
    # 1. Validate API key with web app
    # 2. Retrieve Salesforce credentials
    # 3. Authenticate with Salesforce
    # 4. Perform health checks
    # 5. Log usage and costs
```

**Expected Results:**
- ✅ API key validation successful
- ✅ Salesforce authentication works
- ✅ Health checks complete
- ✅ Usage logged correctly

### 5. End-to-End User Workflow

**Test Scenario:**
```python
def test_complete_user_journey():
    """Test user from registration to API usage"""
    # 1. User registers account
    # 2. Creates API key
    # 3. Connects Salesforce org
    # 4. Uses MCP server via API key
    # 5. Views usage statistics
```

**Expected Results:**
- ✅ Complete workflow successful
- ✅ All components integrated properly
- ✅ Usage tracking accurate
- ✅ Billing calculations correct

## 🔍 Test Data & Fixtures

### User Test Data

```python
# Test users created automatically
test_user = {
    'email': 'test@example.com',
    'name': 'Test User',
    'password': 'testpassword'
}

admin_user = {
    'email': 'admin@example.com', 
    'name': 'Admin User',
    'is_admin': True
}
```

### Salesforce Test Data

```python
# Mock Salesforce responses
mock_org_response = {
    'records': [{
        'Id': '00Dxx0000000000EAA',
        'Name': 'Test Organization',
        'OrganizationType': 'Developer Edition',
        'IsSandbox': True
    }]
}

mock_auth_response = {
    'access_token': 'mock_access_token',
    'instance_url': 'https://test.my.salesforce.com'
}
```

### API Key Test Data

```python
# API keys with known values for testing
test_api_key = {
    'name': 'Test API Key',
    'description': 'Key for unit testing',
    'generated_key': 'fk_test_key_12345...'
}
```

## 📊 Coverage Requirements

### Target Coverage Levels

| Component | Target | Critical |
|-----------|--------|----------|
| Models | 95%+ | User, APIKey, SalesforceOrg |
| API Endpoints | 90%+ | Auth, Dashboard, Internal API |
| MCP Server | 85%+ | Health checks, validation |
| Business Logic | 90%+ | Authentication, billing |

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
python run_tests.py

# Open coverage report
open htmlcov/index.html

# View terminal coverage summary
pytest --cov=app --cov=mcp_server --cov-report=term
```

## 🚨 Test Failures & Debugging

### Common Test Failures

#### 1. Database Connection Issues

```bash
# Error: Could not connect to database
# Solution: Check test database configuration

pytest tests/test_models.py -v --tb=long
```

#### 2. Import Errors

```bash
# Error: ModuleNotFoundError
# Solution: Check Python path and imports

export PYTHONPATH=$PWD
pytest tests/
```

#### 3. Async Test Issues

```bash
# Error: RuntimeError: no running event loop
# Solution: Ensure pytest-asyncio is installed

pip install pytest-asyncio
pytest tests/test_mcp_server.py
```

#### 4. Mock/Fixture Issues

```bash
# Error: Fixture not found
# Solution: Check conftest.py and fixture definitions

pytest tests/test_api_endpoints.py::test_name -v --fixtures
```

### Debugging Test Failures

```bash
# Run specific failing test with full traceback
pytest tests/test_models.py::TestUserModel::test_create_user -v --tb=long

# Run test with pdb debugger
pytest tests/test_models.py::TestUserModel::test_create_user --pdb

# Run tests with print statements visible
pytest tests/test_models.py -v -s
```

## 🎭 Mocking & Test Doubles

### Salesforce API Mocking

```python
# Mock Salesforce API calls
@patch('mcp_server.salesforce_client.SalesforceClient.authenticate')
async def test_salesforce_auth(mock_auth):
    mock_auth.return_value = True
    # Test logic here
```

### HTTP Request Mocking

```python
# Mock aiohttp requests
@patch('aiohttp.ClientSession.post')
async def test_api_validation(mock_post):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={'user_id': '123'})
    mock_post.return_value.__aenter__.return_value = mock_response
```

## 🔄 Continuous Integration

### GitHub Actions Integration

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python run_tests.py --no-coverage
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: local
    hooks:
      - id: tests
        name: Tests
        entry: python run_tests.py
        language: system
        pass_filenames: false
EOF

pre-commit install
```

## 📈 Performance Testing

### Load Testing API Endpoints

```python
# Test API performance under load
def test_api_performance():
    """Test API response times"""
    import time
    
    start_time = time.time()
    # Make API request
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 1.0  # Should respond within 1 second
```

### Memory Usage Testing

```python
# Test memory usage doesn't grow excessively
def test_memory_usage():
    """Test memory doesn't leak during operations"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Perform memory-intensive operations
    
    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory
    
    # Allow some growth but not excessive
    assert memory_growth < 50 * 1024 * 1024  # Less than 50MB growth
```

## ✅ Test Checklist

### Before Deployment

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All MCP server tests pass
- [ ] All end-to-end tests pass
- [ ] Code coverage meets targets (90%+)
- [ ] No security vulnerabilities detected
- [ ] Performance tests pass
- [ ] Manual smoke tests completed

### Manual Testing Scenarios

1. **Web Application**
   - [ ] User can register and login
   - [ ] Dashboard loads correctly
   - [ ] API key creation works
   - [ ] Salesforce org connection works
   - [ ] Usage tracking displays correctly

2. **API Endpoints**
   - [ ] Internal validation API works
   - [ ] Usage logging API works
   - [ ] Error handling appropriate
   - [ ] Rate limiting functional

3. **MCP Server** (requires manual MCP client)
   - [ ] Server starts without errors
   - [ ] Tool listing works
   - [ ] Health check tool functions
   - [ ] Error responses formatted correctly

### Production Verification

After deployment:

- [ ] Web app accessible at production URL
- [ ] Database seeded correctly
- [ ] Admin user can login
- [ ] SSL certificate active
- [ ] DNS resolution working
- [ ] Logs show no errors
- [ ] Health check endpoint responds

## 🎯 Testing Best Practices

### 1. Test Independence
- Each test should be independent
- Use fresh database for each test
- Clean up any external side effects

### 2. Descriptive Test Names
```python
def test_api_key_validates_correct_format_and_rejects_invalid():
    """Test that API keys validate properly formatted keys and reject invalid ones"""
```

### 3. Arrange-Act-Assert Pattern
```python
def test_user_creation():
    # Arrange
    user_data = {'email': 'test@example.com', 'name': 'Test User'}
    
    # Act
    user = User(**user_data)
    user.set_password('password')
    
    # Assert
    assert user.email == 'test@example.com'
    assert user.check_password('password') is True
```

### 4. Test Edge Cases
- Empty inputs
- Maximum length inputs
- Invalid data types
- Network failures
- Authentication failures

### 5. Mock External Dependencies
- Mock Salesforce API calls
- Mock HTTP requests
- Mock file system operations
- Mock time-dependent operations

## 📚 Additional Resources

- **pytest Documentation**: https://docs.pytest.org/
- **pytest-asyncio**: https://pytest-asyncio.readthedocs.io/
- **Flask Testing**: https://flask.palletsprojects.com/en/2.3.x/testing/
- **MCP Testing Patterns**: https://modelcontextprotocol.io/testing

---

## 🏁 Conclusion

This comprehensive test suite ensures ForceWeaver MCP Server is reliable, secure, and performant. Regular testing prevents regressions and maintains code quality as the system evolves.

**Remember**: Tests are living documentation - keep them updated as features change! 