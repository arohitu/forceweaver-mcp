#!/usr/bin/env python3
"""
Quick database status check
"""
import os
import sys

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app import create_app, db
from app.models import Customer, SalesforceConnection, APIKey

def check_db_status():
    app = create_app()
    
    with app.app_context():
        print("=== Database Status ===")
        
        api_keys = APIKey.query.all()
        customers = Customer.query.all()
        connections = SalesforceConnection.query.all()
        
        print(f"API Keys: {len(api_keys)}")
        print(f"Customers: {len(customers)}")
        print(f"SF Connections: {len(connections)}")
        
        if connections:
            print("\n=== Existing Connections ===")
            for conn in connections:
                print(f"Connection ID: {conn.id}")
                print(f"Org ID: {conn.salesforce_org_id}")
                print(f"Instance URL: {conn.instance_url}")
                print(f"Customer ID: {conn.customer_id}")
                print(f"API Version: {conn.preferred_api_version}")
                print("---")

if __name__ == "__main__":
    check_db_status() 