#!/usr/bin/env python3
"""
Local Dashboard Test Script
Test the dashboard functionality locally
"""

from local_config import LocalConfig
from app import create_app
from app.models import User, Customer
from app import db

def test_dashboard_locally():
    """Test dashboard functionality with local SQLite database"""
    
    # Create app
    app = create_app(LocalConfig)
    
    with app.app_context():
        # Create database tables
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")
        
        # Create test user (or get existing one)
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
            print(f"Test user created: {test_user.id} ({test_user.email})")
        else:
            print(f"Test user already exists: {test_user.id} ({test_user.email})")
        
        # Test customer creation (or get existing one)
        customer = Customer.query.filter_by(user_id=test_user.id).first()
        if not customer:
            customer = Customer(
                email=test_user.email,
                user_id=test_user.id
            )
            db.session.add(customer)
            db.session.commit()
            print(f"Customer created: {customer.id}")
        else:
            print(f"Customer already exists: {customer.id}")
        
        # Test relationships
        print(f"User customer relationship: {test_user.customer}")
        print(f"Customer user relationship: {customer.user}")
        
        # Test client
        with app.test_client() as client:
            print("\nTesting routes...")
            
            # Test health endpoint
            response = client.get('/health')
            print(f"Health endpoint: {response.status_code} - {response.get_json()}")
            
            # Test login page (should be accessible without auth)
            response = client.get('/auth/login')
            print(f"Login page: {response.status_code}")
            
            # Test dashboard without login (should redirect)
            response = client.get('/dashboard/')
            print(f"Dashboard without auth: {response.status_code} (should be 302 redirect)")
            
            # Test login
            response = client.post('/auth/login', data={
                'email': 'test@example.com',
                'password': 'password123',
                'csrf_token': 'dummy'  # For testing we'll disable CSRF
            })
            print(f"Login attempt: {response.status_code}")
            
    print("\nLocal testing completed!")

if __name__ == "__main__":
    test_dashboard_locally() 