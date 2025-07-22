#!/usr/bin/env python3
"""Fix user passwords on Heroku"""
from app import create_app, db
from app.models.user import User

def fix_passwords():
    app = create_app()
    with app.app_context():
        print("Fixing user passwords...")
        
        # Fix admin user password
        admin = User.query.filter_by(email="admin@forceweaver.com").first()
        if admin:
            print(f"Resetting password for: {admin.email}")
            admin.set_password("admin123")
            db.session.commit()
            print(f"Admin password reset. Testing: {admin.check_password('admin123')}")
        else:
            print("Admin user not found")
            
        # Fix test user password
        test_user = User.query.filter_by(email="test@forceweaver.com").first()
        if test_user:
            print(f"Resetting password for: {test_user.email}")
            test_user.set_password("test123")
            db.session.commit()
            print(f"Test user password reset. Testing: {test_user.check_password('test123')}")
        else:
            print("Test user not found")
            
        print("Password fixes completed!")

if __name__ == "__main__":
    fix_passwords() 