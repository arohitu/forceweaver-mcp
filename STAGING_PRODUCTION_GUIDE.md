# 🏗️ **Staging & Production Deployment Guide**

## 📋 **Dual Environment Architecture**

Your ForceWeaver SaaS application supports **two complete environments**:

### **🧪 Staging Environment**
- **Branch**: `staging`
- **Heroku App**: `forceweaver-mcp-staging`
- **Domains**:
  - `staging-healthcheck.forceweaver.com` (Web Dashboard)
  - `staging-api.forceweaver.com` (MCP API)
- **Purpose**: Testing, QA, and development validation

### **🚀 Production Environment**
- **Branch**: `main`
- **Heroku App**: `forceweaver-mcp-api`
- **Domains**:
  - `healthcheck.forceweaver.com` (Web Dashboard)
  - `api.forceweaver.com` (MCP API)
- **Purpose**: Live customer-facing application

## 🔧 **Phase 1: OAuth Applications Setup**

### **1. Salesforce Connected Apps**

You need **TWO separate Salesforce Connected Apps** (or configure one with multiple redirect URIs):

#### **Option A: Single Connected App (Recommended)**
1. **Login to Salesforce Developer Org**
2. **Setup → App Manager → Edit your existing Connected App**
3. **Add Both Callback URLs:**
   ```
   https://api.forceweaver.com/api/auth/salesforce/callback
   https://staging-api.forceweaver.com/api/auth/salesforce/callback
   ```

#### **Option B: Separate Connected Apps**
Create two identical connected apps with different callback URLs.

### **2. Google OAuth Applications**

#### **Option A: Single Google OAuth App (Recommended)**
1. **Google Cloud Console → Credentials**
2. **Edit your existing OAuth 2.0 Client**
3. **Add Both Redirect URIs:**
   ```
   https://healthcheck.forceweaver.com/auth/google/callback
   https://staging-healthcheck.forceweaver.com/auth/google/callback
   ```

#### **Option B: Separate Google Apps**
Create separate OAuth apps for staging and production.

## 🚀 **Phase 2: Staging Environment Deployment**

### **1. Create Staging Heroku App**

```bash
# Create staging app
heroku create forceweaver-mcp-staging

# Add PostgreSQL database
heroku addons:create heroku-postgresql:essential-0 -a forceweaver-mcp-staging

# Add logging (optional)
heroku addons:create papertrail:choklad -a forceweaver-mcp-staging
```

### **2. Set Staging Environment Variables**

```bash
# Core Configuration
heroku config:set -a forceweaver-mcp-staging \
  SECRET_KEY="$(openssl rand -base64 32)" \
  ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  IS_STAGING=true \
  FLASK_ENV=staging

# Salesforce OAuth (same as production or separate)
heroku config:set -a forceweaver-mcp-staging \
  SALESFORCE_CLIENT_ID="your_salesforce_consumer_key" \
  SALESFORCE_CLIENT_SECRET="your_salesforce_consumer_secret"

# Google OAuth (same as production or separate)
heroku config:set -a forceweaver-mcp-staging \
  GOOGLE_CLIENT_ID="your_google_client_id" \
  GOOGLE_CLIENT_SECRET="your_google_client_secret"

# Verify staging configuration
heroku config -a forceweaver-mcp-staging
```

### **3. Deploy Staging**

```bash
# Ensure you're on staging branch
git checkout staging

# Merge latest changes from main (if needed)
git merge main

# Commit any staging-specific changes
git add .
git commit -m "Staging environment updates"

# Add staging Heroku remote
heroku git:remote -a forceweaver-mcp-staging -r staging

# Deploy to staging
git push staging staging:main

# Initialize staging database
heroku run python init_db.py -a forceweaver-mcp-staging

# Check staging logs
heroku logs --tail -a forceweaver-mcp-staging
```

### **4. Configure Staging Domains**

```bash
# Add staging domains
heroku domains:add staging-healthcheck.forceweaver.com -a forceweaver-mcp-staging
heroku domains:add staging-api.forceweaver.com -a forceweaver-mcp-staging

# Get DNS targets
heroku domains -a forceweaver-mcp-staging
```

### **5. Update DNS Records**

In your domain registrar:

#### **For staging-healthcheck.forceweaver.com:**
```
Type: CNAME
Name: staging-healthcheck
Value: [staging-heroku-dns-target-1]
TTL: 300 seconds
```

#### **For staging-api.forceweaver.com:**
```
Type: CNAME
Name: staging-api
Value: [staging-heroku-dns-target-2]
TTL: 300 seconds
```

## 🎯 **Phase 3: Production Environment Deployment**

### **1. Create Production Heroku App**

```bash
# Create production app
heroku create forceweaver-mcp-api

# Add PostgreSQL database
heroku addons:create heroku-postgresql:standard-0 -a forceweaver-mcp-api

# Add monitoring
heroku addons:create newrelic:wayne -a forceweaver-mcp-api
heroku addons:create papertrail:choklad -a forceweaver-mcp-api
```

### **2. Set Production Environment Variables**

```bash
# Core Configuration (different keys for security)
heroku config:set -a forceweaver-mcp-api \
  SECRET_KEY="$(openssl rand -base64 32)" \
  ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  IS_STAGING=false \
  FLASK_ENV=production

# Salesforce OAuth
heroku config:set -a forceweaver-mcp-api \
  SALESFORCE_CLIENT_ID="your_salesforce_consumer_key" \
  SALESFORCE_CLIENT_SECRET="your_salesforce_consumer_secret"

# Google OAuth
heroku config:set -a forceweaver-mcp-api \
  GOOGLE_CLIENT_ID="your_google_client_id" \
  GOOGLE_CLIENT_SECRET="your_google_client_secret"

# Verify production configuration
heroku config -a forceweaver-mcp-api
```

### **3. Deploy Production**

```bash
# Ensure you're on main branch
git checkout main

# Add production Heroku remote
heroku git:remote -a forceweaver-mcp-api -r production

# Deploy to production
git push production main:main

# Initialize production database
heroku run python init_db.py -a forceweaver-mcp-api

# Check production logs
heroku logs --tail -a forceweaver-mcp-api
```

### **4. Configure Production Domains**

```bash
# Add production domains
heroku domains:add healthcheck.forceweaver.com -a forceweaver-mcp-api
heroku domains:add api.forceweaver.com -a forceweaver-mcp-api

# Get DNS targets
heroku domains -a forceweaver-mcp-api
```

### **5. Update DNS Records**

#### **For healthcheck.forceweaver.com:**
```
Type: CNAME
Name: healthcheck
Value: [production-heroku-dns-target-1]
TTL: 300 seconds
```

#### **For api.forceweaver.com:**
```
Type: CNAME
Name: api
Value: [production-heroku-dns-target-2]
TTL: 300 seconds
```

## 🔄 **Phase 4: Deployment Workflow**

### **Staging Deployment Process**

```bash
# 1. Switch to staging branch
git checkout staging

# 2. Merge latest features from main (if needed)
git merge main

# 3. Make staging-specific changes (if any)
# ... make changes ...
git add .
git commit -m "Staging updates"

# 4. Deploy to staging
git push staging staging:main

# 5. Test staging environment
curl https://staging-healthcheck.forceweaver.com/health
curl https://staging-api.forceweaver.com/health
```

### **Production Deployment Process**

```bash
# 1. Ensure staging is thoroughly tested
# 2. Switch to main branch
git checkout main

# 3. Merge tested changes from staging
git merge staging

# 4. Deploy to production
git push production main:main

# 5. Verify production deployment
curl https://healthcheck.forceweaver.com/health
curl https://api.forceweaver.com/health
```

## 🧪 **Phase 5: Testing Both Environments**

### **Staging Environment Tests**

```bash
# Test staging web dashboard
curl -I https://staging-healthcheck.forceweaver.com/
# Should redirect to login

# Test staging API
curl https://staging-api.forceweaver.com/health
# Should return {"status": "healthy"}

# Test staging OAuth initiation
curl "https://staging-api.forceweaver.com/api/auth/salesforce/initiate?email=test@staging.com"
# Should redirect to Salesforce
```

### **Production Environment Tests**

```bash
# Test production web dashboard
curl -I https://healthcheck.forceweaver.com/
# Should redirect to login

# Test production API
curl https://api.forceweaver.com/health
# Should return {"status": "healthy"}

# Test production OAuth initiation
curl "https://api.forceweaver.com/api/auth/salesforce/initiate?email=test@production.com"
# Should redirect to Salesforce
```

### **Full Integration Tests**

#### **Staging Integration:**
1. **Register**: https://staging-healthcheck.forceweaver.com/auth/register
2. **Login**: Test email/password and Google OAuth
3. **Connect Salesforce**: Complete OAuth flow
4. **Generate API Key**: Create and copy key
5. **Test API**: Use key with staging API endpoints

#### **Production Integration:**
1. **Register**: https://healthcheck.forceweaver.com/auth/register
2. **Login**: Test email/password and Google OAuth
3. **Connect Salesforce**: Complete OAuth flow
4. **Generate API Key**: Create and copy key
5. **Test API**: Use key with production API endpoints

## 📊 **Phase 6: Monitoring & Management**

### **Environment Comparison Dashboard**

```bash
# Compare database stats
heroku pg:info -a forceweaver-mcp-staging
heroku pg:info -a forceweaver-mcp-api

# Compare app metrics
heroku metrics -a forceweaver-mcp-staging
heroku metrics -a forceweaver-mcp-api

# Compare logs
heroku logs --tail -a forceweaver-mcp-staging
heroku logs --tail -a forceweaver-mcp-api
```

### **Database Synchronization (Optional)**

To populate staging with production-like data:

```bash
# Create production backup
heroku pg:backups:capture -a forceweaver-mcp-api

# Get backup URL
heroku pg:backups:url -a forceweaver-mcp-api

# Restore to staging (CAREFUL - this overwrites staging data!)
heroku pg:backups:restore [BACKUP_URL] DATABASE_URL -a forceweaver-mcp-staging --confirm forceweaver-mcp-staging
```

### **Configuration Management**

Create a configuration comparison script:

```bash
#!/bin/bash
echo "=== STAGING CONFIG ==="
heroku config -a forceweaver-mcp-staging | grep -E "(IS_STAGING|FLASK_ENV|SALESFORCE|GOOGLE)"

echo "=== PRODUCTION CONFIG ==="
heroku config -a forceweaver-mcp-api | grep -E "(IS_STAGING|FLASK_ENV|SALESFORCE|GOOGLE)"
```

## 🚀 **Phase 7: Git Remote Management**

### **Set Up Multiple Remotes**

```bash
# Add both environments as remotes
git remote add staging https://git.heroku.com/forceweaver-mcp-staging.git
git remote add production https://git.heroku.com/forceweaver-mcp-api.git

# List all remotes
git remote -v
# origin    https://github.com/yourusername/forceweaver-mcp.git (fetch)
# origin    https://github.com/yourusername/forceweaver-mcp.git (push)
# staging   https://git.heroku.com/forceweaver-mcp-staging.git (fetch)
# staging   https://git.heroku.com/forceweaver-mcp-staging.git (push)
# production https://git.heroku.com/forceweaver-mcp-api.git (fetch)
# production https://git.heroku.com/forceweaver-mcp-api.git (push)
```

### **Quick Deployment Commands**

```bash
# Deploy to staging
git push staging staging:main

# Deploy to production
git push production main:main

# Deploy specific branch to staging
git push staging feature-branch:main

# Check staging status
heroku ps -a forceweaver-mcp-staging

# Check production status
heroku ps -a forceweaver-mcp-api
```

## 🎯 **Phase 8: Validation Checklist**

### **Pre-Deployment Checklist**

#### **Staging Environment:**
- [ ] **App deployed** to `forceweaver-mcp-staging`
- [ ] **Domains configured**: staging-healthcheck.forceweaver.com, staging-api.forceweaver.com
- [ ] **SSL certificates** active and valid
- [ ] **Environment variables** set with `IS_STAGING=true`
- [ ] **Database initialized** and accessible
- [ ] **OAuth flows** tested and working
- [ ] **API endpoints** responding correctly
- [ ] **Web dashboard** functional with staging badge

#### **Production Environment:**
- [ ] **App deployed** to `forceweaver-mcp-api`
- [ ] **Domains configured**: healthcheck.forceweaver.com, api.forceweaver.com
- [ ] **SSL certificates** active and valid
- [ ] **Environment variables** set with `IS_STAGING=false`
- [ ] **Database initialized** and accessible
- [ ] **Monitoring** set up (New Relic, logs)
- [ ] **OAuth flows** tested and working
- [ ] **API endpoints** responding correctly
- [ ] **Web dashboard** functional without staging badge

### **Post-Deployment Validation**

```bash
# Validate staging environment
echo "Testing Staging Environment..."
curl -s https://staging-api.forceweaver.com/ | jq '.environment'  # Should show "staging"

# Validate production environment
echo "Testing Production Environment..."
curl -s https://api.forceweaver.com/ | jq '.environment'  # Should show "production"

# Test environment indicators
echo "Checking staging badge visibility..."
curl -s https://staging-healthcheck.forceweaver.com/ | grep -i "staging"  # Should find staging badge

echo "Checking production clean interface..."
curl -s https://healthcheck.forceweaver.com/ | grep -i "staging"  # Should NOT find staging badge
```

## 🎊 **Success Criteria**

Your **dual-environment SaaS** is ready when:

### **✅ Staging Environment:**
1. **Accessible** at staging-healthcheck.forceweaver.com and staging-api.forceweaver.com
2. **Shows "STAGING" badge** in the web interface
3. **API returns `"environment": "staging"`**
4. **OAuth flows** work with staging callback URLs
5. **Separate database** from production
6. **Can deploy from `staging` branch** independently

### **✅ Production Environment:**
1. **Accessible** at healthcheck.forceweaver.com and api.forceweaver.com
2. **Clean interface** without staging indicators
3. **API returns `"environment": "production"`**
4. **OAuth flows** work with production callback URLs
5. **Production database** with proper monitoring
6. **Can deploy from `main` branch** with confidence

## 🔄 **Continuous Integration Workflow**

### **Recommended Development Flow:**

```
1. Feature Development → feature-branch
2. Feature Testing → staging branch → staging environment
3. QA Validation → staging environment
4. Production Release → main branch → production environment
```

### **Branch Management:**

```bash
# Create feature branch
git checkout -b feature/new-health-check
# ... develop feature ...
git commit -am "Add new health check feature"

# Test in staging
git checkout staging
git merge feature/new-health-check
git push staging staging:main
# ... test in staging environment ...

# Release to production
git checkout main
git merge staging
git push production main:main
# ... verify in production ...
```

Your **ForceWeaver SaaS** now has **professional dual-environment deployment** ready for enterprise-level development and operations! 🚀

## 📞 **Quick Reference Commands**

```bash
# Deploy to staging
git checkout staging && git push staging staging:main

# Deploy to production  
git checkout main && git push production main:main

# Check staging status
heroku ps -a forceweaver-mcp-staging

# Check production status
heroku ps -a forceweaver-mcp-api

# View staging logs
heroku logs --tail -a forceweaver-mcp-staging

# View production logs
heroku logs --tail -a forceweaver-mcp-api
```

Both environments are now **independently deployable, fully monitored, and ready for professional SaaS operations**! 🎉 