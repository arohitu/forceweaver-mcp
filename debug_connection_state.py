#!/usr/bin/env python3
"""
Debug script to check the current state of Salesforce connections
This helps diagnose API version issues
"""

from app import create_app, db
from app.models import SalesforceConnection, Customer
from sqlalchemy import text
import json

def debug_connection_state():
    """Debug the current state of Salesforce connections."""
    
    print("🔍 Debugging Salesforce Connection State")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check database schema
            print("📋 Checking database schema...")
            
            try:
                result = db.session.execute(text("SELECT preferred_api_version, available_api_versions, api_versions_last_updated FROM salesforce_connection LIMIT 1")).fetchone()
                print("   ✅ API version columns exist in database")
            except Exception as e:
                print(f"   ❌ API version columns missing or error: {e}")
                return
            
            # Get all connections
            print("\n🔗 Salesforce Connections:")
            connections = SalesforceConnection.query.all()
            print(f"   Found {len(connections)} connections")
            
            if not connections:
                print("   No connections found")
                return
            
            for i, connection in enumerate(connections, 1):
                print(f"\n   Connection #{i}:")
                print(f"     ID: {connection.id}")
                print(f"     Org ID: {connection.salesforce_org_id}")
                print(f"     Instance URL: {connection.instance_url}")
                print(f"     Is Sandbox: {connection.is_sandbox}")
                print(f"     Customer ID: {connection.customer_id}")
                
                # API Version info
                print(f"     Preferred Version: {connection.preferred_api_version}")
                print(f"     Available Versions Raw: {connection.available_api_versions}")
                
                try:
                    available_list = connection.available_versions_list
                    print(f"     Available Versions List: {available_list}")
                    print(f"     Count: {len(available_list) if available_list else 0}")
                except Exception as e:
                    print(f"     Error getting available versions: {e}")
                
                try:
                    effective = connection.get_effective_api_version()
                    print(f"     Effective Version: {effective}")
                except Exception as e:
                    print(f"     Error getting effective version: {e}")
                
                print(f"     Last Updated: {connection.api_versions_last_updated}")
                
                # Check customer
                try:
                    customer = Customer.query.get(connection.customer_id)
                    if customer:
                        print(f"     Customer Email: {customer.email}")
                    else:
                        print(f"     Customer: Not found")
                except Exception as e:
                    print(f"     Customer Error: {e}")
                
                print("     " + "-" * 40)
            
            # Test API version fetching
            print(f"\n🧪 Testing API version functionality:")
            test_connection = connections[0]  # Use first connection for testing
            
            try:
                print(f"   Testing with connection: {test_connection.salesforce_org_id}")
                from app.services.salesforce_service import get_available_api_versions
                
                print("   Attempting to fetch API versions...")
                versions = get_available_api_versions(test_connection)
                
                if versions:
                    print(f"   ✅ Successfully fetched {len(versions)} versions:")
                    for version in versions[:3]:  # Show first 3
                        print(f"     • {version.get('version')} - {version.get('label')}")
                else:
                    print("   ⚠️  No versions returned")
                    
            except Exception as e:
                print(f"   ❌ Error fetching versions: {e}")
            
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_connection_state() 