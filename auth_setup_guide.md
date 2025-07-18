# ForceWeaver MCP API - Dual Authentication Setup Guide

## 🔐 **Authentication Flow Overview**

Your API uses a **robust dual authentication system** for maximum security:

```
AI Agent Request → API Key Auth → Salesforce OAuth → Health Check → Response
     ↓                 ↓              ↓              ↓
  Bearer Token    Customer Lookup   Fresh Token   Org Data
```

## 📋 **Prerequisites**

### 1. Environment Variables Required

```bash
# Required - Flask & Database
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost/forceweaver_mcp
ENCRYPTION_KEY=your-fernet-encryption-key-here

# Required - Salesforce Connected App
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_REDIRECT_URI=https://your-domain.com/api/auth/salesforce/callback
```

### 2. Salesforce Connected App Setup

1. **Create Connected App in Salesforce:**
   - Navigate to: Setup → App Manager → New Connected App
   - Enable OAuth Settings: ✅ Yes
   - Callback URL: `https://your-domain.com/api/auth/salesforce/callback`
   - Selected OAuth Scopes:
     - `api` (Access your basic information)
     - `refresh_token` (Perform requests on your behalf at any time)

2. **Get Client Credentials:**
   - Copy Consumer Key → `SALESFORCE_CLIENT_ID`
   - Copy Consumer Secret → `SALESFORCE_CLIENT_SECRET`

### 3. Generate Encryption Key

```bash
# Generate Fernet encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 🚀 **Setup Steps**

### Step 1: Configure Environment

```bash
# Copy environment template
cp env.template .env

# Edit with your values
nano .env
```

### Step 2: Initialize Database

```bash
# Install dependencies
pip install -r requirements.txt

# Create database tables
python init_db.py
```

### Step 3: Start the API

```bash
# Development
python run.py

# Production
gunicorn -b 0.0.0.0:8080 app:create_app()
```

## 🔑 **Authentication Layer 1: API Key Setup**

### Customer Onboarding Flow

1. **Customer initiates OAuth:**
   ```bash
   curl "https://your-domain.com/api/auth/salesforce/initiate?email=customer@company.com"
   ```

2. **Customer completes Salesforce OAuth** (redirected automatically)

3. **System returns API key:**
   ```json
   {
     "message": "Salesforce connection established successfully",
     "customer_id": 123,
     "api_key": "abc123def456...",
     "note": "Please save this API key securely. It will not be shown again."
   }
   ```

### How Layer 1 Works

```python
# AI Agent sends request with API key
headers = {
    "Authorization": "Bearer abc123def456...",
    "Content-Type": "application/json"
}

# API validates key
@require_api_key
def perform_health_check():
    # g.customer is now available
    customer = g.customer
    connection = customer.salesforce_connection
```

## 🔗 **Authentication Layer 2: Salesforce OAuth**

### How Layer 2 Works

```python
# API retrieves encrypted refresh token
connection = g.customer.salesforce_connection
encrypted_token = connection.encrypted_refresh_token

# Decrypt and use refresh token
decrypted_token = decrypt_token(encrypted_token)
sf = Salesforce(instance_url=connection.instance_url)
sf.refresh_token(decrypted_token)  # Gets fresh access token

# Now has temporary access to customer's Salesforce org
```

### Security Features

- ✅ **Encrypted Storage**: Refresh tokens encrypted with Fernet
- ✅ **Temporary Access**: Access tokens expire, refresh tokens rotate
- ✅ **No Password Storage**: Never handles customer credentials
- ✅ **Org-Specific**: Each customer's connection is isolated

## 🧪 **Testing the Authentication System**

### Test Script

```python
import requests
import json

# Test Configuration
BASE_URL = "https://your-domain.com"
CUSTOMER_EMAIL = "test@company.com"
API_KEY = "your-api-key-here"

def test_authentication_flow():
    """Test complete authentication flow"""
    
    # Step 1: Test API key authentication
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    response = requests.get(f"{BASE_URL}/api/mcp/status", headers=headers)
    if response.status_code == 200:
        print("✅ API Key Authentication: PASSED")
        print(f"Customer: {response.json()['customer_id']}")
    else:
        print("❌ API Key Authentication: FAILED")
        print(f"Error: {response.json()}")
        return
    
    # Step 2: Test Salesforce OAuth authentication
    response = requests.post(f"{BASE_URL}/api/mcp/health-check", headers=headers)
    if response.status_code == 200:
        print("✅ Salesforce OAuth Authentication: PASSED")
        print(f"Org ID: {response.json()['salesforce_org_id']}")
    else:
        print("❌ Salesforce OAuth Authentication: FAILED")
        print(f"Error: {response.json()}")

if __name__ == "__main__":
    test_authentication_flow()
```

### Manual Testing Commands

```bash
# Test 1: Customer onboarding
curl "https://your-domain.com/api/auth/salesforce/initiate?email=test@company.com"

# Test 2: API key authentication
curl -H "Authorization: Bearer your-api-key" \
     "https://your-domain.com/api/mcp/status"

# Test 3: Full health check (both auth layers)
curl -X POST \
     -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     "https://your-domain.com/api/mcp/health-check"
```

## 🔍 **Verification Checklist**

### ✅ **Authentication Layer 1 (API Key)**
- [ ] API key required in Authorization header
- [ ] Invalid keys return 401 Unauthorized
- [ ] Valid keys attach customer to request context
- [ ] API keys are hashed in database (not stored plaintext)

### ✅ **Authentication Layer 2 (Salesforce OAuth)**
- [ ] Refresh tokens stored encrypted in database
- [ ] Tokens successfully decrypt for API calls
- [ ] Fresh access tokens obtained automatically
- [ ] Salesforce API calls work with customer's org

### ✅ **Security Verification**
- [ ] No plaintext credentials stored
- [ ] Encryption key properly set in environment
- [ ] HTTPS enabled for production
- [ ] API key generation is cryptographically secure

## 🚨 **Common Issues & Solutions**

### Issue 1: "Invalid API key" Error

**Cause**: Missing or incorrect API key
**Solution**: 
```bash
# Check customer has completed OAuth flow
curl "https://your-domain.com/api/auth/customer/status?email=customer@company.com"
```

### Issue 2: "No Salesforce connection found"

**Cause**: Customer hasn't completed OAuth flow
**Solution**:
```bash
# Customer needs to complete OAuth
curl "https://your-domain.com/api/auth/salesforce/initiate?email=customer@company.com"
```

### Issue 3: "Error decrypting token"

**Cause**: Missing or incorrect ENCRYPTION_KEY
**Solution**:
```bash
# Generate new encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Set in environment: ENCRYPTION_KEY=the-generated-key
```

### Issue 4: "Failed to create Salesforce client"

**Cause**: Invalid Salesforce credentials or expired tokens
**Solution**:
```bash
# Check Salesforce Connected App settings
# Verify CLIENT_ID and CLIENT_SECRET are correct
# Customer may need to re-authenticate
```

## 📊 **Monitoring & Logging**

The system logs all authentication attempts:

```python
# Successful authentications
INFO: API key authentication successful for customer test@company.com

# Failed attempts
WARNING: Invalid API key attempt from 192.168.1.100
ERROR: Error decrypting token: Invalid token format
```

## 🔒 **Security Best Practices**

1. **Environment Variables**: Never commit credentials to version control
2. **HTTPS Only**: Always use HTTPS in production
3. **Token Rotation**: Salesforce tokens rotate automatically
4. **Key Management**: Use secure key management for ENCRYPTION_KEY
5. **Rate Limiting**: Consider implementing rate limiting per API key
6. **Audit Logging**: Monitor all authentication attempts

## 🎯 **Production Deployment**

### Heroku
```bash
heroku config:set ENCRYPTION_KEY=your-key
heroku config:set SALESFORCE_CLIENT_ID=your-id
heroku config:set SALESFORCE_CLIENT_SECRET=your-secret
heroku config:set SALESFORCE_REDIRECT_URI=https://your-app.herokuapp.com/api/auth/salesforce/callback
```

### Docker
```bash
docker run -p 8080:8080 \
  -e ENCRYPTION_KEY=your-key \
  -e SALESFORCE_CLIENT_ID=your-id \
  -e SALESFORCE_CLIENT_SECRET=your-secret \
  -e SALESFORCE_REDIRECT_URI=https://your-domain.com/api/auth/salesforce/callback \
  forceweaver-mcp
```

Your dual authentication system is now fully configured and ready for production use! 🚀 