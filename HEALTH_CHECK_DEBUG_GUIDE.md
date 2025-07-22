# Health Check Debugging Guide

This guide explains how to troubleshoot health check issues using the enhanced debugging capabilities.

## Overview

The health check system has been enhanced with comprehensive debugging to help identify issues with Salesforce API calls that result in "NOT_FOUND" errors.

## Debugging Features Added

### 1. Enhanced Logging
- **Location**: `logs/health_checks.log` - Detailed health check debugging
- **Location**: `logs/debug.log` - General application debugging  
- **Location**: `logs/error.log` - Error logs

### 2. Debug Endpoints
- **`POST /api/mcp/debug`**: Comprehensive debugging with multiple API versions and endpoint validation
- **`POST /api/mcp/test-api-versions`**: Simple API version availability test
- **`POST /api/mcp/health-check`**: Enhanced health check with object availability testing

### 3. Object Availability Check
The health check now includes an object availability check that tests access to:
- Standard objects (User, Organization)
- Metadata objects (EntityDefinition)  
- Revenue Cloud objects (Product2, AttributeDefinition, etc.)

## Debugging Steps for NOT_FOUND Errors

### Step 1: Test API Version Compatibility

```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/test-api-versions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

**What this tests:**
- Which API versions are available in your org
- If the `/services/data` endpoint is accessible
- If specific API versions (v58.0 - v64.0) are working

**Expected Result:** You should see `"success": true` for available API versions.

### Step 2: Comprehensive Debug Test

```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/debug \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

**What this tests:**
- Multiple API versions for compatibility
- Basic queries (User, Organization) with each version
- Direct REST API calls to validate endpoints
- Token refresh process validation
- Instance URL verification

### Step 3: Run Enhanced Health Check

```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/health-check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

**What this includes:**
- Object availability testing
- Conditional checks based on available objects
- Detailed error information with debug context

## Common Issues and Diagnostic Steps

### Issue: ALL Objects Fail with "NOT_FOUND" (Your Current Issue)

**Likely Causes:**
1. **API Version Compatibility**: The API version v64.0 may not be available
2. **Instance URL Issue**: Stored instance URL may be incorrect
3. **Simple-Salesforce Library Issue**: Endpoint construction problems

**Diagnostic Steps:**
1. **Check API Version Availability**: Use `/api/mcp/test-api-versions`
   - If this fails → Instance URL or authentication issue
   - If this succeeds → API version compatibility issue

2. **Compare Instance URLs**: Check if token refresh returns different instance URL
   - Look for `instance_url_match: false` in debug response

3. **Test Multiple API Versions**: Use `/api/mcp/debug`
   - Check if older API versions (v58.0, v59.0) work better

**Expected Debug Results:**
```json
{
  "api_tests": {
    "v64.0": {
      "tests": {
        "user_query": {"status": "error", "error": "NOT_FOUND"},
        "version_endpoint": {"status": "error", "status_code": 404}
      }
    },
    "v58.0": {
      "tests": {
        "user_query": {"status": "success", "record_count": 1},
        "version_endpoint": {"status": "success", "status_code": 200}
      }
    }
  }
}
```

### Issue: Token or Authentication Problems

**Symptoms:**
- `/services/data` endpoint returns 401 or 403
- Token refresh fails

**What to Check:**
- Client ID/Secret configuration
- Refresh token validity
- Sandbox vs Production URL mismatch

### Issue: Instance URL Problems

**Symptoms:**
- Token refresh succeeds but queries fail
- `instance_url_match: false` in debug results

**What to Check:**
- Compare stored instance URL with token response
- Check if org has been migrated to different instance

## Troubleshooting Your Current Issue

Based on your error pattern, here's the recommended approach:

### 1. First - Test API Version Availability
```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/test-api-versions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-actual-api-key"
```

**What to look for:**
- Does `/services/data` return 200?
- Is v64.0 in the available versions list?
- Do older versions (v58.0, v59.0) show `"success": true`?

### 2. Second - Comprehensive Debug
```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/debug \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-actual-api-key"
```

**What to look for:**
- Which API versions allow successful queries?
- Are there instance URL mismatches?
- Do direct REST API calls work when simple-salesforce queries fail?

### 3. Check Debug Logs
```bash
# Check detailed health check logs
tail -f logs/health_checks.log

# Check Salesforce service logs  
tail -f logs/debug.log
```

## Expected Solutions

**Most Likely Solution**: API version downgrade
- If v64.0 isn't available, the system should automatically use an available version
- You may need to set `preferred_api_version` to a working version like v58.0 or v59.0

**Instance URL Fix**: Update stored instance URL
- If token refresh returns a different instance URL, update the database

**Configuration Fix**: Verify environment settings
- Check if sandbox/production settings match the actual org type

## Quick Fix Commands

Once you identify the issue, here are common fixes:

```python
# If API version needs to be changed
UPDATE salesforce_connections SET preferred_api_version = 'v58.0' WHERE id = 1;

# If instance URL needs to be updated  
UPDATE salesforce_connections SET instance_url = 'https://new-instance-url.salesforce.com' WHERE id = 1;
```

Run the API version test first - that will quickly tell us if this is a version compatibility issue (most likely) or a deeper authentication problem. 