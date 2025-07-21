# 🔍 **ForceWeaver Debug Guide: Login to Dashboard Flow**

## 📋 **Complete User Journey Debugging**

This guide shows you exactly how to trace what happens from login through dashboard access, with all the debug logs I've added.

## 🎯 **Expected User Flow**

```
1. User accesses staging-healthcheck.forceweaver.com → Root route (/) 
2. Anonymous user → Redirects to /auth/login
3. User submits login form → Login processing
4. Successful authentication → Flask-Login session created
5. Redirect to /dashboard/ → Dashboard route processing
6. Customer record creation/retrieval → Dashboard rendering
```

## 🔧 **How to Access Debug Logs**

### **On Heroku (Staging)**
```bash
# Real-time log monitoring
heroku logs --tail -a forceweaver-mcp-staging

# Filter for specific log levels
heroku logs --tail -a forceweaver-mcp-staging | grep "INFO"
heroku logs --tail -a forceweaver-mcp-staging | grep "ERROR"

# Search for specific debug markers
heroku logs --tail -a forceweaver-mcp-staging | grep "LOGIN ROUTE"
heroku logs --tail -a forceweaver-mcp-staging | grep "Dashboard accessed"
```

### **Local Testing**
```bash
# Run with local config and watch logs
python3 -c "
from local_config import LocalConfig
from app import create_app
app = create_app(LocalConfig)
app.run(debug=True, port=5001)
"
```

## 📊 **Step-by-Step Debugging Checklist**

### **Step 1: Initial Access**
When you visit `https://staging-healthcheck.forceweaver.com/`

**Expected Logs:**
```
=== REQUEST RECEIVED ===
Host: staging-healthcheck.forceweaver.com
Path: /
Method: GET
Request from anonymous user
Domain routing - Dashboard: True, API: False, Localhost: False
Routing to dashboard/web routes

=== ROOT INDEX ROUTE ===
Root route accessed with host: staging-healthcheck.forceweaver.com
Domain check - Dashboard domain: True, Localhost: False
Processing dashboard/web request
Current user authenticated: False
Anonymous user - redirecting to login
Login redirect URL: /auth/login
```

**✅ What to Check:**
- Domain routing correctly identifies dashboard domain
- User is anonymous (not authenticated)
- Redirect to login is working

**❌ Troubleshooting:**
- If no logs appear → Check Heroku app logs are accessible
- If domain routing wrong → Check domain configuration
- If redirect fails → Check Flask blueprint registration

### **Step 2: Login Page Access**
When redirected to `/auth/login`

**Expected Logs:**
```
=== REQUEST RECEIVED ===
Path: /auth/login
Method: GET
Request from anonymous user

=== LOGIN ROUTE ACCESSED ===
Request method: GET
Current user authenticated: False
Request path: /auth/login
Form created successfully: <class 'app.web.forms.LoginForm'>
GET request - showing login form
Rendering login template
```

**✅ What to Check:**
- Login route is accessible
- Form is created successfully
- Template renders without errors

**❌ Troubleshooting:**
- If "Form creation failed" → Check Flask-WTF is installed
- If template error → Check templates/auth/login.html exists
- If CSRF error → Check CSRF protection is working

### **Step 3: Login Form Submission**
When you enter credentials and submit

**Expected Logs:**
```
=== REQUEST RECEIVED ===
Path: /auth/login
Method: POST
Request from anonymous user

=== LOGIN ROUTE ACCESSED ===
Request method: POST
Form created successfully: <class 'app.web.forms.LoginForm'>

=== LOGIN FORM SUBMITTED ===
Login attempt for email: your-email@example.com
Remember me: False
Database query result - User found: True
User details: ID=1, Email=your-email@example.com, Active=True, First=YourName
Password validation result: True

=== LOGIN SUCCESS - PROCESSING ===
Updating last_login to: 2025-01-21 10:30:45.123456
Database commit completed for last_login
Calling Flask-Login login_user()...
Flask-Login login_user result: True
Current user after login_user(): <User 1>
Current user authenticated: True
Current user ID: 1
Next page from request: None
Using default dashboard redirect
Final redirect URL: /dashboard/
Flash message set: Welcome back!

=== REDIRECTING TO DASHBOARD ===
Login process completed successfully
```

**✅ What to Check:**
- User is found in database
- Password validation passes
- Flask-Login `login_user()` returns `True`
- Current user becomes authenticated
- Redirect URL is correct

**❌ Troubleshooting:**
- If "User found: False" → Check user exists in database
- If "Password validation: False" → Check password is correct
- If "login_user result: False" → Check Flask-Login configuration
- If redirect fails → Check dashboard route registration

### **Step 4: Dashboard Redirect**
When login redirects to `/dashboard/`

**Expected Logs:**
```
=== REQUEST RECEIVED ===
Path: /dashboard/
Method: GET
Request from authenticated user: your-email@example.com (ID: 1)
Domain routing - Dashboard: True, API: False, Localhost: False
Routing to dashboard/web routes

=== USER LOADER CALLED ===
Loading user with ID: 1
User loaded successfully: your-email@example.com (ID: 1)
```

**✅ What to Check:**
- Request shows authenticated user
- User loader successfully retrieves user
- Routing directs to dashboard

**❌ Troubleshooting:**
- If still shows "anonymous user" → Session not persisting
- If user loader fails → Check database connection
- If routing wrong → Check blueprint URL prefixes

### **Step 5: Dashboard Processing**
When dashboard route processes the request

**Expected Logs:**
```
=== Dashboard accessed by user: 1 (your-email@example.com)
Getting or creating customer record...
Getting customer for user 1 (your-email@example.com)
Existing customer: 1  [OR] Existing customer: None
[If creating new customer:]
Creating new customer record...
Customer added to session, committing...
Customer committed, refreshing...
New customer created with ID: 2

Customer record obtained: ID=2
Initializing dashboard statistics...
Initial stats: {'has_salesforce_connection': False, 'has_api_key': False, ...}
Querying health check statistics...
Health check count: 0
Querying last health check...
No health checks found
Checking API key...
No API key found
Rendering dashboard template...
```

**✅ What to Check:**
- User is properly identified
- Customer record is created or retrieved
- Statistics are calculated without errors
- Template rendering succeeds

**❌ Troubleshooting:**
- If customer creation fails → Check database schema
- If statistics queries fail → Check table relationships
- If template fails → Check template syntax and variables

## 🚨 **Common Issues and Solutions**

### **Issue 1: 500 Error on Dashboard**
**Symptoms:** Dashboard returns `{"error": {"message": "An unexpected error occurred", "status_code": 500}}`

**Debug Steps:**
1. Check for exception in logs: `heroku logs --tail -a forceweaver-mcp-staging | grep "ERROR"`
2. Look for template errors or missing variables
3. Verify database schema matches models

**Solution:** Look for the specific error in the logs and address it

### **Issue 2: Login Doesn't Persist**
**Symptoms:** Login appears successful but dashboard shows anonymous user

**Debug Steps:**
1. Check if `login_user()` returns `True`
2. Verify session is being created
3. Check Flask-Login configuration

**Solution:** 
```python
# Check these settings in config
SECRET_KEY = 'proper-secret-key'  # Must be consistent
SESSION_COOKIE_SECURE = False      # For development
```

### **Issue 3: User Loader Fails**
**Symptoms:** User loader cannot find user after login

**Debug Steps:**
1. Check user ID in session
2. Verify database connection
3. Check user exists in database

**Solution:** Verify user ID is being stored correctly in session

### **Issue 4: Template Errors**
**Symptoms:** Template rendering fails with undefined variables

**Debug Steps:**
1. Check template variables are passed to `render_template()`
2. Verify template syntax
3. Check for undefined Jinja2 functions

**Solution:** Ensure all template variables are defined and passed correctly

## 🎯 **Debug Commands for Each Issue**

### **Check Database State**
```bash
# Connect to Heroku database
heroku pg:psql -a forceweaver-mcp-staging

# Check users
SELECT id, email, first_name, is_active, created_at FROM "user";

# Check customers
SELECT id, user_id, email, created_at FROM customer;

# Check relationships
SELECT u.id, u.email, c.id as customer_id 
FROM "user" u 
LEFT JOIN customer c ON u.id = c.user_id;
```

### **Test Authentication Flow**
```bash
# Test login endpoint
curl -X POST https://staging-healthcheck.forceweaver.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@example.com&password=password123"

# Test dashboard access (will show redirect if not authenticated)
curl -I https://staging-healthcheck.forceweaver.com/dashboard/
```

### **Monitor Real-Time Logs**
```bash
# Watch all logs
heroku logs --tail -a forceweaver-mcp-staging

# Watch only your debug sections
heroku logs --tail -a forceweaver-mcp-staging | grep -E "(LOGIN ROUTE|Dashboard accessed|USER LOADER)"

# Watch for errors
heroku logs --tail -a forceweaver-mcp-staging | grep -E "(ERROR|WARNING|Exception)"
```

## 📝 **Creating Debug Sessions**

### **Manual Test Session**
1. **Open Terminal**: `heroku logs --tail -a forceweaver-mcp-staging`
2. **Open Browser**: Navigate to `https://staging-healthcheck.forceweaver.com/`
3. **Follow Logs**: Watch the debug output in real-time
4. **Login**: Submit your credentials and watch the authentication flow
5. **Check Dashboard**: Verify dashboard loads and all logs show success

### **Automated Test**
```bash
# Create a test script
cat > test_login_flow.py << 'EOF'
import requests
import time

# Test the complete flow
session = requests.Session()

print("1. Testing root access...")
response = session.get('https://staging-healthcheck.forceweaver.com/')
print(f"Status: {response.status_code}")

print("2. Testing login page...")
response = session.get('https://staging-healthcheck.forceweaver.com/auth/login')
print(f"Status: {response.status_code}")

print("3. Check Heroku logs for debug output")
EOF

python3 test_login_flow.py
```

## 🎊 **Success Indicators**

When everything is working correctly, you should see:

✅ **Complete log chain** from request → login → authentication → dashboard
✅ **No ERROR or WARNING logs** during normal flow
✅ **User loader** successfully retrieves user
✅ **Customer record** created or retrieved
✅ **Dashboard statistics** calculated without errors
✅ **Template rendering** completes successfully
✅ **Final HTTP 200** response with dashboard HTML

This debugging setup will show you **exactly** what happens at every step of the user journey! 🔍 