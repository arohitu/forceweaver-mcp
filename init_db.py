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
            print("🔄 Checking for API version columns...")
            from sqlalchemy import text
            
            # Check if the new columns exist, add them if not
            columns_exist = True
            try:
                # Try to select the new columns - if this fails, we need to add them
                result = db.session.execute(text("SELECT preferred_api_version FROM salesforce_connection LIMIT 1")).fetchone()
                print("   ✅ API version columns already exist")
            except Exception as e:
                print("   ➕ Adding new API version columns...")
                columns_exist = False
                try:
                    # Rollback any failed transaction first
                    db.session.rollback()
                    
                    # Add the new columns in separate transactions
                    try:
                        db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN preferred_api_version VARCHAR(10)"))
                        db.session.commit()
                        print("   ✅ Added preferred_api_version column")
                    except Exception as e1:
                        db.session.rollback()
                        print(f"   ⚠️  preferred_api_version column may already exist: {e1}")
                    
                    try:
                        db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN available_api_versions TEXT"))
                        db.session.commit()
                        print("   ✅ Added available_api_versions column")
                    except Exception as e2:
                        db.session.rollback()
                        print(f"   ⚠️  available_api_versions column may already exist: {e2}")
                    
                    try:
                        db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN api_versions_last_updated TIMESTAMP"))
                        db.session.commit()
                        print("   ✅ Added api_versions_last_updated column")
                    except Exception as e3:
                        db.session.rollback()
                        print(f"   ⚠️  api_versions_last_updated column may already exist: {e3}")
                    
                    print("   ✅ API version columns setup completed")
                    
                except Exception as alter_error:
                    print(f"   ❌ Error adding columns: {alter_error}")
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
                        # Set default to more recent version
                        connection.preferred_api_version = "v61.0"  # Summer '24 - more recent than v52.0
                        connections_updated += 1
                        print(f"   Set default API version for {connection.salesforce_org_id}: v61.0")
                        
                        # Try to fetch real API versions if possible
                        try:
                            from app.services.salesforce_service import update_connection_api_versions
                            print(f"   Attempting to fetch real API versions for {connection.salesforce_org_id}...")
                            versions = update_connection_api_versions(connection, force_update=True)
                            if versions:
                                # Update preferred to latest if we got real versions
                                connection.preferred_api_version = versions[0]
                                print(f"   ✅ Updated to latest available version: {versions[0]}")
                            else:
                                print(f"   ⚠️  Keeping default version: {connection.preferred_api_version}")
                        except Exception as version_error:
                            print(f"   ⚠️  Could not fetch API versions: {version_error}")
                            print(f"   Keeping default version: {connection.preferred_api_version}")
                
                if connections_updated > 0:
                    db.session.commit()
                    print(f"   ✅ Updated {connections_updated} connections with API version settings")
            
            print(f"\n🎉 Database initialization completed successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            sys.exit(1)

if __name__ == "__main__":
    init_database() 