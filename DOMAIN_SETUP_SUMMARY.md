# 🎯 ForceWeaver Domain Setup - Changes Summary

## ✅ Issues Resolved

### **Primary Issue Fixed:**
- **Problem**: After Salesforce login, users weren't getting redirected to `https://staging-healthcheck.forceweaver.com/dashboard/`
- **Root Cause**: OAuth callback was using relative URLs (`/dashboard/salesforce`) instead of external domain URLs
- **Solution**: Updated redirect logic to use external domain URLs based on environment

## 🔧 Technical Changes Made

### **1. Updated `config.py`**
- ✅ **Fixed Salesforce OAuth redirect URIs**: Now uses domain-based URLs instead of hardcoded Heroku URLs
- ✅ **Fixed Google OAuth redirect URIs**: Now uses domain-based URLs for both environments
- ✅ **Added external URL helpers**: New methods `get_dashboard_url()` and `get_api_url()` for generating full external URLs

### **2. Updated `app/api/auth_routes.py`**
- ✅ **Fixed successful OAuth redirect**: Now redirects to external dashboard URL instead of relative URL
- ✅ **Fixed error OAuth redirect**: Error cases also redirect to external dashboard URL
- ✅ **Enhanced logging**: Better tracking of redirect URLs in logs

### **3. Updated `env.template`**
- ✅ **Corrected documentation**: Shows correct staging and production domain examples
- ✅ **Updated callback URLs**: Reflects the new domain-based redirect URIs

### **4. Updated `STAGING_PRODUCTION_GUIDE.md`**
- ✅ **Added OAuth testing section**: Clear instructions for testing redirect flows
- ✅ **Enhanced Salesforce setup**: Better guidance for configuring Connected Apps

### **5. Created `test_domains.py`**
- ✅ **Domain validation script**: Automatically tests staging and production configurations
- ✅ **OAuth URL verification**: Validates all redirect URIs are correct

## 🌐 Current Domain Configuration

| Environment | Web Dashboard | API Endpoint |
|-------------|---------------|--------------|
| **Staging** | `staging-healthcheck.forceweaver.com` | `staging-api.forceweaver.com` |
| **Production** | `healthcheck.forceweaver.com` | `api.forceweaver.com` |

## 📋 OAuth Redirect URLs (Fixed)

### **Salesforce OAuth Callbacks:**
- **Staging**: `https://staging-api.forceweaver.com/api/auth/salesforce/callback`
- **Production**: `https://api.forceweaver.com/api/auth/salesforce/callback`

### **Google OAuth Callbacks:**
- **Staging**: `https://staging-healthcheck.forceweaver.com/auth/google/callback`
- **Production**: `https://healthcheck.forceweaver.com/auth/google/callback`

### **Post-OAuth Dashboard Redirects:**
- **Staging**: `https://staging-healthcheck.forceweaver.com/dashboard/salesforce`
- **Production**: `https://healthcheck.forceweaver.com/dashboard/salesforce`

## 🚀 Next Steps Required

### **1. Update Salesforce Connected App** ⚠️ **CRITICAL**
You need to update your Salesforce Connected App with both callback URLs:

1. **Login to Salesforce Developer Org**
2. **Navigate to**: Setup → App Manager → [Your Connected App] → Edit
3. **Add both callback URLs**:
   ```
   https://api.forceweaver.com/api/auth/salesforce/callback
   https://staging-api.forceweaver.com/api/auth/salesforce/callback
   ```
4. **Save the changes**

### **2. Update Google OAuth Application** ⚠️ **CRITICAL**
Update your Google Cloud Console OAuth app:

1. **Go to**: Google Cloud Console → Credentials
2. **Edit your OAuth 2.0 Client ID**
3. **Add both redirect URIs**:
   ```
   https://healthcheck.forceweaver.com/auth/google/callback
   https://staging-healthcheck.forceweaver.com/auth/google/callback
   ```
4. **Save the changes**

### **3. Test the Fixed OAuth Flow**
Once OAuth apps are updated:

#### **Test Staging:**
1. Go to: `https://staging-healthcheck.forceweaver.com`
2. Register/Login
3. Connect Salesforce Org
4. **Expected**: Redirected back to staging dashboard after OAuth

#### **Test Production:**  
1. Go to: `https://healthcheck.forceweaver.com`
2. Register/Login
3. Connect Salesforce Org
4. **Expected**: Redirected back to production dashboard after OAuth

## ✅ Verification Commands

### **Test Domain Configuration:**
```bash
python3 test_domains.py
```

### **Test Environment Detection:**
```bash
# Test staging
IS_STAGING=true python3 -c "from config import Config; print('Dashboard:', Config.get_dashboard_url('/dashboard/salesforce'))"

# Test production  
IS_STAGING=false python3 -c "from config import Config; print('Dashboard:', Config.get_dashboard_url('/dashboard/salesforce'))"
```

## 🎉 Expected Results

After completing the OAuth app updates:

- ✅ **Staging OAuth**: Salesforce login → `https://staging-healthcheck.forceweaver.com/dashboard/salesforce`
- ✅ **Production OAuth**: Salesforce login → `https://healthcheck.forceweaver.com/dashboard/salesforce`
- ✅ **Environment Detection**: Automatic based on `IS_STAGING` environment variable
- ✅ **Cross-Domain Support**: API and Dashboard domains work together seamlessly

## 🔍 Troubleshooting

If OAuth redirects still don't work:

1. **Check OAuth App Configuration**: Ensure both callback URLs are added
2. **Verify Environment Variables**: Confirm `IS_STAGING` is set correctly  
3. **Check Application Logs**: Look for redirect URL debug output
4. **Run Domain Test**: Use `python3 test_domains.py` to verify configuration
5. **Clear Browser Cache**: OAuth redirects can be cached

---

**All code changes are complete!** 🚀 You just need to update your OAuth applications with the new callback URLs. 