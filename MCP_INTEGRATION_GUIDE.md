# ForceWeaver MCP Server - Integration Guide

This guide helps you integrate the ForceWeaver MCP Server with various MCP clients and AI development tools.

## 🎯 Overview

ForceWeaver MCP Server is a **Model Context Protocol (MCP) v2025-03-26 compliant server** that provides AI agents with comprehensive Salesforce Revenue Cloud health checking capabilities through standardized JSON-RPC 2.0 messaging.

## 🔧 Client Configuration

### Claude Desktop

Claude Desktop is one of the most popular MCP clients. Here's how to configure it:

#### 1. Find Configuration File

**macOS/Linux:**
```bash
~/.config/claude/claude_desktop_config.json
```

**Windows:**
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

#### 2. Add ForceWeaver Server

```json
{
  "mcpServers": {
    "forceweaver": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/absolute/path/to/forceweaver-mcp",
      "env": {
        "SALESFORCE_INSTANCE_URL": "https://your-org.my.salesforce.com",
        "SALESFORCE_ACCESS_TOKEN": "your_access_token",
        "SALESFORCE_REFRESH_TOKEN": "your_refresh_token",
        "SALESFORCE_ORG_ID": "00D000000000000",
        "SALESFORCE_CLIENT_ID": "your_client_id",
        "SALESFORCE_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

#### 3. Restart Claude Desktop

After saving the configuration, restart Claude Desktop to load the server.

### Continue.dev

For Visual Studio Code with Continue extension:

#### 1. Open Continue Configuration

Press `Cmd/Ctrl + Shift + P` and select "Continue: Open Config"

#### 2. Add MCP Server

```json
{
  "mcpServers": [
    {
      "name": "forceweaver",
      "command": "python",
      "args": ["server.py"],
      "cwd": "/absolute/path/to/forceweaver-mcp",
      "env": {
        "SALESFORCE_INSTANCE_URL": "https://your-org.my.salesforce.com",
        "SALESFORCE_ACCESS_TOKEN": "your_access_token"
      }
    }
  ]
}
```

### Cursor IDE

For Cursor IDE with MCP support:

```json
{
  "mcp": {
    "servers": {
      "forceweaver": {
        "command": "python",
        "args": ["server.py"],
        "cwd": "/absolute/path/to/forceweaver-mcp"
      }
    }
  }
}
```

## 🌐 Environment Variables

### Required Variables

```bash
# Salesforce Connection
SALESFORCE_INSTANCE_URL=https://your-org.my.salesforce.com
SALESFORCE_ACCESS_TOKEN=your_salesforce_access_token
SALESFORCE_REFRESH_TOKEN=your_salesforce_refresh_token
SALESFORCE_ORG_ID=00D000000000000

# OAuth Application
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret
```

### Optional Variables

```bash
# API Configuration
SALESFORCE_API_VERSION=v64.0

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## 🔐 Authentication Setup

### 1. Create Salesforce Connected App

1. **Navigate to Salesforce Setup**
   - Go to Setup → App Manager
   - Click "New Connected App"

2. **Configure OAuth Settings**
   - Enable OAuth Settings: ✅ Yes
   - Callback URL: `http://localhost:8080/callback` (for local setup)
   - OAuth Scopes:
     - `api` (Access your basic information)
     - `refresh_token` (Perform requests on your behalf at any time)
     - `full` (Full access) - if needed

3. **Get Client Credentials**
   - Copy Consumer Key → `SALESFORCE_CLIENT_ID`
   - Copy Consumer Secret → `SALESFORCE_CLIENT_SECRET`

### 2. Obtain Access Tokens

#### Option A: OAuth Flow (Recommended)

```python
# Use this helper script to get tokens
import requests
from urllib.parse import urlparse, parse_qs

# Step 1: Get authorization code
auth_url = f"https://login.salesforce.com/services/oauth2/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
print(f"Visit: {auth_url}")

# Step 2: Exchange code for tokens
code = input("Enter authorization code from callback URL: ")
token_data = {
    'grant_type': 'authorization_code',
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'code': code
}

response = requests.post('https://login.salesforce.com/services/oauth2/token', data=token_data)
tokens = response.json()
print(f"Access Token: {tokens['access_token']}")
print(f"Refresh Token: {tokens['refresh_token']}")
print(f"Instance URL: {tokens['instance_url']}")
```

#### Option B: Username/Password Flow (Less Secure)

```python
import requests

token_data = {
    'grant_type': 'password',
    'client_id': client_id,
    'client_secret': client_secret,
    'username': 'your_username',
    'password': 'your_password_with_security_token'
}

response = requests.post('https://login.salesforce.com/services/oauth2/token', data=token_data)
tokens = response.json()
```

## 🧪 Testing Integration

### 1. Verify Server Startup

```bash
# Test server can start
python server.py
# Should start without errors and wait for input
```

### 2. Test with Manual JSON-RPC

```bash
# Test ping
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | python server.py

# Test tool listing
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python server.py

# Test tool execution
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"revenue_cloud_health_check","arguments":{}}}' | python server.py
```

### 3. Expected Responses

#### Ping Response
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {}
}
```

#### Tools List Response
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "revenue_cloud_health_check",
        "description": "Perform a comprehensive health check...",
        "inputSchema": {
          "type": "object",
          "properties": {
            "check_types": {
              "type": "array",
              "items": {"type": "string"}
            },
            "api_version": {
              "type": "string"
            }
          }
        }
      }
    ]
  }
}
```

## 💬 Usage Examples

### Basic Health Check

**AI Prompt:** "Run a basic Salesforce health check"

**Expected Tool Call:**
```json
{
  "name": "revenue_cloud_health_check",
  "arguments": {
    "check_types": ["basic_org_info"]
  }
}
```

### Comprehensive Analysis

**AI Prompt:** "Analyze our Salesforce Revenue Cloud configuration comprehensively"

**Expected Tool Call:**
```json
{
  "name": "revenue_cloud_health_check",
  "arguments": {}
}
```

### Specific Focus Areas

**AI Prompt:** "Check our sharing model and product bundle configuration"

**Expected Tool Call:**
```json
{
  "name": "revenue_cloud_health_check",
  "arguments": {
    "check_types": ["sharing_model", "bundle_analysis"]
  }
}
```

## 🚨 Troubleshooting

### Server Not Starting

```bash
# Check Python version
python --version  # Should be 3.11+

# Check dependencies
pip list | grep mcp

# Check environment variables
python -c "import os; print('Instance URL:', os.getenv('SALESFORCE_INSTANCE_URL'))"
```

### Authentication Errors

```bash
# Test Salesforce connection
python -c "
from services.salesforce_service import SalesforceAPIClient
client = SalesforceAPIClient('instance_url', 'access_token')
print(client.get_org_info())
"
```

### MCP Client Not Recognizing Server

1. **Check Configuration Path**: Ensure config file is in correct location
2. **Verify JSON Syntax**: Use JSON validator on config file
3. **Check File Paths**: Ensure `cwd` points to correct directory
4. **Restart Client**: Restart Claude Desktop or other MCP client

### Common Error Messages

#### "Missing required environment variables"
- Solution: Set all required Salesforce credentials in environment

#### "Failed to connect to Salesforce"
- Solution: Verify access token is valid and not expired
- Try refreshing token using refresh_token

#### "Server failed to start"
- Solution: Check Python version, dependencies, and file permissions

## 📊 Performance Tips

### 1. Token Management
- Implement token refresh logic for long-running sessions
- Cache tokens securely to avoid repeated OAuth flows

### 2. API Efficiency
- Use specific `check_types` to run only needed checks
- Consider API version compatibility for your org

### 3. Logging
- Use `LOG_LEVEL=ERROR` in production for better performance
- Monitor stderr output for debugging information

## 🔄 Maintenance

### Token Refresh

```python
# Automatic token refresh example
from services.salesforce_service import SalesforceConnectionManager

refresh_token = os.getenv('SALESFORCE_REFRESH_TOKEN')
client_id = os.getenv('SALESFORCE_CLIENT_ID')
client_secret = os.getenv('SALESFORCE_CLIENT_SECRET')

new_tokens = SalesforceConnectionManager.refresh_token_if_needed(
    refresh_token, client_id, client_secret
)

if new_tokens:
    # Update environment variables
    os.environ['SALESFORCE_ACCESS_TOKEN'] = new_tokens['access_token']
```

### Health Monitoring

```bash
# Check server health
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | timeout 10 python server.py
```

## 📚 Additional Resources

- [MCP Specification](https://spec.modelcontextprotocol.io)
- [Salesforce REST API Documentation](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/)
- [FastMCP Framework](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop MCP Guide](https://claude.ai/docs/mcp)

---

**Need Help?** Check our troubleshooting section or create an issue in the repository. 