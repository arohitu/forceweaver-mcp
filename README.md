# ForceWeaver MCP Server

**AI-Powered Salesforce Revenue Cloud Health Checking**

ForceWeaver is a comprehensive Salesforce health monitoring solution designed for AI agents. Built on the Model Context Protocol (MCP), it enables AI tools like Claude Desktop and VS Code GitHub Copilot to perform intelligent analysis of your Salesforce Revenue Cloud setup.

## 🚀 Quick Start

### 1. Sign Up & Get API Key

1. Visit **[mcp.forceweaver.com](https://mcp.forceweaver.com)**
2. Create your account
3. Generate an API key from the dashboard

### 2. Connect Salesforce Org

1. Create a Salesforce Connected App
2. Add your org credentials in the dashboard
3. Configure OAuth settings

### 3. Configure AI Agent

**VS Code GitHub Copilot:**

```json
{
  "github.copilot.chat.mcpServers": {
    "forceweaver": {
      "command": "python",
      "args": ["mcp_server/enhanced_server.py"],
      "env": {
        "FORCEWEAVER_API_KEY": "fk_your_api_key",
        "SALESFORCE_ORG_ID": "production"
      }
    }
  }
}
```

### 4. Start Analyzing!

Ask your AI agent:
- "Check the health of my Salesforce org"
- "Analyze the sharing model configuration" 
- "Run a comprehensive Revenue Cloud health check"

## 🏗️ Architecture

ForceWeaver uses a hybrid architecture combining a Flask web application with an enhanced MCP server:

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   AI Agent          │    │   MCP Server        │    │   Web Application   │
│   (VS Code/Claude)  │◄──►│   Enhanced Server   │◄──►│   mcp.forceweaver.  │
│                     │    │   - Tool execution  │    │   com               │
│                     │    │   - Validation      │    │   - User management │
└─────────────────────┘    │   - Rate limiting   │    │   - API key mgmt    │
                           └─────────────────────┘    │   - Billing         │
                                      │               └─────────────────────┘
                                      ▼                          │
                           ┌─────────────────────┐              │
                           │   Salesforce Org    │◄─────────────┘
                           │   - Health checks   │
                           │   - Revenue Cloud   │
                           └─────────────────────┘
```

## 🔧 Available Health Checks

### Basic Checks ($0.01 each)

| Check | Description |
|-------|-------------|
| `basic_org_info` | Organization details, users, trial status |
| `sharing_model` | OWDs, sharing rules, access levels |
| `bundle_analysis` | Products, pricebooks, quotes, orders |
| `data_integrity` | Duplicates, missing fields, orphaned records |

### Premium Checks ($0.05 each)

| Check | Description |
|-------|-------------|
| `performance_metrics` | API usage, response times, performance |
| `security_audit` | User permissions, field-level security |

## 🛠️ Development Setup

### Prerequisites

- Python 3.8+
- PostgreSQL
- Heroku CLI (for deployment)

### Local Development

```bash
# Clone repository
git clone https://github.com/forceweaver/mcp-server.git
cd mcp-server

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp env.template .env
# Edit .env with your configuration

# Initialize database
python seed_db.py

# Run Flask web app
python app.py

# Run MCP server (separate terminal)
python mcp_server/enhanced_server.py
```

### Environment Variables

```bash
# Flask Web App
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-encryption-key
DATABASE_URL=postgresql://user:pass@localhost/forceweaver_mcp

# MCP Server  
VALIDATION_URL=http://localhost:5000

# Admin User
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password
```

## 🚀 Deployment

### Heroku Deployment

```bash
# Create Heroku app
heroku create forceweaver-mcp

# Add PostgreSQL
heroku addons:create heroku-postgresql:mini

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set ENCRYPTION_KEY=your-encryption-key
heroku config:set ADMIN_EMAIL=your-email
heroku config:set ADMIN_PASSWORD=secure-password

# Deploy
git push heroku main

# Seed database
heroku run python seed_db.py
```

### Domain Setup

1. Configure custom domain in Heroku
2. Update DNS records to point to Heroku
3. Add SSL certificate

## 📁 Project Structure

```
forceweaver-mcp/
├── app/                          # Flask web application
│   ├── __init__.py              # App factory
│   ├── models/                  # Database models
│   │   ├── user.py             # User authentication
│   │   ├── api_key.py          # API key management
│   │   ├── salesforce_org.py   # Salesforce org config
│   │   ├── usage_log.py        # Usage tracking
│   │   └── rate_configuration.py
│   ├── web/                    # HTML routes
│   │   ├── main_routes.py      # Landing pages
│   │   ├── auth_routes.py      # Authentication
│   │   └── dashboard_routes.py # User dashboard
│   └── api/v1/                 # API endpoints
│       └── internal_api.py     # MCP server integration
├── mcp_server/                  # Enhanced MCP server
│   ├── enhanced_server.py      # Main MCP server
│   ├── validation_client.py    # Web app integration
│   ├── salesforce_client.py    # Salesforce API client
│   └── health_checker.py       # Health check logic
├── templates/                   # HTML templates
├── app.py                      # Flask entry point
├── seed_db.py                  # Database initialization
└── requirements.txt            # Dependencies
```

## 🔐 Security Features

### Data Protection
- **Encrypted credentials**: Salesforce secrets encrypted at rest
- **Secure API keys**: Bcrypt hashed with secure generation
- **No data persistence**: Salesforce data accessed temporarily only
- **HTTPS everywhere**: All communications encrypted

### Access Control
- **User authentication**: Email-based registration/login
- **API key management**: Easy generation and revocation
- **Usage tracking**: Complete audit trail
- **Rate limiting**: Configurable per-user limits

## 📊 Monitoring & Analytics

### Usage Dashboard
- Real-time API call monitoring
- Success rate tracking
- Cost analysis and optimization
- Detailed activity logs

### Billing
- Pay-per-use model
- Transparent pricing
- Monthly invoicing
- Cost optimization tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints
- Include docstrings
- Write tests for new features
- Update documentation

## 📚 Documentation

- **[User Guide](USER_GUIDE.md)** - Complete setup and usage guide
- **[API Reference](docs/api.md)** - Internal API documentation
- **[MCP Integration](docs/mcp.md)** - MCP client setup
- **[Deployment Guide](docs/deployment.md)** - Production deployment

## 🆘 Support

- **Dashboard**: Built-in support tickets
- **Email**: support@forceweaver.com
- **Documentation**: [docs.forceweaver.com](https://docs.forceweaver.com)
- **GitHub Issues**: Bug reports and feature requests

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io)
- Powered by [FastMCP](https://github.com/jlowin/fastmcp)
- Inspired by the Salesforce developer community

---

**Ready to supercharge your Salesforce monitoring with AI?** 

[Get Started →](https://mcp.forceweaver.com) | [View Documentation →](USER_GUIDE.md)