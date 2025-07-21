#!/usr/bin/env python3
"""
Simple Dashboard Route Test
Test the dashboard route directly with a logged-in user session
"""

from local_config import LocalConfig
from app import create_app
from app.models import User, Customer
from app import db
from flask_login import login_user

def test_dashboard_route():
    """Test the dashboard route directly"""
    
    # Create app
    app = create_app(LocalConfig)
    
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Get or create test user
        test_user = User.query.filter_by(email="test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                first_name="Test",
                last_name="User"
            )
            test_user.set_password("password123")
            db.session.add(test_user)
            db.session.commit()
        
        # Test with request context and logged-in user
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            print(f"Testing dashboard for user: {test_user.email}")
            
            # Test simple route first
            print("Testing /dashboard/simple route...")
            response = client.get('/dashboard/simple')
            print(f"Simple dashboard: {response.status_code}")
            if response.status_code == 200:
                print("✅ Simple dashboard works!")
                print(response.data.decode()[:200] + "..." if len(response.data.decode()) > 200 else response.data.decode())
            else:
                print(f"❌ Simple dashboard failed: {response.data.decode()}")
            
            print("\nTesting /dashboard/test route...")
            response = client.get('/dashboard/test')
            print(f"Test route: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ Test route works: {response.get_json()}")
            else:
                print(f"❌ Test route failed: {response.data.decode()}")
            
            print("\nTesting main /dashboard/ route...")
            response = client.get('/dashboard/')
            print(f"Main dashboard: {response.status_code}")
            if response.status_code == 200:
                print("✅ Main dashboard works!")
            else:
                print(f"❌ Main dashboard failed")
                print(f"Response data: {response.data.decode()[:500]}...")

if __name__ == "__main__":
    test_dashboard_route() 