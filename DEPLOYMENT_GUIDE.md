# 🚀 **ForceWeaver SaaS Deployment Guide**

## 📋 **Complete Deployment for Dual-Domain SaaS Application**

This guide will deploy your **integrated ForceWeaver application** with:
- **`healthcheck.forceweaver.com`** - Web dashboard for users
- **`api.forceweaver.com`** - MCP API for AI agents

## 🏗️ **Architecture Overview**

```
Single Heroku App
├── healthcheck.forceweaver.com (Web Dashboard)
│   ├── User Registration/Login
│   ├── Google OAuth Integration
│   ├── Salesforce Org Management
│   ├── API Key Management
│   └── Health Check History
└── api.forceweaver.com (MCP API)
    ├── AI Agent Authentication
    ├── Health Check Endpoints
    ├── MCP Tool Discovery
    └── Customer OAuth Integration
```

## 🔧 **Phase 1: Pre-Deployment Setup**

### **1. Create Required OAuth Applications**

#### **A. Salesforce Connected App**
1. **Login to Salesforce Developer Org**
2. **Setup → App Manager → New Connected App**
3. **Configure OAuth Settings:**
   ```
   App Name: ForceWeaver Health Checker
   API Name: ForceWeaver_Health_Checker
   Contact Email: your-email@example.com
   
   OAuth Settings:
   ✅ Enable OAuth Settings
   Callback URL: https://api.forceweaver.com/api/auth/salesforce/callback
   
   Selected OAuth Scopes:
   ✅ Access and manage your data (api)
   ✅ Perform requests on your behalf at any time (refresh_token, offline_access)
   ✅ Provide access to your data via the Web (web)
   ```
4. **Save and Copy:**
   - Consumer Key (SALESFORCE_CLIENT_ID)
   - Consumer Secret (SALESFORCE_CLIENT_SECRET)

#### **B. Google OAuth Application**
1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create New Project** or select existing
3. **APIs & Services → Credentials**
4. **Create Credentials → OAuth 2.0 Client IDs**
5. **Configure OAuth:**
   ```
   Application type: Web application
   Name: ForceWeaver Dashboard
   
   Authorized redirect URIs:
   https://healthcheck.forceweaver.com/auth/google/callback
   ```
6. **Copy:**
   - Client ID (GOOGLE_CLIENT_ID)
   - Client Secret (GOOGLE_CLIENT_SECRET)

### **2. Generate Security Keys**

```bash
# Generate SECRET_KEY
export SECRET_KEY=$(openssl rand -base64 32)

# Generate ENCRYPTION_KEY
export ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
```

## 🚀 **Phase 2: Heroku Deployment**

### **1. Create and Configure Heroku App**

```bash
# Create Heroku app
heroku create forceweaver-saas

# Add PostgreSQL database
heroku addons:create heroku-postgresql:essential-0

# Add logging (optional)
heroku addons:create papertrail:choklad
```

### **2. Set Environment Variables**

```bash
# Core Configuration
heroku config:set SECRET_KEY="$SECRET_KEY"
heroku config:set ENCRYPTION_KEY="$ENCRYPTION_KEY"

# Salesforce OAuth
heroku config:set SALESFORCE_CLIENT_ID="your_salesforce_consumer_key"
heroku config:set SALESFORCE_CLIENT_SECRET="your_salesforce_consumer_secret"
heroku config:set SALESFORCE_REDIRECT_URI="https://api.forceweaver.com/api/auth/salesforce/callback"

# Google OAuth
heroku config:set GOOGLE_CLIENT_ID="your_google_client_id"
heroku config:set GOOGLE_CLIENT_SECRET="your_google_client_secret"

# App Configuration
heroku config:set APP_NAME="ForceWeaver SaaS"
heroku config:set APP_VERSION="1.0.0"

# Verify configuration
heroku config
```

### **3. Deploy Application**

```bash
# Commit all changes
git add .
git commit -m "Complete SaaS application with dual domains"

# Add Heroku remote
heroku git:remote -a forceweaver-saas

# Deploy to Heroku
git push heroku main

# Check deployment status
heroku logs --tail
```

### **4. Initialize Database**

```bash
# Run database migrations
heroku run python init_db.py

# Verify database
heroku pg:info
```

## 🌐 **Phase 3: Custom Domain Configuration**

### **1. Add Domains to Heroku**

```bash
# Add both custom domains
heroku domains:add healthcheck.forceweaver.com
heroku domains:add api.forceweaver.com

# Get DNS targets
heroku domains
```

### **2. Configure DNS Records**

In your domain registrar (GoDaddy, Namecheap, etc.):

#### **For healthcheck.forceweaver.com:**
```
Type: CNAME
Name: healthcheck
Value: [your-heroku-dns-target-1]
TTL: 300 seconds
```

#### **For api.forceweaver.com:**
```
Type: CNAME
Name: api  
Value: [your-heroku-dns-target-2]
TTL: 300 seconds
```

### **3. Verify SSL Certificates**

```bash
# Check SSL status (wait 5-10 minutes after DNS setup)
heroku certs

# Both domains should show "ACM Status: OK"
heroku domains
```

## 🧪 **Phase 4: Testing & Verification**

### **1. Test Web Dashboard**

```bash
# Test web dashboard
curl -I https://healthcheck.forceweaver.com/
# Should redirect to login page

# Test registration
# Visit: https://healthcheck.forceweaver.com/auth/register

# Test Google OAuth
# Visit: https://healthcheck.forceweaver.com/auth/google
```

### **2. Test API Endpoints**

```bash
# Test API health
curl https://api.forceweaver.com/health

# Test MCP tools discovery
curl https://api.forceweaver.com/api/mcp/tools

# Test OAuth initiation
curl "https://api.forceweaver.com/api/auth/salesforce/initiate?email=test@example.com"
```

### **3. Complete Integration Test**

1. **Register via Web Dashboard:**
   - Go to: `https://healthcheck.forceweaver.com`
   - Register new account
   - Login successfully

2. **Connect Salesforce Org:**
   - Navigate to "Salesforce Org" page
   - Click "Connect Salesforce Org"
   - Complete OAuth flow
   - Verify connection shows in dashboard

3. **Generate API Key:**
   - Go to "API Keys" page
   - Create new API key
   - Copy and save the key

4. **Test API Integration:**
   ```bash
   # Use the generated API key
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.forceweaver.com/api/mcp/status

   # Run health check via API
   curl -X POST \
        -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Content-Type: application/json" \
        https://api.forceweaver.com/api/mcp/health-check
   ```

## 📊 **Phase 5: Monitoring & Analytics**

### **1. Set Up Application Monitoring**

```bash
# Add New Relic (optional)
heroku addons:create newrelic:wayne

# Configure logging
heroku logs --tail

# Set up log drains (optional)
heroku drains:add https://your-log-service.com/endpoint
```

### **2. Database Monitoring**

```bash
# Monitor database performance
heroku pg:stats

# Set up automated backups
heroku pg:backups:capture
heroku pg:backups:schedules
```

### **3. Custom Analytics Dashboard**

Add to your dashboard template:
```html
<!-- Google Analytics (optional) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🔒 **Phase 6: Security & Performance**

### **1. Security Checklist**

- ✅ **HTTPS Enforced**: All traffic encrypted
- ✅ **Environment Variables**: All secrets secured
- ✅ **CSRF Protection**: Forms protected
- ✅ **Session Security**: Secure session configuration
- ✅ **SQL Injection**: SQLAlchemy ORM prevents injection
- ✅ **XSS Prevention**: Template auto-escaping enabled

### **2. Performance Optimization**

```bash
# Scale dynos if needed
heroku ps:scale web=2

# Enable compression
heroku config:set FLASK_ENV=production

# Monitor performance
heroku metrics
```

### **3. Rate Limiting (Optional)**

Add to your application:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to API endpoints
@app.route('/api/mcp/health-check')
@limiter.limit("10 per minute")
def health_check():
    # Your code here
```

## 💰 **Phase 7: Monetization Setup**

### **1. Stripe Integration (Optional)**

```bash
# Add Stripe configuration
heroku config:set STRIPE_PUBLISHABLE_KEY="your_stripe_publishable_key"
heroku config:set STRIPE_SECRET_KEY="your_stripe_secret_key"

# Add to requirements.txt
echo "stripe==5.8.0" >> requirements.txt
```

### **2. Usage Tracking**

The application already tracks:
- API key usage timestamps
- Health check history
- User activity logs

### **3. Billing Dashboard**

Add billing routes to show:
- Monthly usage statistics
- API call counts
- Health check frequency
- Subscription status

## 🎯 **Phase 8: Go-Live Checklist**

### **Before Going Live:**

- [ ] **Both domains accessible** and SSL working
- [ ] **User registration** works end-to-end
- [ ] **Google OAuth** login functional
- [ ] **Salesforce OAuth** connects successfully
- [ ] **API key generation** working
- [ ] **Health checks** execute properly
- [ ] **API endpoints** respond correctly for AI agents
- [ ] **Database backups** configured
- [ ] **Monitoring** set up and working
- [ ] **Error handling** graceful
- [ ] **Performance** acceptable under load

### **After Going Live:**

1. **Create documentation** for AI developers
2. **Set up customer support** process
3. **Monitor application** performance
4. **Track user** adoption metrics
5. **Iterate based** on user feedback

## 🚀 **Success Criteria**

Your ForceWeaver SaaS is **production-ready** when:

1. **✅ `https://healthcheck.forceweaver.com`** - Users can register, login, and manage Salesforce connections
2. **✅ `https://api.forceweaver.com`** - AI agents can authenticate and perform health checks
3. **✅ OAuth flows** work for both Salesforce and Google
4. **✅ Dashboard** shows org details, API keys, and health history
5. **✅ MCP compliance** verified for AI agent integration
6. **✅ Security** measures active and monitoring in place

## 🎉 **Launch Commands Summary**

```bash
# Complete deployment sequence:

# 1. Deploy to Heroku
git push heroku main

# 2. Configure domains
heroku domains:add healthcheck.forceweaver.com
heroku domains:add api.forceweaver.com

# 3. Set all environment variables (see Phase 2)
heroku config:set SECRET_KEY="..." ENCRYPTION_KEY="..." # etc.

# 4. Initialize database
heroku run python init_db.py

# 5. Verify deployment
curl https://healthcheck.forceweaver.com/
curl https://api.forceweaver.com/health

# 6. Test complete workflow
# Register → Connect Salesforce → Generate API Key → Test API
```

Your **ForceWeaver SaaS** is now a **complete, production-ready application** serving both human users and AI agents! 🎊

## 📞 **Support & Next Steps**

- **Web Dashboard**: Full user management and org monitoring
- **AI Agent API**: MCP-compliant endpoints for health checks
- **Dual Authentication**: Secure for both humans and machines
- **Scalable Architecture**: Ready for enterprise customers
- **Monetization Ready**: Usage tracking and billing infrastructure

Your application is perfectly positioned to serve the AI agent ecosystem while providing an intuitive web experience for end users! 🚀 