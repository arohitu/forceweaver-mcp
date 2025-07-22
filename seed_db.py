#!/usr/bin/env python3
"""
Database seed script for ForceWeaver MCP Server
Creates initial admin user and default configurations
"""
import os
from app import create_app, db
from app.models.user import User
from app.models.rate_configuration import RateConfiguration

def seed_database():
    """Seed the database with initial data"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        # Create default rate configurations
        print("Creating default rate configurations...")
        try:
            default_tiers = RateConfiguration.initialize_default_tiers()
            if default_tiers:
                print(f"Created {len(default_tiers)} rate configuration tiers")
            else:
                print("Rate configuration tiers already exist")
        except Exception as e:
            print(f"Warning: Could not create rate configurations: {e}")
        
        # Create admin user
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@forceweaver.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'forceweaver123')  # Change in production!
        admin_name = os.environ.get('ADMIN_NAME', 'ForceWeaver Admin')
        
        print(f"Checking for admin user: {admin_email}")
        
        # Check if admin already exists
        existing_admin = User.get_by_email(admin_email)
        
        if existing_admin:
            print("Admin user already exists")
            if not existing_admin.is_admin:
                existing_admin.is_admin = True
                db.session.commit()
                print("Updated existing user to admin")
        else:
            try:
                admin_user = User.create_user(
                    email=admin_email,
                    name=admin_name,
                    password=admin_password,
                    is_admin=True
                )
                print(f"Created admin user: {admin_email}")
                print(f"Admin password: {admin_password}")
                print("*** PLEASE CHANGE THE ADMIN PASSWORD AFTER FIRST LOGIN ***")
            except Exception as e:
                print(f"Error creating admin user: {e}")
        
        print("Database seeding completed!")
        
        # Print summary
        user_count = User.query.count()
        rate_config_count = RateConfiguration.query.count()
        
        print("\nDatabase Summary:")
        print(f"- Users: {user_count}")
        print(f"- Rate Configurations: {rate_config_count}")

if __name__ == "__main__":
    seed_database() 