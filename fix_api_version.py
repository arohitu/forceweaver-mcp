#!/usr/bin/env python3
"""
Quick fix script to update API versions for existing connections
"""

import sys
from app import create_app, db
from app.models import SalesforceConnection
from app.services.salesforce_service import update_connection_api_versions

def fix_api_versions():
    """Update API versions for all existing connections."""
    
    print("🔧 Fixing API Versions...")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all connections
            connections = SalesforceConnection.query.all()
            print(f"Found {len(connections)} Salesforce connections")
            
            if not connections:
                print("No connections to update")
                return
            
            for connection in connections:
                print(f"\n📋 Processing: {connection.salesforce_org_id}")
                print(f"   Current preferred version: {connection.preferred_api_version}")
                
                # Update to newer default if needed
                if not connection.preferred_api_version or connection.preferred_api_version in ['v52.0', 'v59.0']:
                    print("   Setting default to v61.0...")
                    connection.preferred_api_version = "v61.0"
                
                # Try to fetch real API versions
                try:
                    print("   Fetching available API versions from Salesforce...")
                    versions = update_connection_api_versions(connection, force_update=True)
                    
                    if versions:
                        # Update to latest available version
                        latest_version = versions[0]
                        connection.preferred_api_version = latest_version
                        print(f"   ✅ Updated to latest version: {latest_version}")
                        print(f"   Available versions: {', '.join(versions[:3])}...")
                    else:
                        print(f"   ⚠️  No versions fetched, using: {connection.preferred_api_version}")
                        
                except Exception as e:
                    print(f"   ❌ Error fetching versions: {e}")
                    print(f"   Using default: {connection.preferred_api_version}")
                
                print(f"   Final version: {connection.preferred_api_version}")
            
            # Save all changes
            db.session.commit()
            print(f"\n✅ Successfully updated {len(connections)} connections!")
            
            # Verify results
            print(f"\n📊 Final Status:")
            for connection in SalesforceConnection.query.all():
                effective_version = connection.get_effective_api_version()
                print(f"   {connection.salesforce_org_id}: {effective_version}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == "__main__":
    success = fix_api_versions()
    if not success:
        sys.exit(1)
    print("\n🎉 API version fix completed!") 