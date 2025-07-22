# ForceWeaver MCP Server - User Guide

Welcome to ForceWeaver MCP Server! This guide will help you get started with AI-powered Salesforce Revenue Cloud health checking.

## 🚀 Quick Start

### Step 1: Create Your Account

1. Visit [mcp.forceweaver.com](https://mcp.forceweaver.com)
2. Click "Sign Up" and create your account
3. Log in to access your dashboard

### Step 2: Generate API Key

1. Go to **Dashboard → API Keys**
2. Click **"Create New API Key"**
3. Enter a descriptive name (e.g., "VS Code MCP", "Claude Desktop")
4. Copy and save your API key securely - it's only shown once!

### Step 3: Connect Salesforce Org

1. Go to **Dashboard → Salesforce Organizations**
2. Click **"Connect New Salesforce Org"**
3. Fill in your org details:
   - **Org Identifier**: A unique name (e.g., "production", "sandbox")
   - **Instance URL**: Your Salesforce domain (e.g., `https://mycompany.my.salesforce.com`)
   - **Client ID & Secret**: From your Salesforce Connected App

### Step 4: Configure AI Agent

Choose your preferred AI agent:

#### VS Code GitHub Copilot

Add to your `.vscode/settings.json`:

```json
{
  "github.copilot.chat.mcpServers": {
    "forceweaver": {
      "command": "python",
      "args": ["mcp_server/enhanced_server.py"],
      "env": {
        "FORCEWEAVER_API_KEY": "fk_your_api_key_here",
        "SALESFORCE_ORG_ID": "production"
      }
    }
  }
}
```

#### Claude Desktop

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "forceweaver": {
      "command": "python",
      "args": ["mcp_server/enhanced_server.py"],
      "env": {
        "FORCEWEAVER_API_KEY": "fk_your_api_key_here",
        "SALESFORCE_ORG_ID": "production"
      }
    }
  }
}
```

### Step 5: Start Analyzing!

Ask your AI agent questions like:
- "Check the health of my Salesforce org"
- "Analyze the sharing model configuration"
- "Run a comprehensive Revenue Cloud health check"
- "Check for data integrity issues in my Salesforce setup"

## 🔧 Salesforce Connected App Setup

To connect your Salesforce org, you need to create a Connected App:

### 1. Create Connected App

1. Go to Salesforce **Setup → Apps → App Manager**
2. Click **"New Connected App"**
3. Fill in basic information:
   - **Connected App Name**: ForceWeaver MCP
   - **API Name**: ForceWeaver_MCP
   - **Contact Email**: Your email

### 2. Configure OAuth Settings

1. Enable **"Enable OAuth Settings"**
2. Set **Callback URL**: `https://mcp.forceweaver.com/callback`
3. Select OAuth Scopes:
   - "Perform requests on your behalf at any time (refresh_token, offline_access)"
   - "Access and manage your data (api)"
4. Enable **"Client Credentials Flow"**

### 3. Get Credentials

1. Save the Connected App
2. Wait 2-10 minutes for changes to take effect
3. Go to **Manage Connected Apps** → Your App
4. Copy the **Consumer Key** (Client ID)
5. Click **"Click to reveal"** to get the **Consumer Secret** (Client Secret)

### 4. Security Settings (Optional)

For production environments:
1. Edit the Connected App
2. Set **Permitted Users**: "Admin approved users are pre-authorized"
3. Create Permission Sets and assign to users

## 🛠️ Available Health Checks

### Basic Checks (Free)

| Check Type | Description | Cost |
|------------|-------------|------|
| `basic_org_info` | Organization details, user count, trial status | $0.01 |
| `sharing_model` | Organization-wide defaults and sharing rules | $0.01 |
| `bundle_analysis` | Product bundles, pricebooks, quotes, orders | $0.01 |
| `data_integrity` | Duplicate records, missing fields, orphaned data | $0.01 |

### Premium Checks

| Check Type | Description | Cost |
|------------|-------------|------|
| `performance_metrics` | API usage patterns, response times | $0.05 |
| `security_audit` | User permissions, field-level security | $0.05 |

### Example Tool Usage

```python
# Basic health check
{
  "forceweaver_api_key": "fk_your_api_key",
  "salesforce_org_id": "production",
  "check_types": ["basic_org_info", "sharing_model"]
}

# Comprehensive analysis  
{
  "forceweaver_api_key": "fk_your_api_key",
  "salesforce_org_id": "production",
  "check_types": [
    "basic_org_info",
    "sharing_model", 
    "bundle_analysis",
    "data_integrity"
  ]
}
```

## 📊 Managing Usage & Billing

### View Usage Statistics

1. Go to **Dashboard → Usage & Billing**
2. See current month summary:
   - Total API calls
   - Success rate
   - Current charges
3. Review detailed activity logs

### Billing Model

- **Pay-per-use**: Only pay for API calls you make
- **No monthly fees**: No subscription required
- **Transparent pricing**: See cost per call type
- **Monthly billing**: Invoiced at month end

### Optimization Tips

- Use specific check types instead of all checks
- Monitor failed calls and fix Salesforce configuration
- Use basic checks for regular monitoring
- Premium checks for deep analysis

## 🔒 Security & Privacy

### Data Protection

- **No permanent storage**: Salesforce data is only accessed temporarily for analysis
- **Encrypted credentials**: Client secrets encrypted with industry-standard encryption
- **Secure transmission**: All communications over HTTPS
- **Access logging**: All API calls logged for security and billing

### API Key Security

- **One-time display**: API keys shown only once during creation
- **Hashed storage**: Keys stored as bcrypt hashes
- **Easy revocation**: Deactivate keys immediately from dashboard
- **Usage tracking**: Monitor key usage for suspicious activity

### Salesforce Permissions

ForceWeaver requires minimal Salesforce permissions:
- **Read access** to standard objects (Account, Contact, Opportunity, etc.)
- **API access** for queries and metadata
- **No data modification** - read-only operations only

## 🚀 Advanced Usage

### Multiple Salesforce Orgs

Connect multiple orgs for different environments:

```json
{
  "github.copilot.chat.mcpServers": {
    "forceweaver-prod": {
      "command": "python",
      "args": ["mcp_server/enhanced_server.py"],
      "env": {
        "FORCEWEAVER_API_KEY": "fk_your_api_key",
        "SALESFORCE_ORG_ID": "production"
      }
    },
    "forceweaver-sandbox": {
      "command": "python", 
      "args": ["mcp_server/enhanced_server.py"],
      "env": {
        "FORCEWEAVER_API_KEY": "fk_your_api_key",
        "SALESFORCE_ORG_ID": "sandbox"
      }
    }
  }
}
```

### Custom Check Scripts

Create AI agent workflows:

```
1. "Check health of production org"
2. "Compare sharing model between prod and sandbox"
3. "Generate monthly health report"
4. "Alert me about data integrity issues"
```

### API Integration

For programmatic access, use the internal validation API (advanced users):

```bash
curl -X POST https://mcp.forceweaver.com/api/v1.0/internal/validate \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "fk_your_api_key",
    "org_id": "production"
  }'
```

## 🔧 Troubleshooting

### Common Issues

#### "Invalid API key" Error

- Check API key is copied correctly (starts with `fk_`)
- Verify key is active in Dashboard → API Keys
- Ensure no extra spaces or characters

#### "Salesforce org not found" Error

- Verify org identifier matches exactly
- Check org is active in Dashboard → Salesforce Organizations
- Confirm Connected App is configured correctly

#### "Authentication failed" Error

- Verify Client ID and Client Secret are correct
- Check Connected App is enabled and approved
- Wait 10 minutes after Connected App changes
- Ensure correct callback URL is set

#### Slow Response Times

- Check Salesforce org performance
- Reduce number of check types
- Verify network connectivity
- Contact support if issues persist

### Getting Help

1. **Dashboard**: Check activity logs for error details
2. **Documentation**: Review setup guides
3. **Support**: Contact support through dashboard
4. **Community**: GitHub Discussions (coming soon)

## 📈 Best Practices

### Regular Monitoring

- Set up weekly health check routines
- Monitor success rates in Usage dashboard
- Review and fix failing API calls promptly
- Keep Connected App credentials current

### Cost Optimization

- Start with basic checks for regular monitoring
- Use premium checks for quarterly deep analysis
- Monitor usage patterns and optimize check frequency
- Deactivate unused API keys

### Security Hygiene

- Rotate API keys quarterly
- Use unique org identifiers
- Keep Connected App secrets secure
- Monitor usage logs for anomalies
- Remove access for departed team members

## 🆕 What's Next?

ForceWeaver MCP is continuously evolving:

- **More check types**: Additional Revenue Cloud analysis
- **Custom rules**: Define your own health check criteria
- **Reporting**: Automated reports and dashboards
- **Integrations**: Slack notifications, email alerts
- **Enterprise features**: Team management, SSO

Stay updated by following our [releases](https://github.com/forceweaver/mcp-server/releases)!

---

## 📞 Support

- **Dashboard**: Built-in support tickets
- **Email**: support@forceweaver.com
- **Documentation**: [docs.forceweaver.com](https://docs.forceweaver.com)
- **Status**: [status.forceweaver.com](https://status.forceweaver.com)

Happy health checking! 🏥⚡ 