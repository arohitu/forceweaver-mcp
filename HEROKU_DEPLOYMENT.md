# Heroku Deployment Guide for ForceWeaver MCP Server

This guide covers deploying the ForceWeaver MCP Server to Heroku as a worker process.

## 🚀 Deployment Steps

### 1. Prepare Repository

Ensure your repository has the updated MCP server structure:

```
forceweaver-mcp/
├── server.py              # Main MCP server
├── services/              # Business logic
│   ├── salesforce_service.py
│   └── health_checker_service.py
├── requirements.txt       # MCP dependencies
├── Procfile              # Heroku process definition
├── runtime.txt           # Python version
└── env.template          # Environment template
```

### 2. Create Heroku App

```bash
# Create new Heroku app
heroku create your-mcp-server-name

# Or update existing app
heroku git:remote -a your-existing-app-name
```

### 3. Configure Environment Variables

Set the required Salesforce connection variables:

```bash
# Required Salesforce credentials
heroku config:set SALESFORCE_INSTANCE_URL=https://your-org.my.salesforce.com
heroku config:set SALESFORCE_ACCESS_TOKEN=your_salesforce_access_token
heroku config:set SALESFORCE_REFRESH_TOKEN=your_salesforce_refresh_token
heroku config:set SALESFORCE_ORG_ID=00D000000000000

# OAuth application credentials
heroku config:set SALESFORCE_CLIENT_ID=your_connected_app_client_id
heroku config:set SALESFORCE_CLIENT_SECRET=your_connected_app_client_secret

# Optional configuration
heroku config:set SALESFORCE_API_VERSION=v64.0
heroku config:set LOG_LEVEL=INFO
```

### 4. Deploy the Application

```bash
# Deploy to Heroku
git add .
git commit -m "Convert to MCP server"
git push heroku main
```

### 5. Scale Worker Process

Since this is an MCP server (not a web app), run it as a worker:

```bash
# Scale down web process (if exists)
heroku ps:scale web=0

# Scale up worker process
heroku ps:scale worker=1
```

## 📊 Monitoring

### Check Process Status

```bash
# View running processes
heroku ps

# View logs
heroku logs --tail

# View worker logs specifically
heroku logs --tail --dyno=worker
```

### Health Monitoring

The MCP server runs continuously and accepts JSON-RPC messages. To test it's working:

```bash
# Check if process is running
heroku ps:exec -d worker.1
# Then inside the dyno:
# echo '{"jsonrpc":"2.0","id":1,"method":"ping"}' | python server.py
```

## 🔧 Configuration Details

### Procfile

The `Procfile` specifies how to run the MCP server:

```
release: echo "No database migrations needed for MCP server"
worker: python server.py
```

### Resource Requirements

MCP servers typically need:
- **Dyno Type**: `Basic` or `Standard-1X` (depending on load)
- **Memory**: 512MB-1GB RAM
- **CPU**: Single core sufficient for most workloads

### Scaling Considerations

```bash
# For higher load, scale horizontally
heroku ps:scale worker=2

# Or scale to larger dyno type
heroku dyno:type worker=standard-2x
```

## 🐛 Troubleshooting

### Common Issues

#### Server Won't Start
```bash
# Check logs for startup errors
heroku logs --tail --dyno=worker

# Common causes:
# - Missing environment variables
# - Invalid Salesforce credentials
# - Python dependency issues
```

#### Environment Variable Issues
```bash
# List all config vars
heroku config

# Test Salesforce connection
heroku run python -c "
from services.salesforce_service import SalesforceAPIClient
import os
client = SalesforceAPIClient(
    os.getenv('SALESFORCE_INSTANCE_URL'),
    os.getenv('SALESFORCE_ACCESS_TOKEN')
)
print(client.get_org_info())
"
```

#### Memory/Performance Issues
```bash
# Monitor resource usage
heroku logs --tail | grep "Memory\|Error"

# Scale up if needed
heroku dyno:type worker=standard-2x
```

## 🔄 Updates and Maintenance

### Deploy Updates

```bash
# Deploy new version
git push heroku main

# Restart workers
heroku restart worker
```

### Token Refresh

If Salesforce tokens expire:

```bash
# Update access token
heroku config:set SALESFORCE_ACCESS_TOKEN=new_access_token

# Restart to pick up new config
heroku restart worker
```

### Health Checks

Set up monitoring to ensure the MCP server stays healthy:

```bash
# You can use Heroku Scheduler for periodic health checks
heroku addons:create scheduler:standard

# Then add a scheduled task to ping the server
```

## 💰 Cost Optimization

### For Development/Testing
```bash
# Use eco dynos (sleeps when inactive)
heroku dyno:type worker=eco
```

### For Production
```bash
# Use basic or standard dynos (no sleeping)
heroku dyno:type worker=basic
```

## 🛡️ Security Best Practices

1. **Environment Variables**: Never commit secrets to git
2. **Token Rotation**: Regularly refresh Salesforce tokens
3. **Access Control**: Limit Salesforce user permissions
4. **Monitoring**: Monitor logs for suspicious activity

## 📞 Support

### Useful Commands

```bash
# View all app info
heroku info

# Access dyno shell
heroku ps:exec -d worker.1

# View configuration
heroku config

# View process status
heroku ps

# Restart app
heroku restart

# Scale processes
heroku ps:scale worker=1
```

### Getting Help

If you encounter issues:

1. Check Heroku logs: `heroku logs --tail`
2. Verify environment variables: `heroku config`
3. Test Salesforce connectivity manually
4. Review MCP server logs for protocol errors

---

**Note**: This deployment creates an MCP server that communicates via STDIO. It's designed to be used by MCP clients, not accessed directly via HTTP. 