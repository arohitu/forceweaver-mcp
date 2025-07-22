# Health Check Debugging Guide

This guide explains how to troubleshoot health check issues using the enhanced debugging capabilities.

## Overview

The health check system has been enhanced with comprehensive debugging to help identify issues with Salesforce API calls that result in "NOT_FOUND" errors.

## Debugging Features Added

### 1. Enhanced Logging
- **Location**: `logs/health_checks.log` - Detailed health check debugging
- **Location**: `logs/debug.log` - General application debugging  
- **Location**: `logs/error.log` - Error logs

### 2. Debug Endpoint
**Endpoint**: `POST /api/mcp/debug`
**Purpose**: Test basic Salesforce connectivity and object availability

### 3. Object Availability Check
The health check now includes an object availability check that tests access to:
- Standard objects (User, Organization)
- Metadata objects (EntityDefinition)  
- Revenue Cloud objects (Product2, AttributeDefinition, etc.)

## How to Debug Health Check Issues

### Step 1: Use the Debug Endpoint

```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/debug \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

This will test basic queries and return detailed information about:
- Salesforce client configuration
- API version being used
- Basic object accessibility
- Specific error messages for failed queries

### Step 2: Run Health Check with Enhanced Debugging

```bash
curl -X POST https://staging-api.forceweaver.com/api/mcp/health-check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key"
```

The health check now includes:
- **Object Availability Check**: Tests which objects are accessible
- **Conditional Checks**: Skips checks for unavailable objects with informational messages
- **Detailed Error Information**: Includes debug info in check results

### Step 3: Review Debug Logs

Check the log files for detailed debugging information:

```bash
# Health check specific logs
tail -f logs/health_checks.log

# General debug logs  
tail -f logs/debug.log

# Error logs
tail -f logs/error.log
```

## Common Issues and Solutions

### Issue: All Health Checks Fail with "NOT_FOUND" Errors

**Likely Cause**: Revenue Cloud objects are not available in the org

**What to Check**:
1. Use the debug endpoint to test basic connectivity
2. Look for "Object Availability Check" results in health check response
3. Check if Revenue Cloud is enabled in the Salesforce org

**Solution**: 
- If standard objects (User, Organization) work but Revenue Cloud objects don't, the org may not have Revenue Cloud enabled
- Contact Salesforce admin to enable Revenue Cloud features
- The health check will now show informational messages for unavailable features instead of errors

### Issue: Basic Connectivity Fails

**Likely Cause**: Authentication or API access issues

**What to Check**:
1. API version compatibility
2. Refresh token validity
3. Instance URL correctness
4. Client ID/Secret configuration

**Debug Information Available**:
- Salesforce client configuration details
- Token refresh process results
- API version information
- Instance URL validation

### Issue: Metadata Objects Not Accessible

**Likely Cause**: Permission issues with metadata API

**What to Check**:
1. EntityDefinition object accessibility
2. User permissions for metadata access

**Solution**:
- The health check will skip metadata-dependent checks (like OWD sharing settings) if EntityDefinition is not accessible
- This is now treated as informational rather than an error

## Debug Output Examples

### Successful Debug Response
```json
{
    "success": true,
    "debug_results": {
        "user_query": {"status": "success", "record_count": 1},
        "org_query": {"status": "success", "record_count": 1},
        "product_query": {"status": "error", "error": "NOT_FOUND"},
        "entity_definition_query": {"status": "success", "record_count": 1}
    }
}
```

### Health Check with Object Availability
```json
{
    "health_check_results": {
        "checks": {
            "object_availability_check": {
                "status": "warning",
                "message": "Standard objects available but no Revenue Cloud objects found",
                "details": {
                    "details": [
                        "✅ Available Objects:",
                        "   • Organization", 
                        "   • User",
                        "❌ Unavailable Objects:",
                        "   • Product2: NOT_FOUND",
                        "📦 Revenue Cloud Analysis:",
                        "   Available RC objects: 0/6"
                    ]
                }
            }
        }
    }
}
```

## Log File Examples

### Health Check Log Entry
```
2025-01-22 10:30:15,123 [INFO] app.services.health_checker_service:45: === Testing Basic Connectivity ===
2025-01-22 10:30:15,125 [INFO] app.services.health_checker_service:67: === Basic Connectivity Test Query Debug ===
2025-01-22 10:30:15,126 [INFO] app.services.health_checker_service:68: Description: Testing if we can query anything at all
2025-01-22 10:30:15,127 [INFO] app.services.health_checker_service:69: Query: SELECT Id FROM User LIMIT 1
2025-01-22 10:30:15,332 [INFO] app.services.health_checker_service:78: Query executed successfully in 0.20s
2025-01-22 10:30:15,333 [INFO] app.services.health_checker_service:79: Total records returned: 1
```

## Next Steps

1. **First Time Setup**: Start with the debug endpoint to verify basic connectivity
2. **Revenue Cloud Issues**: If RC objects aren't available, check with Salesforce admin about licensing
3. **Permission Issues**: If metadata objects aren't accessible, review user permissions
4. **Ongoing Monitoring**: Use the enhanced health check for regular monitoring with detailed object availability information

The enhanced debugging provides much more visibility into what's happening during health checks, making it easier to identify and resolve configuration issues. 