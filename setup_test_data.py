#!/usr/bin/env python3
"""
ForceWeaver MCP API - Test Data Setup Script
Creates test customers and API keys for local testing
"""

import os
import sys
from datetime import datetime

# Set development environment variables if not set
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'dev-secret-key-for-local-testing'
if not os.environ.get('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:///local_test.db'
if not os.environ.get('ENCRYPTION_KEY'):
    os.environ['ENCRYPTION_KEY'] = 'ZGV2LWVuY3J5cHRpb24ta2V5LWZvci1sb2NhbC10ZXN0aW5nLTEyMzQ1Njc4OTBhYmNkZWZnaGlqa2w='

def setup_test_data():
    """Set up test data for local development"""
    
    print("🔧 ForceWeaver MCP API - Test Data Setup")
    print("=" * 50)
    
    try:
        from app import create_app, db
        from app.models import Customer, APIKey, SalesforceConnection
        from app.core.security import generate_api_key, hash_api_key, encrypt_token
        
        app = create_app()
        
        with app.app_context():
            print("📊 Initializing database...")
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create test customers
            test_customers = [
                {
                    "email": "demo@example.com",
                    "name": "Demo Customer",
                    "org_id": "00D123456789DEMO",
                    "instance_url": "https://demo.salesforce.com"
                },
                {
                    "email": "test@company.com", 
                    "name": "Test Company",
                    "org_id": "00D123456789TEST",
                    "instance_url": "https://test.salesforce.com"
                },
                {
                    "email": "developer@forceweaver.com",
                    "name": "Developer Account", 
                    "org_id": "00D123456789DEV",
                    "instance_url": "https://dev.salesforce.com"
                }
            ]
            
            created_customers = []
            
            for customer_data in test_customers:
                print(f"\n👤 Creating customer: {customer_data['email']}")
                
                # Check if customer already exists
                existing_customer = Customer.query.filter_by(email=customer_data['email']).first()
                if existing_customer:
                    print(f"   ⚠️  Customer already exists (ID: {existing_customer.id})")
                    customer = existing_customer
                else:
                    # Create new customer
                    customer = Customer(email=customer_data['email'])
                    db.session.add(customer)
                    db.session.flush()
                    print(f"   ✅ Customer created (ID: {customer.id})")
                
                # Create API key if doesn't exist
                if not customer.api_key:
                    api_key_value = generate_api_key()
                    api_key = APIKey(
                        hashed_key=hash_api_key(api_key_value),
                        customer_id=customer.id
                    )
                    db.session.add(api_key)
                    print(f"   🔑 API Key: {api_key_value}")
                else:
                    api_key_value = "[EXISTING - NOT SHOWN]"
                    print(f"   🔑 API Key: {api_key_value}")
                
                # Create Salesforce connection if doesn't exist
                if not customer.salesforce_connection:
                    encrypted_token = encrypt_token(f"mock-refresh-token-{customer.id}")
                    connection = SalesforceConnection(
                        salesforce_org_id=customer_data['org_id'],
                        encrypted_refresh_token=encrypted_token,
                        instance_url=customer_data['instance_url'],
                        customer_id=customer.id
                    )
                    db.session.add(connection)
                    print(f"   🔗 Salesforce Org: {customer_data['org_id']}")
                else:
                    print(f"   🔗 Salesforce Org: {customer.salesforce_connection.salesforce_org_id}")
                
                created_customers.append({
                    'customer': customer,
                    'email': customer_data['email'],
                    'api_key': api_key_value,
                    'org_id': customer_data['org_id'],
                    'instance_url': customer_data['instance_url']
                })
            
            # Commit all changes
            db.session.commit()
            print(f"\n✅ All test data created successfully!")
            
            # Display summary
            print("\n📋 Test Data Summary")
            print("=" * 30)
            
            for customer_info in created_customers:
                print(f"\n📧 Email: {customer_info['email']}")
                print(f"🆔 Customer ID: {customer_info['customer'].id}")
                print(f"🔑 API Key: {customer_info['api_key']}")
                print(f"🏢 Salesforce Org: {customer_info['org_id']}")
                print(f"🌐 Instance URL: {customer_info['instance_url']}")
            
            print(f"\n🚀 Ready for testing!")
            print("You can now use these API keys to test your endpoints.")
            
            return created_customers
            
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        return None

def test_endpoints():
    """Test basic endpoints with created test data"""
    
    print("\n🧪 Testing Basic Endpoints")
    print("=" * 30)
    
    try:
        import requests
        
        base_url = "http://localhost:5000"
        
        # Test health endpoint
        print("Testing /health endpoint...")
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
            print("💡 Make sure the server is running: python run.py")
        
        # Test root endpoint
        print("Testing / endpoint...")
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ Root endpoint working")
                data = response.json()
                print(f"   Service: {data.get('service')}")
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Test MCP tools endpoint
        print("Testing /api/mcp/tools endpoint...")
        try:
            response = requests.get(f"{base_url}/api/mcp/tools", timeout=5)
            if response.status_code == 200:
                print("✅ MCP tools endpoint working")
                data = response.json()
                print(f"   Available tools: {len(data.get('tools', []))}")
            else:
                print(f"❌ MCP tools endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ MCP tools endpoint error: {e}")
        
    except ImportError:
        print("⚠️  requests library not available for endpoint testing")
        print("Install with: pip install requests")

def show_test_commands():
    """Show useful test commands"""
    
    print("\n📝 Useful Test Commands")
    print("=" * 30)
    
    print("\n1. Start the development server:")
    print("   python run.py")
    
    print("\n2. Test health endpoint:")
    print("   curl http://localhost:5000/health")
    
    print("\n3. Test with API key:")
    print("   curl -H 'Authorization: Bearer YOUR_API_KEY' \\")
    print("        http://localhost:5000/api/mcp/status")
    
    print("\n4. Test health check:")
    print("   curl -X POST \\")
    print("        -H 'Authorization: Bearer YOUR_API_KEY' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        http://localhost:5000/api/mcp/health-check")
    
    print("\n5. Run unit tests:")
    print("   python test_local.py")
    
    print("\n6. Run integration tests:")
    print("   python test_integration.py")

def cleanup_test_data():
    """Clean up test data"""
    
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Remove test database files
        test_dbs = ['local_test.db', 'integration_test.db', 'test.db']
        
        for db_file in test_dbs:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"✅ Removed {db_file}")
        
        # Remove log files
        if os.path.exists('logs'):
            import shutil
            shutil.rmtree('logs')
            print("✅ Removed logs directory")
        
        print("✅ Cleanup completed!")
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")

def main():
    """Main function"""
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'setup':
            setup_test_data()
            test_endpoints()
            show_test_commands()
        elif command == 'test':
            test_endpoints()
        elif command == 'cleanup':
            cleanup_test_data()
        elif command == 'commands':
            show_test_commands()
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: setup, test, cleanup, commands")
    else:
        # Default: setup everything
        customers = setup_test_data()
        if customers:
            test_endpoints()
            show_test_commands()

if __name__ == '__main__':
    main() 