# ForceWeaver MCP Server - Heroku Deployment Guide

This guide provides detailed instructions for deploying ForceWeaver MCP Server to Heroku in production.

## 🎯 Overview

ForceWeaver uses a **single-server architecture** on Heroku:
- **Web dyno**: Runs the Flask web application and internal API
- **PostgreSQL add-on**: Database for user data, API keys, and usage tracking
- **Custom domain**: `mcp.forceweaver.com` with SSL certificate

## 📋 Prerequisites

### 1. Required Accounts & Tools

- **Heroku Account**: [Sign up at heroku.com](https://signup.heroku.com)
- **Heroku CLI**: [Install Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
- **Git**: Version control (should already be installed)
- **Domain**: `forceweaver.com` (you confirmed you own this)

### 2. Required Environment Setup

```bash
# Install Heroku CLI (macOS)
brew install heroku/brew/heroku

# Login to Heroku
heroku login

# Verify installation
heroku --version
```

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

```bash
# Navigate to your project
cd /Users/rohit.radhakrishnan/Documents/VScode/forceweaver-mcp

# Ensure you're on the main branch
git checkout main
git pull origin main

# Verify all files are committed
git status
```

### Step 2: Create Heroku Application

```bash
# Create new Heroku app
heroku create forceweaver-mcp

# Verify app creation
heroku apps:info forceweaver-mcp
```

**Expected Output:**
```
Creating app... done, ⬢ forceweaver-mcp
https://forceweaver-mcp-abc123.herokuapp.com/ | https://git.heroku.com/forceweaver-mcp.git
```

### Step 3: Add PostgreSQL Database

```bash
# Add PostgreSQL (free tier)
heroku addons:create heroku-postgresql:mini -a forceweaver-mcp

# Verify database was added
heroku config -a forceweaver-mcp
```

**Expected Output:**
```
DATABASE_URL: postgres://username:password@host:port/database
```

### Step 4: Configure Environment Variables

```bash
# Generate secure keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Set environment variables
heroku config:set SECRET_KEY="$SECRET_KEY" -a forceweaver-mcp
heroku config:set ENCRYPTION_KEY="$ENCRYPTION_KEY" -a forceweaver-mcp

# Set admin user (change these values!)
heroku config:set ADMIN_EMAIL="admin@forceweaver.com" -a forceweaver-mcp
heroku config:set ADMIN_NAME="ForceWeaver Admin" -a forceweaver-mcp
heroku config:set ADMIN_PASSWORD="ChangeThisPassword123!" -a forceweaver-mcp

# Set environment
heroku config:set FLASK_ENV="production" -a forceweaver-mcp
heroku config:set LOG_LEVEL="INFO" -a forceweaver-mcp

# Verify configuration
heroku config -a forceweaver-mcp
```

### Step 5: Deploy Application

```bash
# Add Heroku remote (if not already added)
git remote add heroku https://git.heroku.com/forceweaver-mcp.git

# Deploy to Heroku
git push heroku main
```

**Expected Output:**
```
Enumerating objects: 150, done.
...
remote: -----> Building on the Heroku-22 stack
remote: -----> Using buildpack: heroku/python
remote: -----> Python app detected
remote: -----> Installing python-3.11.6
remote: -----> Installing pip 23.3.1, setuptools 68.2.2 and wheel 0.41.2
remote: -----> Installing SQLite3
remote: -----> Installing requirements with pip
remote: -----> $ python seed_db.py
remote:        Database initialized successfully
remote:        Default rate configurations created
remote:        Admin user created: admin@forceweaver.com
remote: -----> Launching...
remote: -----> https://forceweaver-mcp-abc123.herokuapp.com/ deployed to Heroku
```

### Step 6: Verify Deployment

```bash
# Check application status
heroku ps -a forceweaver-mcp

# View logs
heroku logs --tail -a forceweaver-mcp

# Open application in browser
heroku open -a forceweaver-mcp
```

## 🌐 Custom Domain Setup

### Step 1: Add Custom Domain to Heroku

```bash
# Add custom domain
heroku domains:add mcp.forceweaver.com -a forceweaver-mcp

# Get DNS target
heroku domains -a forceweaver-mcp
```

**Expected Output:**
```
Domain Name           DNS Record Type  DNS Target
mcp.forceweaver.com   CNAME           abc-123-def-456.herokudns.com
```

### Step 2: Configure DNS (GoDaddy)

1. **Login to GoDaddy DNS Management**
   - Go to [GoDaddy DNS Management](https://dcc.godaddy.com/manage/dns)
   - Select `forceweaver.com` domain

2. **Add CNAME Record**
   - **Type**: CNAME
   - **Name**: mcp
   - **Value**: `abc-123-def-456.herokudns.com` (from Heroku command above)
   - **TTL**: 1 hour (3600 seconds)

3. **Save Changes**
   - Click "Save" to add the CNAME record
   - DNS propagation may take up to 24 hours

### Step 3: Enable SSL Certificate

```bash
# Enable automatic SSL certificate
heroku certs:auto:enable -a forceweaver-mcp

# Check SSL certificate status
heroku certs -a forceweaver-mcp
```

## 🔧 Configuration Management

### Environment Variables Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | `a1b2c3d4...` | Flask secret key for sessions |
| `ENCRYPTION_KEY` | ✅ | `gAAAAAB...` | Fernet key for encrypting secrets |
| `ADMIN_EMAIL` | ✅ | `admin@forceweaver.com` | Initial admin user email |
| `ADMIN_NAME` | ✅ | `ForceWeaver Admin` | Initial admin user name |
| `ADMIN_PASSWORD` | ✅ | `SecurePassword123!` | Initial admin password |
| `FLASK_ENV` | ✅ | `production` | Flask environment |
| `LOG_LEVEL` | ✅ | `INFO` | Logging level |
| `DATABASE_URL` | Auto | `postgres://...` | PostgreSQL connection (set by Heroku) |
| `PORT` | Auto | `5000` | Port number (set by Heroku) |

### Updating Configuration

```bash
# Update environment variables
heroku config:set VARIABLE_NAME="new_value" -a forceweaver-mcp

# View current configuration
heroku config -a forceweaver-mcp

# Remove a configuration
heroku config:unset VARIABLE_NAME -a forceweaver-mcp
```

## 📊 Monitoring & Maintenance

### Viewing Application Logs

```bash
# View recent logs
heroku logs -n 1000 -a forceweaver-mcp

# Follow logs in real-time
heroku logs --tail -a forceweaver-mcp

# Filter logs by source
heroku logs --source app -a forceweaver-mcp
```

### Database Management

```bash
# Connect to database
heroku pg:psql -a forceweaver-mcp

# View database info
heroku pg:info -a forceweaver-mcp

# Create database backup
heroku pg:backups:capture -a forceweaver-mcp

# Download backup
heroku pg:backups:download -a forceweaver-mcp
```

### Application Management

```bash
# Restart application
heroku restart -a forceweaver-mcp

# Scale dynos
heroku ps:scale web=1 -a forceweaver-mcp

# Check dyno usage
heroku ps -a forceweaver-mcp

# Run one-off commands
heroku run python seed_db.py -a forceweaver-mcp
```

## 🔄 Deployment Updates

### Regular Updates

```bash
# Make your changes locally
git add .
git commit -m "Update: feature description"

# Push to main branch
git push origin main

# Deploy to Heroku
git push heroku main

# Verify deployment
heroku logs --tail -a forceweaver-mcp
```

### Database Migrations

```bash
# If you add new models or fields, run migrations
heroku run python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()" -a forceweaver-mcp
```

### Emergency Rollback

```bash
# View recent releases
heroku releases -a forceweaver-mcp

# Rollback to previous release
heroku rollback v123 -a forceweaver-mcp
```

## 🛡️ Security Best Practices

### 1. Secure Environment Variables

```bash
# Rotate secrets regularly
NEW_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
heroku config:set SECRET_KEY="$NEW_SECRET_KEY" -a forceweaver-mcp
```

### 2. Database Security

```bash
# Enable database encryption at rest (available in paid plans)
heroku pg:settings:log-statement -s all -a forceweaver-mcp

# Regular backups
heroku scheduler:add "pg:backups:capture" -a forceweaver-mcp
```

### 3. Application Security

- **Change default admin password** immediately after first deployment
- **Enable two-factor authentication** for Heroku account
- **Regularly update dependencies** via `requirements.txt`
- **Monitor application logs** for suspicious activity

## 📈 Scaling Considerations

### Current Setup (Free/Hobby Tier)

- **Dynos**: 1 web dyno (hobby-basic recommended)
- **Database**: PostgreSQL Mini (free tier, 10K rows limit)
- **Expected Load**: 10 concurrent users, 1000 requests/month

### Scaling Up

```bash
# Upgrade to hobby dynos (recommended for production)
heroku dyno:type hobby -a forceweaver-mcp

# Upgrade database (when you exceed 10K rows)
heroku addons:upgrade heroku-postgresql:hobby-basic -a forceweaver-mcp

# Add more web dynos (if needed)
heroku ps:scale web=2 -a forceweaver-mcp
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs for errors
heroku logs --tail -a forceweaver-mcp

# Check dyno status
heroku ps -a forceweaver-mcp

# Common causes:
# - Missing environment variables
# - Database connection issues
# - Import errors in code
```

#### 2. Database Connection Errors

```bash
# Verify DATABASE_URL is set
heroku config:get DATABASE_URL -a forceweaver-mcp

# Test database connection
heroku run python -c "from app import create_app, db; app = create_app(); print('DB connection OK')" -a forceweaver-mcp
```

#### 3. SSL Certificate Issues

```bash
# Check certificate status
heroku certs -a forceweaver-mcp

# Force renewal if needed
heroku certs:auto:refresh -a forceweaver-mcp
```

#### 4. DNS Issues

```bash
# Check domain configuration
heroku domains -a forceweaver-mcp

# Test DNS resolution
nslookup mcp.forceweaver.com
```

### Getting Help

- **Heroku Support**: [help.heroku.com](https://help.heroku.com)
- **Application Logs**: `heroku logs --tail -a forceweaver-mcp`
- **Status Page**: [status.heroku.com](https://status.heroku.com)

## ✅ Post-Deployment Checklist

After successful deployment, verify:

- [ ] Application loads at `https://mcp.forceweaver.com`
- [ ] SSL certificate is active (green lock icon)
- [ ] Admin can login with configured credentials
- [ ] User registration works
- [ ] API key creation works
- [ ] Salesforce org connection works
- [ ] Internal API endpoints respond correctly
- [ ] Database is accessible and seeded
- [ ] Logs show no errors
- [ ] All environment variables are set
- [ ] DNS resolution is working

## 🎉 Success!

Your ForceWeaver MCP Server is now live at:

**🌐 Web Interface**: https://mcp.forceweaver.com
**🔧 Admin Panel**: https://mcp.forceweaver.com/auth/login
**📊 API Status**: https://mcp.forceweaver.com/api/v1.0/internal/health

## 🔄 Next Steps

1. **Test the complete flow**:
   - Register a test user
   - Create API key
   - Connect Salesforce org
   - Test MCP server integration

2. **Set up monitoring**:
   - Configure log monitoring
   - Set up uptime monitoring
   - Monitor usage and costs

3. **Update documentation**:
   - Share the live URL with users
   - Update integration guides
   - Create support documentation

Your ForceWeaver MCP Server is now production-ready! 🚀 