#!/usr/bin/env python3
"""
Database seeding script for ForceWeaver MCP Server
"""
from app import create_app, db
from app.models.user import User
from app.models.rate_configuration import RateConfiguration

def seed_database():
    """Create tables and seed initial data"""
    print("Creating database tables...")
    db.create_all()
    
    # Seed rate configurations
    print("Creating default rate configurations...")
    try:
        if not RateConfiguration.query.filter_by(is_default=True).first():
            default_rate = RateConfiguration(
                tier_name='default',
                display_name='Default',
                calls_per_hour=100,
                burst_limit=20,
                is_default=True,
                description='Default rate configuration for new users'
            )
            db.session.add(default_rate)
            db.session.commit()
            print("Default rate configuration created")
    except Exception as e:
        print(f"Warning: Could not create rate configurations: {e}")
        db.session.rollback()
    
    # Create admin user
    admin_email = "admin@forceweaver.com"
    admin_password = "admin123"
    
    print(f"Checking for admin user: {admin_email}")
    
    try:
        # Check if admin user exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if not existing_admin:
            print("Creating admin user...")
            admin_user = User(
                email=admin_email,
                name="System Administrator"
            )
            admin_user.set_password(admin_password)
            admin_user.is_admin = True
            admin_user.is_active = True
            
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created: {admin_email}")
        else:
            print("Admin user already exists")
            
        # Create test user  
        test_email = "test@forceweaver.com"
        test_password = "test123"
        
        existing_test = User.query.filter_by(email=test_email).first()
        
        if not existing_test:
            print("Creating test user...")
            test_user = User(
                email=test_email,
                name="Test User"
            )
            test_user.set_password(test_password)
            test_user.is_active = True
            
            db.session.add(test_user)
            db.session.commit()
            print(f"Test user created: {test_email}")
        else:
            print("Test user already exists")
            
    except Exception as e:
        print(f"Error creating users: {e}")
        db.session.rollback()
    
    print("Database seeding completed!")
    
    # Print summary
    print("\nDatabase Summary:")
    print(f"- Users: {User.query.count()}")
    print(f"- Rate Configurations: {RateConfiguration.query.count()}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_database() 