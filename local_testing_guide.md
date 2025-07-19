# ForceWeaver MCP API - Local Testing Guide

## 🧪 **Complete Local Testing Suite**

This guide will help you thoroughly test your ForceWeaver MCP API locally before deployment.

## 📋 **Testing Overview**

We'll test all components:
- ✅ **Unit Tests**: Individual component testing
- ✅ **Integration Tests**: End-to-end workflow testing  
- ✅ **API Tests**: HTTP endpoint testing
- ✅ **Security Tests**: Authentication and encryption
- ✅ **Database Tests**: Model and relationship testing
- ✅ **Mock Tests**: Salesforce service mocking

## 🚀 **Quick Start**

### Step 1: Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install additional testing dependencies
pip install pytest pytest-mock pytest-cov
```

### Step 2: Run Unit Tests

```bash
# Run comprehensive unit test suite
python test_local.py

# Expected output:
# 🧪 ForceWeaver MCP API - Local Unit Testing Suite
# ============================================================
# 🎉 ALL TESTS PASSED!
# ✅ Your ForceWeaver MCP API is ready for local testing
```

### Step 3: Run Integration Tests

```bash
# Start local server with test data
python test_integration.py

# Follow prompts to test complete workflows
```

## 🔧 **Detailed Testing Steps**

### **1. Unit Testing (test_local.py)**

Tests all components in isolation:

```bash
python test_local.py
```

**What it tests:**
- ✅ Application creation and configuration
- ✅ Database models and relationships
- ✅ Token encryption/decryption
- ✅ API key generation and hashing
- ✅ HTTP endpoints (unauthenticated)
- ✅ API key authentication
- ✅ Salesforce service (mocked)
- ✅ Health checker (mocked)
- ✅ OAuth flow (mocked)
- ✅ Complete workflow simulation
- ✅ Error handling
- ✅ MCP compliance

**Sample Output:**
```
🧪 Test 1: Application Creation
✅ Application created successfully

🧪 Test 2: Database Models
✅ Customer model works
✅ APIKey model works
✅ SalesforceConnection model works
✅ Model relationships work

🧪 Test 3: Encryption/Decryption
✅ Token encryption/decryption works
✅ Handles None values correctly
...
```

### **2. Integration Testing (test_integration.py)**

Tests complete workflows with real server:

```bash
python test_integration.py
```

**What it tests:**
- ✅ Local server startup
- ✅ Database initialization
- ✅ Customer onboarding flow
- ✅ API key authentication
- ✅ Salesforce connection simulation
- ✅ Health check execution
- ✅ Error scenarios

### **3. API Testing (test_api.py)**

Tests HTTP endpoints directly:

```bash
python test_api.py
```

**What it tests:**
- ✅ All endpoint responses
- ✅ Authentication headers
- ✅ Request/response formats
- ✅ Error codes and messages
- ✅ JSON schema validation

### **4. Security Testing (test_security.py)**

Tests security components:

```bash
python test_security.py
```

**What it tests:**
- ✅ Token encryption strength
- ✅ API key uniqueness
- ✅ Hash collision resistance
- ✅ Authentication bypass attempts
- ✅ Injection attack prevention

## 🎯 **Test Coverage**

### **Components Tested:**

#### **✅ Core Components**
- `app/__init__.py` - Application factory
- `app/models.py` - Database models
- `app/core/security.py` - Security functions
- `app/core/errors.py` - Error handling
- `app/core/logging_config.py` - Logging

#### **✅ API Routes**
- `app/api/auth_routes.py` - OAuth endpoints
- `app/api/mcp_routes.py` - MCP endpoints

#### **✅ Services**
- `app/services/salesforce_service.py` - Salesforce integration
- `app/services/health_checker_service.py` - Health checks

#### **✅ Configuration**
- `config.py` - Environment configuration
- Database connectivity
- Environment variable handling

## 🛠️ **Test Environment Setup**

### **Automatic Setup (Recommended)**

The test suite automatically:
- Creates temporary SQLite database
- Sets test environment variables
- Mocks external services
- Cleans up after tests

### **Manual Setup (Optional)**

If you want to test with specific configurations:

```bash
# Create test environment file
cp env.template .env.test

# Edit test configuration
nano .env.test

# Set test environment variables
export SECRET_KEY=test-secret-key
export DATABASE_URL=sqlite:///test.db
export ENCRYPTION_KEY=test-encryption-key
export SALESFORCE_CLIENT_ID=test-client-id
export SALESFORCE_CLIENT_SECRET=test-client-secret
```

## 🧪 **Individual Component Testing**

### **Test Database Models**

```python
# Test customer creation
python -c "
from app import create_app, db
from app.models import Customer
import os

os.environ['DATABASE_URL'] = 'sqlite:///test.db'
app = create_app()
with app.app_context():
    db.create_all()
    customer = Customer(email='test@example.com')
    db.session.add(customer)
    db.session.commit()
    print(f'Customer created: {customer.id}')
"
```

### **Test Encryption**

```python
# Test token encryption
python -c "
from app.core.security import encrypt_token, decrypt_token
import os

os.environ['ENCRYPTION_KEY'] = 'test-key'
token = 'test-refresh-token'
encrypted = encrypt_token(token)
decrypted = decrypt_token(encrypted)
print(f'Original: {token}')
print(f'Encrypted: {encrypted}')
print(f'Decrypted: {decrypted}')
print(f'Match: {token == decrypted}')
"
```

### **Test API Key Generation**

```python
# Test API key generation
python -c "
from app.core.security import generate_api_key, hash_api_key

key1 = generate_api_key()
key2 = generate_api_key()
hash1 = hash_api_key(key1)
hash2 = hash_api_key(key1)

print(f'Key 1: {key1}')
print(f'Key 2: {key2}')
print(f'Unique: {key1 != key2}')
print(f'Hash 1: {hash1}')
print(f'Hash 2: {hash2}')
print(f'Consistent: {hash1 == hash2}')
"
```

## 🌐 **Local Server Testing**

### **Start Development Server**

```bash
# Method 1: Using run.py
python run.py

# Method 2: Using Flask CLI
export FLASK_APP=app
export FLASK_ENV=development
flask run

# Method 3: Using Gunicorn
gunicorn -b 0.0.0.0:5000 app:create_app()
```

### **Test Endpoints Manually**

```bash
# Test basic endpoints
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/api/mcp/tools

# Test with authentication (after setup)
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:5000/api/mcp/status
```

## 📊 **Test Data Setup**

### **Create Test Customer**

```python
# Create test customer with API key
python -c "
from app import create_app, db
from app.models import Customer, APIKey
from app.core.security import generate_api_key, hash_api_key
import os

os.environ['DATABASE_URL'] = 'sqlite:///test.db'
app = create_app()
with app.app_context():
    db.create_all()
    
    # Create customer
    customer = Customer(email='test@example.com')
    db.session.add(customer)
    db.session.flush()
    
    # Create API key
    api_key_value = generate_api_key()
    api_key = APIKey(
        hashed_key=hash_api_key(api_key_value),
        customer_id=customer.id
    )
    db.session.add(api_key)
    db.session.commit()
    
    print(f'Customer ID: {customer.id}')
    print(f'API Key: {api_key_value}')
    print('Save this API key for testing!')
"
```

## 🔍 **Debugging Tests**

### **Verbose Test Output**

```bash
# Run tests with maximum verbosity
python test_local.py -v

# Run specific test
python -m unittest test_local.TestForceWeaverMCPAPI.test_01_app_creation -v
```

### **Test Database Inspection**

```python
# Inspect test database
python -c "
from app import create_app, db
from app.models import Customer, APIKey, SalesforceConnection
import os

os.environ['DATABASE_URL'] = 'sqlite:///test.db'
app = create_app()
with app.app_context():
    customers = Customer.query.all()
    api_keys = APIKey.query.all()
    connections = SalesforceConnection.query.all()
    
    print(f'Customers: {len(customers)}')
    print(f'API Keys: {len(api_keys)}')
    print(f'Connections: {len(connections)}')
"
```

### **Common Issues & Solutions**

#### **Issue 1: Import Errors**
```bash
# Solution: Ensure correct Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python test_local.py
```

#### **Issue 2: Database Errors**
```bash
# Solution: Clean up test database
rm test.db
python test_local.py
```

#### **Issue 3: Environment Variables**
```bash
# Solution: Check environment variables
python -c "import os; print(os.environ.get('SECRET_KEY'))"
```

## 🎯 **Pre-Deployment Checklist**

Before deploying, ensure all tests pass:

### **✅ Unit Tests**
- [ ] All 12 unit tests pass
- [ ] No deprecation warnings
- [ ] Clean test database cleanup

### **✅ Integration Tests**
- [ ] Server starts successfully
- [ ] Database initializes correctly
- [ ] All endpoints respond correctly
- [ ] Authentication works end-to-end

### **✅ Security Tests**
- [ ] Token encryption/decryption works
- [ ] API keys are unique and secure
- [ ] Authentication cannot be bypassed
- [ ] Error messages don't leak sensitive info

### **✅ Performance Tests**
- [ ] Response times under 2 seconds
- [ ] Database queries are efficient
- [ ] No memory leaks in long-running tests

## 🚀 **Next Steps**

After all local tests pass:

1. **✅ Run Complete Test Suite**
   ```bash
   python test_local.py
   python test_integration.py
   python test_api.py
   python test_security.py
   ```

2. **✅ Test with Real Data**
   - Set up actual Salesforce Connected App
   - Test with real customer onboarding
   - Verify health checks work with real org

3. **✅ Performance Testing**
   - Test with multiple concurrent requests
   - Verify database performance under load
   - Test memory usage over time

4. **✅ Deploy to Staging**
   - Use same configuration as production
   - Test with production-like data
   - Verify all integrations work

Your ForceWeaver MCP API is now thoroughly tested and ready for deployment! 🎉 