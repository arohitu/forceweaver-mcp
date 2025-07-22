# ForceWeaver MCP Server

A **Model Context Protocol (MCP) compliant server** that provides AI agents with comprehensive Salesforce Revenue Cloud health checking capabilities. This server follows the official MCP v2025-03-26 specification for maximum compatibility with MCP clients like Claude Desktop, Continue.dev, and other AI development tools.

## 🎯 What is MCP?

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) is an open standard that enables AI applications to securely access external data sources and tools. Our MCP server exposes Salesforce Revenue Cloud analysis capabilities through standardized JSON-RPC 2.0 messaging over STDIO transport.

## 🛠️ Available Tools

### `revenue_cloud_health_check`

Performs comprehensive analysis of Salesforce Revenue Cloud configurations, including:

- **Basic Organization Info**: Validates org settings and basic connectivity
- **Sharing Model Analysis**: Checks Organization-Wide Default (OWD) sharing settings
- **Bundle Configuration**: Analyzes product bundles and pricing configurations
- **Attribute Integrity**: Validates picklist fields and data integrity

**Parameters:**
- `check_types` (optional): Array of specific check types to run
  - `basic_org_info`: Organization details and connectivity
  - `sharing_model`: Sharing rules and OWD settings
  - `bundle_analysis`: Product bundle configuration
  - `attribute_integrity`: Picklist validation and data integrity
- `api_version` (optional): Salesforce API version to use (e.g., "v64.0")

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **Salesforce Connected App** configured for OAuth
3. **Valid Salesforce credentials** (access token, refresh token, org details)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/forceweaver-mcp.git
cd forceweaver-mcp

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp env.template .env
# Edit .env with your Salesforce credentials
```

### Configuration

Set the following environment variables in your `.env` file:

```bash
# Required: Salesforce Connection Details
SALESFORCE_INSTANCE_URL=https://your-org.my.salesforce.com
SALESFORCE_ACCESS_TOKEN=your_salesforce_access_token
SALESFORCE_REFRESH_TOKEN=your_salesforce_refresh_token
SALESFORCE_ORG_ID=00D000000000000

# Required: Salesforce OAuth Application
SALESFORCE_CLIENT_ID=your_connected_app_client_id
SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret

# Optional: API Version and Logging
SALESFORCE_API_VERSION=v64.0
LOG_LEVEL=INFO
```

### Running the MCP Server

```bash
# Start the MCP server
python server.py
```

The server will start and listen on STDIN/STDOUT for JSON-RPC 2.0 messages according to the MCP specification.

## 🔧 MCP Client Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "forceweaver": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/forceweaver-mcp"
    }
  }
}
```

### Continue.dev

Add to your `config.json`:

```json
{
  "mcpServers": [
    {
      "name": "forceweaver",
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/forceweaver-mcp"
    }
  ]
}
```

## 📡 MCP Protocol Details

This server implements the following MCP capabilities:

### Server Features
- ✅ **Tools**: Exposes `revenue_cloud_health_check` tool
- ✅ **Tool Calling**: Full JSON-RPC 2.0 tool execution
- ✅ **Error Handling**: Structured error responses
- ✅ **Logging**: Proper stderr logging (stdout reserved for protocol)

### Protocol Methods
- `initialize`: Server initialization and capability negotiation
- `tools/list`: Lists available tools with schemas
- `tools/call`: Executes tool with parameters
- `ping`: Health check and connectivity test

## 🧪 Testing

### Manual Testing

```bash
# Test basic connectivity
echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | python server.py

# List available tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | python server.py

# Call health check tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"revenue_cloud_health_check","arguments":{"check_types":["basic_org_info"]}}}' | python server.py
```

### With MCP Client

```bash
# Using the MCP CLI tool (if available)
mcp call forceweaver revenue_cloud_health_check '{"check_types": ["basic_org_info", "sharing_model"]}'
```

## 🏗️ Architecture

```
┌─────────────────┐    JSON-RPC 2.0     ┌──────────────────┐
│   MCP Client    │ ◄──── STDIO ────► │  MCP Server      │
│  (Claude, etc.) │                    │  (ForceWeaver)   │
└─────────────────┘                    └──────────────────┘
                                               │
                                               │ simple-salesforce
                                               ▼
                                       ┌──────────────────┐
                                       │  Salesforce API  │
                                       │   (REST/SOQL)    │
                                       └──────────────────┘
```

### Components

- **`server.py`**: Main MCP server implementation using FastMCP
- **`services/salesforce_service.py`**: Salesforce API client wrapper
- **`services/health_checker_service.py`**: Revenue Cloud analysis logic
- **STDIO Transport**: JSON-RPC 2.0 messages over standard input/output

## 🛡️ Security Considerations

- **Environment-based Authentication**: No API keys stored in code
- **Token Management**: Secure handling of Salesforce OAuth tokens
- **Logging**: Sensitive data logged only to stderr, never stdout
- **Input Validation**: All tool parameters validated against JSON schemas

## 🚢 Deployment

### Heroku

```bash
# Deploy to Heroku
heroku create your-app-name
heroku config:set SALESFORCE_INSTANCE_URL=https://your-org.salesforce.com
heroku config:set SALESFORCE_ACCESS_TOKEN=your_token
# ... set other environment variables
git push heroku main
```

### Docker

```bash
# Build image
docker build -t forceweaver-mcp .

# Run with environment file
docker run --env-file .env forceweaver-mcp
```

### Local Development

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python server.py
```

## 📚 MCP Resources

- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io)
- [MCP Python SDK Documentation](https://modelcontextprotocol.io/python)
- [MCP Client Integration Guides](https://modelcontextprotocol.io/clients)
- [FastMCP Framework](https://github.com/modelcontextprotocol/python-sdk)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Ensure MCP compliance with `mcp validate`
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Built with ❤️ for the MCP ecosystem**