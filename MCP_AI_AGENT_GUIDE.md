# ForceWeaver MCP API - AI Agent Integration Guide

## Overview

ForceWeaver MCP API is a **Model Context Protocol (MCP) compliant server** that provides AI agents with powerful tools to analyze and health-check Salesforce Revenue Cloud configurations. This API enables AI agents to perform comprehensive diagnostics on Salesforce organizations through standardized MCP tool invocations.

## 🤖 What AI Agents Can Do

- **Health Check Salesforce Orgs**: Analyze organization settings, sharing models, and configuration integrity
- **Diagnose Revenue Cloud Issues**: Identify bundle configuration problems, attribute integrity issues, and sharing model conflicts
- **Generate Detailed Reports**: Get structured analysis with actionable recommendations
- **API Version Management**: Specify which Salesforce API version to use for compatibility

## 🔗 Getting Started

### 1. Authentication Setup
Before using the API, users must authenticate with Salesforce:

1. **Initial Setup**: Have the user visit: `https://api.forceweaver.com/api/auth/salesforce/initiate?email=user@example.com`
2. **OAuth Flow**: User completes Salesforce OAuth and receives an API key
3. **API Key Usage**: Include API key in all requests: `Authorization: Bearer API_KEY_HERE`

### 2. MCP Server Discovery

**Endpoint**: `GET https://api.forceweaver.com/`

The root endpoint identifies this as an MCP-compliant server:

```json
{
  "service": "ForceWeaver MCP API",
  "protocol": {
    "name": "Model Context Protocol",
    "version": "2025-03-26"
  },
  "capabilities": {
    "tools": true,
    "authentication": "Bearer token (API key)"
  }
}
```

## 🛠️ Available Tools

### 1. Tool Discovery

**Endpoint**: `GET https://api.forceweaver.com/api/mcp/tools`

```json
{
  "tools": [
    {
      "name": "revenue_cloud_health_check",
      "description": "Perform a comprehensive health check on Salesforce Revenue Cloud configuration. Analyzes org settings, sharing models, bundle configurations, and data integrity.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "check_types": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["basic_org_info", "sharing_model", "bundle_analysis", "attribute_integrity"]
            },
            "description": "Specific types of checks to perform"
          },
          "api_version": {
            "type": "string",
            "pattern": "^v\\d+\\.0$",
            "description": "Salesforce API version to use (e.g., 'v64.0')"
          }
        }
      }
    }
  ]
}
```

### 2. Tool Invocation

**Endpoint**: `POST https://api.forceweaver.com/api/mcp/health-check`

**Headers**:
```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

#### Option A: MCP Standard Format (Recommended for AI Agents)
```json
{
  "name": "revenue_cloud_health_check",
  "arguments": {
    "check_types": ["basic_org_info", "sharing_model"],
    "api_version": "v64.0"
  }
}
```

#### Option B: Direct Format (Simplified)
```json
{
  "check_types": ["basic_org_info", "sharing_model"],
  "api_version": "v64.0"
}
```

**Response Format** (MCP-compliant for both formats):
```json
{
  "content": [
    {
      "type": "text",
      "text": "✅ Revenue Cloud Health Check Completed\n\nExecuted 2 health checks on Salesforce org...\n\n• Basic Organization Info: PASSED\n• Sharing Model Check: WARNING - External sharing detected"
    }
  ],
  "isError": false,
  "_meta": {
    "customer_id": 34,
    "salesforce_org_id": "00D1234567890123",
    "api_version_used": "v64.0",
    "checks_requested": ["basic_org_info", "sharing_model"],
    "total_checks": 2
  }
}
```

## 📋 Tool Parameters Reference

### `revenue_cloud_health_check`

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `check_types` | array[string] | No | Specific checks to run | `["basic_org_info", "sharing_model"]` |
| `api_version` | string | No | Salesforce API version | `"v64.0"` |

#### Available Check Types:
- **`basic_org_info`**: Organization details, type, and basic configuration
- **`sharing_model`**: Organization-Wide Defaults (OWD) and sharing rules analysis  
- **`bundle_analysis`**: Product bundle configuration and Revenue Cloud setup
- **`attribute_integrity`**: Picklist value validation and attribute consistency

#### Supported API Versions:
- `v58.0` through `v64.0` (automatically detects available versions per org)
- If not specified, uses customer's preferred version or latest available

## 🤖 AI Agent Implementation Examples

### Example 1: MCP Standard Format (Recommended)

```python
import requests

def run_salesforce_health_check_mcp(api_key, org_type="full"):
    """Run a Salesforce health check using MCP format for AI agents."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Determine check scope
    if org_type == "basic":
        checks = ["basic_org_info"]
    elif org_type == "security":
        checks = ["basic_org_info", "sharing_model"] 
    else:  # full
        checks = []  # Run all checks
    
    payload = {
        "name": "revenue_cloud_health_check",
        "arguments": {}
    }
    
    if checks:
        payload["arguments"]["check_types"] = checks
    
    response = requests.post(
        "https://api.forceweaver.com/api/mcp/health-check",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        if not result.get("isError", True):
            return {
                "success": True,
                "report": result["content"][0]["text"],
                "metadata": result["_meta"]
            }
    
    return {"success": False, "error": response.text}
```

### Example 2: Direct Format (Simplified)

```python
def run_salesforce_health_check_direct(api_key, check_types=None, api_version=None):
    """Run health check with direct parameter format."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {}
    
    if check_types:
        payload["check_types"] = check_types
    if api_version:
        payload["api_version"] = api_version
    
    response = requests.post(
        "https://api.forceweaver.com/api/mcp/health-check",
        json=payload,
        headers=headers
    )
    
    return response.json() if response.status_code == 200 else {"error": response.text}
```

### Example 3: Error Handling

```python
def robust_health_check(api_key):
    """Health check with comprehensive error handling."""
    
    try:
        # First check service status
        status_response = requests.get(
            "https://api.forceweaver.com/api/mcp/status",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        if status_response.status_code != 200:
            return {"error": "Service unavailable"}
        
        status = status_response.json()
        if not status.get("salesforce_connected"):
            return {"error": "No Salesforce connection found. User needs to authenticate."}
        
        # Run the health check using MCP format
        result = run_salesforce_health_check_mcp(api_key)
        return result
        
    except requests.RequestException as e:
        return {"error": f"Network error: {str(e)}"}
```

## 🔄 Service Status Check

**Endpoint**: `GET https://api.forceweaver.com/api/mcp/status`

Use this to verify service availability before running health checks:

```json
{
  "service_status": "operational",
  "customer_id": 34,
  "salesforce_connected": true,
  "salesforce_org_id": "00D1234567890123",
  "effective_api_version": "v64.0",
  "available_api_versions": ["v64.0", "v63.0", "v62.0"]
}
```

## ⚠️ Error Handling

### Common Error Responses (MCP Format):

**Authentication Error (401)**:
```json
{
  "content": [{"type": "text", "text": "❌ API key is required"}],
  "isError": true,
  "error_type": "Unauthorized"
}
```

**Tool Not Found (404)**:
```json
{
  "content": [{"type": "text", "text": "❌ Unknown tool: invalid_tool_name. Only 'revenue_cloud_health_check' is supported."}],
  "isError": true,
  "error_type": "ToolNotFound"
}
```

**Invalid Arguments (400)**:
```json
{
  "content": [{"type": "text", "text": "❌ Invalid check types: invalid_type. Valid types: basic_org_info, sharing_model, bundle_analysis, attribute_integrity"}],
  "isError": true,
  "error_type": "InvalidArgument"
}
```

## 🚀 Production Endpoints

- **Production**: `https://api.forceweaver.com`
- **Staging**: `https://staging-api.forceweaver.com`

## 📖 Integration Workflow

1. **User Authentication**: Direct user to OAuth flow
2. **Service Discovery**: Check MCP capabilities at root endpoint
3. **Tool Discovery**: Get available tools via `/api/mcp/tools`
4. **Status Check**: Verify Salesforce connection via `/api/mcp/status`
5. **Tool Invocation**: Call health check via `/api/mcp/health-check`
6. **Result Processing**: Parse MCP-compliant content responses

## 🔐 Security Considerations

- API keys are customer-specific and tied to their Salesforce org
- All requests require proper Bearer token authentication
- Health check results may contain sensitive org configuration data
- Respect rate limits and implement proper retry logic

## 📞 Support

For API issues or questions:
- Check service status at the `/health` endpoint
- Review error response codes and types
- Ensure API key is valid and Salesforce connection is active

---

*This API follows the Model Context Protocol (MCP) v2025-03-26 specification for maximum compatibility with AI agents and MCP clients.* 