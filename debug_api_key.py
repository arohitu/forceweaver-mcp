#!/usr/bin/env python3
"""
Debug and cleanup script for API key database records
"""
import os
import sys
import hashlib
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Customer, SalesforceConnection, APIKey

def hash_api_key(api_key):
    """Hash an API key the same way the system does"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def debug_api_key(api_key_value):
    """Debug what's in the database for a specific API key"""
    app = create_app()
    
    with app.app_context():
        # Hash the API key
        key_hash = hash_api_key(api_key_value)
        print(f"🔍 Looking for API key hash: {key_hash}")
        
        # Find the API key record
        api_key_record = APIKey.query.filter_by(key_hash=key_hash).first()
        
        if not api_key_record:
            print("❌ API key not found in database!")
            return
        
        print(f"✅ Found API key record:")
        print(f"   ID: {api_key_record.id}")
        print(f"   Active: {api_key_record.is_active}")
        print(f"   Customer ID: {api_key_record.customer_id}")
        print(f"   Created: {api_key_record.created_at}")
        
        # Get customer record
        customer = Customer.query.get(api_key_record.customer_id)
        if customer:
            print(f"✅ Found customer record:")
            print(f"   ID: {customer.id}")
            print(f"   Name: {customer.name}")
            print(f"   Email: {customer.email}")
            print(f"   Created: {customer.created_at}")
        else:
            print("❌ Customer record not found!")
            return
        
        # Get Salesforce connection
        sf_connection = customer.salesforce_connection
        if sf_connection:
            print(f"✅ Found Salesforce connection:")
            print(f"   ID: {sf_connection.id}")
            print(f"   Org ID: {sf_connection.salesforce_org_id}")
            print(f"   Instance URL: {sf_connection.instance_url}")
            print(f"   Is Sandbox: {sf_connection.is_sandbox}")
            print(f"   Preferred API Version: {sf_connection.preferred_api_version}")
            print(f"   Available Versions: {sf_connection.available_api_versions}")
            print(f"   Created: {sf_connection.created_at}")
            print(f"   Updated: {sf_connection.updated_at}")
            
            # Check if refresh token exists
            if sf_connection.encrypted_refresh_token:
                print(f"   Refresh Token: Present (encrypted)")
            else:
                print(f"   Refresh Token: ❌ MISSING")
        else:
            print("❌ No Salesforce connection found!")
        
        return api_key_record, customer, sf_connection

def cleanup_database():
    """Clean up all database records"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning up database...")
        
        # Get current counts
        api_key_count = APIKey.query.count()
        customer_count = Customer.query.count()
        sf_connection_count = SalesforceConnection.query.count()
        
        print(f"📊 Current records:")
        print(f"   API Keys: {api_key_count}")
        print(f"   Customers: {customer_count}")
        print(f"   SF Connections: {sf_connection_count}")
        
        # Delete all records
        print("🗑️  Deleting all records...")
        SalesforceConnection.query.delete()
        APIKey.query.delete()
        Customer.query.delete()
        
        db.session.commit()
        
        print("✅ Database cleaned up!")
        
        # Verify cleanup
        api_key_count = APIKey.query.count()
        customer_count = Customer.query.count()
        sf_connection_count = SalesforceConnection.query.count()
        
        print(f"📊 After cleanup:")
        print(f"   API Keys: {api_key_count}")
        print(f"   Customers: {customer_count}")
        print(f"   SF Connections: {sf_connection_count}")

def test_api_key_direct(api_key_value):
    """Test the API key directly against our endpoints"""
    import requests
    import json
    
    print("🧪 Testing API key against debug endpoint...")
    
    # Test the debug endpoint
    url = "https://staging-api.forceweaver.com/api/mcp/test-api-versions"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key_value
    }
    
    try:
        response = requests.post(url, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', 'unknown')}")
            
            if 'results' in data:
                results = data['results']
                print(f"   Instance URL: {results.get('instance_url', 'unknown')}")
                
                services_endpoint = results.get('services_data_endpoint', {})
                print(f"   Services Data Status: {services_endpoint.get('status_code', 'unknown')}")
                
                if 'version_tests' in results:
                    version_tests = results['version_tests']
                    working_versions = [v for v, info in version_tests.items() if info.get('success', False)]
                    print(f"   Working API Versions: {working_versions}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Exception: {str(e)}")

if __name__ == "__main__":
    api_key = "axOJYn5328DkpXQsVcJzE6SH1TtxP4J-FGhrwj55G1I"
    
    print("🔍 Debugging API key database records...")
    print("=" * 50)
    
    # Debug the current state
    records = debug_api_key(api_key)
    
    print("\n" + "=" * 50)
    
    # Test the API key
    test_api_key_direct(api_key)
    
    print("\n" + "=" * 50)
    print("Options:")
    print("1. If you see old/incorrect Salesforce connection data above")
    print("2. Run: python3 debug_api_key.py cleanup")
    print("3. Then re-authenticate with your current Salesforce org")
    
    # Check if cleanup was requested
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        print("\n🧹 Performing database cleanup...")
        cleanup_database()
        print("\n✅ Cleanup complete! You'll need to re-authenticate.") 