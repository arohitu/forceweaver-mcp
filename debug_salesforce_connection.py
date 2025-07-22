#!/usr/bin/env python3
"""
Debug script for Salesforce connection issues.
This script helps diagnose why the health check is failing.
"""

import os
import sys
from app import create_app, db
from app.models import Customer, SalesforceConnection
from app.core.security import decrypt_token
from config import Config
import requests

def debug_salesforce_connections():
    """Debug all Salesforce connections in the database."""
    
    app = create_app()
    with app.app_context():
        print("🔍 Debugging Salesforce Connections")
        print("=" * 50)
        
        # Check environment configuration
        print(f"\n📋 Environment Configuration:")
        print(f"   SALESFORCE_CLIENT_ID: {Config.SALESFORCE_CLIENT_ID[:10] if Config.SALESFORCE_CLIENT_ID else 'NOT SET'}...")
        print(f"   SALESFORCE_CLIENT_SECRET: {'SET' if Config.SALESFORCE_CLIENT_SECRET else 'NOT SET'}")
        print(f"   ENCRYPTION_KEY: {'SET' if Config.ENCRYPTION_KEY else 'NOT SET'}")
        
        # Get all customers with Salesforce connections
        customers = Customer.query.join(SalesforceConnection).all()
        
        if not customers:
            print(f"\n❌ No customers with Salesforce connections found")
            return
            
        print(f"\n👥 Found {len(customers)} customers with Salesforce connections")
        
        for customer in customers:
            connection = customer.salesforce_connection
            print(f"\n🔗 Customer: {customer.email}")
            print(f"   Customer ID: {customer.id}")
            print(f"   Org ID: {connection.salesforce_org_id}")
            print(f"   Instance URL: {connection.instance_url}")
            print(f"   Is Sandbox: {connection.is_sandbox}")
            print(f"   Org Name: {connection.org_name}")
            print(f"   Org Type: {connection.org_type}")
            print(f"   Connected: {connection.created_at}")
            
            # Try to decrypt the refresh token
            try:
                decrypted_token = decrypt_token(connection.encrypted_refresh_token)
                if decrypted_token:
                    print(f"   ✅ Refresh token decrypted successfully")
                    print(f"   Token length: {len(decrypted_token)}")
                    
                    # Try to refresh the token manually
                    print(f"   🔄 Attempting token refresh...")
                    test_token_refresh(connection, decrypted_token)
                else:
                    print(f"   ❌ Failed to decrypt refresh token")
                    
            except Exception as e:
                print(f"   ❌ Error decrypting token: {e}")

def test_token_refresh(connection, refresh_token):
    """Test token refresh for a specific connection."""
    try:
        # Determine the correct token URL
        if connection.is_sandbox:
            token_url = "https://test.salesforce.com/services/oauth2/token"
        else:
            token_url = "https://login.salesforce.com/services/oauth2/token"
            
        print(f"   Token URL: {token_url}")
        
        refresh_data = {
            'grant_type': 'refresh_token',
            'client_id': Config.SALESFORCE_CLIENT_ID,
            'client_secret': Config.SALESFORCE_CLIENT_SECRET,
            'refresh_token': refresh_token
        }
        
        print(f"   Sending refresh request...")
        response = requests.post(token_url, data=refresh_data)
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print(f"   ✅ Token refresh successful!")
            print(f"   New access token length: {len(token_data.get('access_token', ''))}")
        else:
            print(f"   ❌ Token refresh failed!")
            print(f"   Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"   Error: {error_data['error']}")
                if 'error_description' in error_data:
                    print(f"   Description: {error_data['error_description']}")
            except:
                pass
                
    except Exception as e:
        print(f"   ❌ Exception during token refresh: {e}")

if __name__ == "__main__":
    debug_salesforce_connections() 