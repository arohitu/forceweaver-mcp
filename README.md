# ForceWeaver MCP API

A standalone, monetized API service that exposes the RevenueCloudHealthChecker tool to AI agents via secure, MCP-compliant endpoints. This service provides comprehensive health checks for Salesforce Revenue Cloud configurations through a dual-authentication system.

## Features

- **Dual Authentication System**: API keys for customers + one-time Salesforce OAuth 2.0 flow
- **MCP Compliance**: Follows Model Context Protocol standards for AI agent integration
- **Comprehensive Health Checks**: Analyzes 10+ aspects of Revenue Cloud configuration
- **Secure Token Management**: Encrypted storage of Salesforce refresh tokens
- **Production Ready**: Docker support, proper logging, error handling
- **Scalable Architecture**: Built for cloud deployment (Heroku, DigitalOcean, GCP, AWS)

## Quick Start

### 1. Environment Setup

Copy the environment configuration:

```bash
# Copy environment template
cp .env.example .env

# Edit with your values
vim .env
```

Required environment variables:
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://username:password@localhost/forceweaver_mcp
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_REDIRECT_URI=https://your-domain.com/api/auth/salesforce/callback
ENCRYPTION_KEY=your-fernet-encryption-key-here
```

### 2. Database Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py
```

### 3. Run the Application

**Development:**
```bash
python run.py
```

**Production (Docker):**
```bash
docker build -t forceweaver-mcp .
docker run -p 8080:8080 --env-file .env forceweaver-mcp
```

## API Endpoints

### Authentication Flow

#### 1. Initiate Salesforce OAuth
```
GET /api/auth/salesforce/initiate?email=<customer-email>
```

Redirects to Salesforce authorization page.

#### 2. OAuth Callback (Automatic)
```
GET /api/auth/salesforce/callback
```

Handles Salesforce OAuth callback and returns:
```json
{
  "message": "Salesforce connection established successfully",
  "customer_id": 123,
  "salesforce_org_id": "00D...",
  "instance_url": "https://yourorg.salesforce.com",
  "api_key": "your-api-key-here",
  "note": "Please save this API key securely. It will not be shown again."
}
```

#### 3. Check Connection Status
```
GET /api/auth/customer/status?email=<customer-email>
```

Returns connection status for a customer.

### MCP Endpoints

All MCP endpoints require `Authorization: Bearer <api_key>` header.

#### Health Check
```
POST /api/mcp/health-check
```

Performs comprehensive Revenue Cloud health check:
```json
{
  "success": true,
  "customer_id": 123,
  "salesforce_org_id": "00D...",
  "health_check_results": {
    "timestamp": "2024-01-20T10:30:00Z",
    "checks": {
      "billing_rules": { "status": "ok", "message": "Found 5 active billing rules" },
      "cpq_configuration": { "status": "warning", "message": "Legacy CPQ settings detected" },
      "price_books": { "status": "ok", "message": "Found 3 active price books" },
      "product_catalog": { "status": "ok", "message": "Found 127 active products" },
      "quote_templates": { "status": "ok", "message": "Found 2 quote templates" },
      "approval_processes": { "status": "ok", "message": "Approval processes check completed" },
      "revenue_schedules": { "status": "ok", "message": "Found 45 revenue schedules" },
      "contracts": { "status": "ok", "message": "Found 23 active contracts" },
      "subscriptions": { "status": "ok", "message": "Found 89 subscriptions" },
      "billing_setup": { "status": "ok", "message": "Found 1 active billing configuration" }
    },
    "overall_health": {
      "score": 85.5,
      "grade": "B",
      "summary": {
        "total_checks": 10,
        "ok": 8,
        "warnings": 1,
        "errors": 1
      }
    }
  }
}
```

#### Get Available Tools (MCP)
```
GET /api/mcp/tools
```

Returns MCP-compliant tool definitions:
```json
{
  "tools": [
    {
      "name": "revenue_cloud_health_check",
      "description": "Perform a comprehensive health check on Salesforce Revenue Cloud configuration",
      "inputSchema": {
        "type": "object",
        "properties": {
          "check_types": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific types of checks to perform (optional, defaults to all)"
          }
        }
      }
    }
  ],
  "capabilities": {
    "tools": {
      "listChanged": false
    }
  }
}
```

#### Service Status
```
GET /api/mcp/status
```

Returns service status for the authenticated customer.

## Health Check Categories

The API performs comprehensive checks across 10 categories:

1. **Billing Rules** - Active billing rules and expiration dates
2. **CPQ Configuration** - Required settings and legacy configuration detection
3. **Price Books** - Active price books and standard price book validation
4. **Product Catalog** - Active products and product family assignments
5. **Quote Templates** - Template configuration and default template validation
6. **Approval Processes** - Approval process configuration (requires Metadata API)
7. **Revenue Schedules** - Revenue schedule analysis
8. **Contracts** - Contract status and configuration
9. **Subscriptions** - Subscription configuration (CPQ-dependent)
10. **Billing Setup** - Billing configuration and active settings

## Security Features

- **Encrypted Token Storage**: Salesforce refresh tokens are encrypted using Fernet encryption
- **Hashed API Keys**: Customer API keys are hashed before storage
- **OAuth 2.0 Flow**: Secure one-time authorization without handling customer credentials
- **Request Logging**: Comprehensive logging for audit trails
- **Error Handling**: Secure error responses that don't leak sensitive information

## Deployment Options

### Heroku
```bash
# Create Heroku app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set SALESFORCE_CLIENT_ID=your-client-id
# ... etc

# Deploy
git push heroku main
```

### DigitalOcean App Platform
```yaml
# app.yaml
name: forceweaver-mcp
services:
- name: api
  source_dir: /
  github:
    repo: your-username/forceweaver-mcp
    branch: main
  run_command: gunicorn -b 0.0.0.0:8080 app:create_app()
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
databases:
- name: db
  engine: PG
  version: "13"
```

### Google Cloud Run
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/your-project/forceweaver-mcp

# Deploy to Cloud Run
gcloud run deploy forceweaver-mcp \
  --image gcr.io/your-project/forceweaver-mcp \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your values

# Initialize database
python init_db.py

# Run development server
python run.py
```

### Testing
```bash
# Test OAuth flow
curl "http://localhost:5000/api/auth/salesforce/initiate?email=test@example.com"

# Test health check (requires API key)
curl -X POST "http://localhost:5000/api/mcp/health-check" \
  -H "Authorization: Bearer your-api-key"
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agent      │    │  Customer       │    │   Salesforce    │
│                 │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ API Key Auth         │ OAuth 2.0            │
          │                      │                      │
          ▼                      ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                ForceWeaver MCP API                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Auth      │  │    MCP      │  │     Health Checker      │ │
│  │  Routes     │  │  Routes     │  │       Service           │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Security   │  │   Error     │  │      Logging            │ │
│  │   Core      │  │ Handling    │  │    Configuration        │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
                ┌─────────────────┐
                │   PostgreSQL    │
                │    Database     │
                └─────────────────┘
```

## License

This project is proprietary software. All rights reserved.

## Support

For support, please contact: support@forceweaver.com