#!/usr/bin/env python3
"""
Migration script for API Version columns
This script adds the new API version columns to existing SalesforceConnection records
"""

import sys
from app import create_app, db
from app.models import SalesforceConnection
from app.services.salesforce_service import update_connection_api_versions
from sqlalchemy import text

def migrate_api_version_columns():
    """Add API version columns and populate them for existing connections."""
    
    print("🔄 Migrating API Version Columns...")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Add columns if they don't exist
            print("📋 Checking/adding database columns...")
            
            try:
                # Check if columns exist
                result = db.session.execute(text("SELECT preferred_api_version FROM salesforce_connection LIMIT 1")).fetchone()
                print("   ✅ API version columns already exist")
            except Exception:
                print("   ➕ Adding new API version columns...")
                try:
                    db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN preferred_api_version VARCHAR(10)"))
                    db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN available_api_versions TEXT"))
                    db.session.execute(text("ALTER TABLE salesforce_connection ADD COLUMN api_versions_last_updated TIMESTAMP"))
                    db.session.commit()
                    print("   ✅ Successfully added API version columns")
                except Exception as e:
                    print(f"   ⚠️  Error adding columns (may already exist): {e}")
                    db.session.rollback()
            
            # Step 2: Find existing connections
            print("\n🔗 Processing existing Salesforce connections...")
            connections = SalesforceConnection.query.all()
            print(f"   Found {len(connections)} existing connections")
            
            if not connections:
                print("   No connections to migrate")
                return True
            
            # Step 3: Update each connection
            updated_count = 0
            for connection in connections:
                print(f"\n   Processing connection: {connection.salesforce_org_id}")
                
                try:
                    # Set default preferred version if not set
                    if not connection.preferred_api_version:
                        connection.preferred_api_version = "v61.0"  # Set to recent version
                        print(f"     Set default preferred version: v61.0")
                    
                    # Try to fetch real API versions from Salesforce
                    try:
                        print(f"     Fetching available versions from Salesforce...")
                        versions = update_connection_api_versions(connection, force_update=True)
                        if versions:
                            # Update preferred to latest if we got real versions
                            connection.preferred_api_version = versions[0]
                            print(f"     ✅ Fetched {len(versions)} versions, set preferred to: {versions[0]}")
                        else:
                            print(f"     ⚠️  No versions fetched, keeping default: {connection.preferred_api_version}")
                    except Exception as version_error:
                        print(f"     ⚠️  Could not fetch versions: {version_error}")
                        print(f"     Keeping default version: {connection.preferred_api_version}")
                    
                    updated_count += 1
                    
                except Exception as conn_error:
                    print(f"     ❌ Error processing connection: {conn_error}")
            
            # Step 4: Commit all changes
            db.session.commit()
            print(f"\n✅ Successfully updated {updated_count} connections")
            
            # Step 5: Verify the migration
            print("\n📊 Migration Verification:")
            for connection in SalesforceConnection.query.all():
                print(f"   {connection.salesforce_org_id}:")
                print(f"     Preferred Version: {connection.preferred_api_version}")
                print(f"     Available Versions: {len(connection.available_versions_list)} versions")
                print(f"     Effective Version: {connection.get_effective_api_version()}")
            
            print(f"\n🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = migrate_api_version_columns()
    if not success:
        sys.exit(1) 