#!/usr/bin/env python3
"""
Database initialization script for ForceWeaver MCP API
Creates all tables and sets up initial data
"""

from app import create_app, db
from app.models import User, Customer, APIKey, SalesforceConnection, HealthCheckHistory
import sys

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        print("🔨 Initializing ForceWeaver MCP API Database...")
        
        try:
            # Check if tables exist and create if they don't
            print("📋 Creating database tables...")
            db.create_all()
            
            # Add new columns to existing SalesforceConnection records if they don't have them
            print("🔄 Updating existing SalesforceConnection records...")
            from sqlalchemy import text
            
            # Check if the new columns exist, add them if not
            try:
                # Try to select the new columns - if this fails, we need to add them
                result = db.session.execute(text("SELECT preferred_api_version FROM salesforce_connection LIMIT 1")).fetchone()
            except Exception as e:
                print("   Adding new API version columns...")
                try:
                    # Add the new columns
                    db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN preferred_api_version VARCHAR(10)"))
                    db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN available_api_versions TEXT"))
                    db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN api_versions_last_updated TIMESTAMP"))
                    db.session.commit()
                    print("   ✅ API version columns added successfully")
                except Exception as alter_error:
                    print(f"   ⚠️  Could not add columns (they may already exist): {alter_error}")
                    db.session.rollback()
            
            print("✅ Database tables created successfully!")
            
            # Display table information
            tables = db.metadata.tables.keys()
            print(f"📊 Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   • {table}")
                
            # Check for existing data
            print("\n📈 Database Status:")
            user_count = User.query.count()
            customer_count = Customer.query.count()
            connection_count = SalesforceConnection.query.count()
            api_key_count = APIKey.query.count()
            health_check_count = HealthCheckHistory.query.count()
            
            print(f"   Users: {user_count}")
            print(f"   Customers: {customer_count}")
            print(f"   Salesforce Connections: {connection_count}")
            print(f"   API Keys: {api_key_count}")
            print(f"   Health Check History: {health_check_count}")
            
            if connection_count > 0:
                print("\n🔧 Updating existing connections with default API version settings...")
                connections_updated = 0
                for connection in SalesforceConnection.query.all():
                    if not connection.preferred_api_version:
                        # Set default to latest version
                        connection.preferred_api_version = "v59.0"
                        connections_updated += 1
                
                if connections_updated > 0:
                    db.session.commit()
                    print(f"   ✅ Updated {connections_updated} connections with default API version")
            
            print(f"\n🎉 Database initialization completed successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            sys.exit(1)

if __name__ == "__main__":
    init_database() 