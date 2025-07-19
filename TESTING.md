# ForceWeaver MCP API - Testing Guide

## 🚀 **Quick Start - Test Everything**

```bash
# Run all tests (recommended)
python run_all_tests.py

# Expected final output:
# 🎉 ALL TESTS PASSED!
# ✅ Your ForceWeaver MCP API is fully tested and ready for deployment!
```

## 📋 **Individual Test Commands**

### **1. Unit Tests (Fastest)**
```bash
# Test all components individually
python test_local.py

# Tests: App creation, database models, encryption, API keys, 
#        authentication, Salesforce service, health checker, etc.
```

### **2. Integration Tests**
```bash
# Test with real server running
python test_integration.py

# Tests: Complete workflows, server startup, database init,
#        customer creation, API auth, health checks, etc.
```

### **3. Setup Test Data**
```bash
# Create test customers and API keys
python setup_test_data.py

# Creates: 3 test customers with API keys and mock Salesforce connections
```

### **4. Manual Testing**
```bash
# Start the server
python run.py

# In another terminal, test endpoints:
curl http://localhost:5000/health
curl http://localhost:5000/api/mcp/tools

# Test with API key (get from setup_test_data.py output):
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5000/api/mcp/status
```

## 🧪 **Test Suite Overview**

| Test Suite | Purpose | Time | What it tests |
|------------|---------|------|---------------|
| **Unit Tests** | Component isolation | ~30s | Models, security, services, routes |
| **Integration Tests** | End-to-end workflows | ~60s | Complete API workflows with real server |
| **Test Data Setup** | Create test customers | ~10s | Database setup, API keys, mock connections |
| **Manual Tests** | HTTP endpoint testing | ~5s | Basic endpoint responses |

## 🔧 **Test Commands Reference**

### **Run All Tests (Recommended)**
```bash
python run_all_tests.py           # Full test suite
python run_all_tests.py full      # Same as above
python run_all_tests.py quick     # Unit tests only
python run_all_tests.py cleanup   # Clean up test data
```

### **Individual Test Scripts**
```bash
python test_local.py               # Unit tests
python test_integration.py         # Integration tests
python setup_test_data.py          # Setup test data
python setup_test_data.py cleanup  # Clean up test data
python test_auth.py                # Authentication tests
```

## 📊 **Expected Test Results**

### **Unit Tests (test_local.py)**
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

...12 total tests...

🎉 ALL TESTS PASSED!
```

### **Integration Tests (test_integration.py)**
```
🧪 Test: Basic Server Health
✅ Basic Server Health: PASSED

🧪 Test: Database Initialization
✅ Database Initialization: PASSED

🧪 Test: Customer Creation
✅ Customer Creation: PASSED

...9 total tests...

🎉 ALL INTEGRATION TESTS PASSED!
```

### **Test Data Setup (setup_test_data.py)**
```
👤 Creating customer: demo@example.com
   ✅ Customer created (ID: 1)
   🔑 API Key: abc123def456...
   🔗 Salesforce Org: 00D123456789DEMO

👤 Creating customer: test@company.com
   ✅ Customer created (ID: 2)
   🔑 API Key: xyz789abc123...
   🔗 Salesforce Org: 00D123456789TEST

🚀 Ready for testing!
```

## 🔍 **Troubleshooting**

### **Common Issues:**

#### **1. Import Errors**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

#### **2. Port Already in Use**
```bash
# Solution: Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

#### **3. Database Errors**
```bash
# Solution: Clean up test databases
python setup_test_data.py cleanup
```

#### **4. Permission Errors**
```bash
# Solution: Make scripts executable
chmod +x *.py
```

## 🎯 **Pre-Deployment Checklist**

Before deploying to production, ensure:

- [ ] `python run_all_tests.py` passes completely
- [ ] All 12 unit tests pass
- [ ] All 9 integration tests pass
- [ ] Test data setup works
- [ ] Manual endpoint tests work
- [ ] No errors in test output

## 🌐 **Manual Testing Examples**

### **Basic Endpoints**
```bash
# Health check
curl http://localhost:5000/health

# API info
curl http://localhost:5000/

# Available tools
curl http://localhost:5000/api/mcp/tools
```

### **Authenticated Endpoints**
```bash
# Get API key from setup_test_data.py output, then:

# Service status
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:5000/api/mcp/status

# Health check (mocked)
curl -X POST \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     http://localhost:5000/api/mcp/health-check
```

## 📈 **Performance Testing**

For performance testing (optional):
```bash
# Test concurrent requests
ab -n 100 -c 10 http://localhost:5000/health

# Test with authentication
ab -n 50 -c 5 -H "Authorization: Bearer YOUR_API_KEY" \
   http://localhost:5000/api/mcp/status
```

## 🎉 **Success Criteria**

Your ForceWeaver MCP API is ready for deployment when:

1. **All automated tests pass** (`python run_all_tests.py` succeeds)
2. **Manual endpoints respond correctly** (health, tools, status, health-check)
3. **Authentication works** (API keys authenticate properly)
4. **Database operations work** (customers, API keys, connections)
5. **Error handling works** (invalid requests return proper errors)

Once all tests pass, you're ready to deploy to production! 🚀 clear