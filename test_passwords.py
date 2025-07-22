#!/usr/bin/env python3
"""Test password validation on Heroku"""
from app import create_app, db
from app.models.user import User

def test_passwords():
    app = create_app()
    with app.app_context():
        print("Testing password validation...")
        
        # Test admin user
        admin = User.query.filter_by(email="admin@forceweaver.com").first()
        if admin:
            print(f"Admin user found: {admin.email}")
            print(f"Password test with 'admin123': {admin.check_password('admin123')}")
            print(f"Password hash length: {len(admin.password_hash) if admin.password_hash else 0}")
        else:
            print("Admin user not found")
            
        # Test the test user
        test_user = User.query.filter_by(email="test@forceweaver.com").first()
        if test_user:
            print(f"Test user found: {test_user.email}")
            print(f"Password test with 'test123': {test_user.check_password('test123')}")
            print(f"Password hash length: {len(test_user.password_hash) if test_user.password_hash else 0}")
        else:
            print("Test user not found")

if __name__ == "__main__":
    test_passwords() 