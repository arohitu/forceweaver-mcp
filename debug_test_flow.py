#!/usr/bin/env python3
"""
Debug Test Flow - Complete User Journey Simulation
Shows all debug logs from login through dashboard
"""

from local_config import LocalConfig
from app import create_app
from app.models import User, Customer
from app import db
import time

def setup_test_data():
    """Set up test data for debugging"""
    # Create or get test user
    test_user = User.query.filter_by(email="debug@test.com").first()
    if not test_user:
        test_user = User(
            email="debug@test.com",
            first_name="Debug",
            last_name="User"
        )
        test_user.set_password("debug123")
        db.session.add(test_user)
        db.session.commit()
        print(f"✅ Created test user: {test_user.email}")
    else:
        print(f"✅ Using existing test user: {test_user.email}")
    
    return test_user

def simulate_complete_flow():
    """Simulate complete user flow with debug logging"""
    
    # Create app
    app = create_app(LocalConfig)
    
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Set up test data
        test_user = setup_test_data()
        
        print("\n" + "="*60)
        print("🚀 STARTING COMPLETE USER FLOW SIMULATION")
        print("="*60)
        
        with app.test_client() as client:
            
            # Step 1: Access root page (anonymous)
            print("\n📍 STEP 1: Accessing root page as anonymous user...")
            print("-" * 50)
            response = client.get('/')
            print(f"Status: {response.status_code}")
            print(f"Should redirect to login: {response.status_code == 302}")
            
            # Step 2: Access login page
            print("\n📍 STEP 2: Accessing login page...")
            print("-" * 50)
            response = client.get('/auth/login')
            print(f"Status: {response.status_code}")
            print(f"Login page loads: {response.status_code == 200}")
            
            # Step 3: Get CSRF token for login
            print("\n📍 STEP 3: Extracting CSRF token...")
            print("-" * 50)
            csrf_token = None
            if b'csrf_token' in response.data:
                print("✅ CSRF token found in response")
                # Extract CSRF token from hidden input
                import re
                token_match = re.search(b'name="csrf_token" value="([^"]+)"', response.data)
                if token_match:
                    csrf_token = token_match.group(1).decode()
                    print(f"✅ CSRF token extracted: {csrf_token[:20]}...")
                else:
                    print("❌ Could not extract CSRF token")
            else:
                print("❌ No CSRF token in response")
            
            # Step 4: Submit login form
            print("\n📍 STEP 4: Submitting login form...")
            print("-" * 50)
            login_data = {
                'email': 'debug@test.com',
                'password': 'debug123',
                'remember_me': False
            }
            if csrf_token:
                login_data['csrf_token'] = csrf_token
            
            response = client.post('/auth/login', data=login_data, follow_redirects=False)
            print(f"Login response status: {response.status_code}")
            print(f"Should redirect (302): {response.status_code == 302}")
            
            if response.status_code == 302:
                redirect_url = response.headers.get('Location', '')
                print(f"Redirect location: {redirect_url}")
                print(f"Redirecting to dashboard: {'/dashboard/' in redirect_url}")
            else:
                print("❌ Login did not redirect - check logs for authentication issues")
            
            # Step 5: Follow redirect to dashboard
            print("\n📍 STEP 5: Accessing dashboard after login...")
            print("-" * 50)
            response = client.get('/dashboard/')
            print(f"Dashboard status: {response.status_code}")
            print(f"Dashboard loads successfully: {response.status_code == 200}")
            
            if response.status_code == 200:
                print("✅ Dashboard loaded successfully!")
                # Check for staging badge
                if b'STAGING' in response.data:
                    print("✅ Staging badge found in dashboard")
                else:
                    print("ℹ️  No staging badge (may be normal for local testing)")
                
                # Check for welcome message
                if b'Welcome' in response.data:
                    print("✅ Welcome message found")
                else:
                    print("⚠️  No welcome message found")
                    
            else:
                print("❌ Dashboard failed to load - check logs for errors")
            
            # Step 6: Test simple debug routes
            print("\n📍 STEP 6: Testing debug routes...")
            print("-" * 50)
            
            # Test simple dashboard
            response = client.get('/dashboard/simple')
            print(f"Simple dashboard: {response.status_code} ({'✅ OK' if response.status_code == 200 else '❌ FAIL'})")
            
            # Test API route
            response = client.get('/dashboard/test')
            print(f"Test API route: {response.status_code} ({'✅ OK' if response.status_code == 200 else '❌ FAIL'})")
            if response.status_code == 200:
                test_data = response.get_json()
                print(f"Test response: {test_data}")
        
        print("\n" + "="*60)
        print("🏁 FLOW SIMULATION COMPLETED")
        print("="*60)
        print("\n📋 DEBUGGING CHECKLIST:")
        print("✅ Check all debug logs appeared above")
        print("✅ Verify each step completed successfully")
        print("✅ Look for any ERROR or WARNING messages")
        print("✅ Confirm dashboard loaded with proper content")
        
        print("\n🔍 TO DEBUG ON HEROKU:")
        print("1. Deploy these debug changes")
        print("2. Run: heroku logs --tail -a forceweaver-mcp-staging")
        print("3. Navigate through login flow in browser")
        print("4. Watch debug logs in real-time")

if __name__ == "__main__":
    simulate_complete_flow() 