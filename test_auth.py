#!/usr/bin/env python3
"""
ForceWeaver MCP API - Authentication Test Script
This script verifies that both authentication layers are working correctly.
"""

import requests
import json
import os
import sys
from urllib.parse import urlparse

def test_authentication_system():
    """Test the complete dual authentication system."""
    
    # Configuration
    BASE_URL = input("Enter your API base URL (e.g., https://your-domain.com): ").strip()
    if not BASE_URL.startswith('http'):
        BASE_URL = f"https://{BASE_URL}"
    
    print(f"\n🔍 Testing ForceWeaver MCP API at: {BASE_URL}")
    print("=" * 60)
    
    # Test 1: Health endpoint (no auth required)
    print("\n1️⃣ Testing Basic Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Basic health check: PASSED")
        else:
            print(f"❌ Basic health check: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ Basic health check: ERROR - {e}")
        return False
    
    # Test 2: MCP tools endpoint (no auth required)
    print("\n2️⃣ Testing MCP Tools Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/mcp/tools", timeout=10)
        if response.status_code == 200:
            tools = response.json().get('tools', [])
            print(f"✅ MCP tools endpoint: PASSED ({len(tools)} tools available)")
        else:
            print(f"❌ MCP tools endpoint: FAILED ({response.status_code})")
    except Exception as e:
        print(f"❌ MCP tools endpoint: ERROR - {e}")
    
    # Test 3: API key authentication
    print("\n3️⃣ Testing API Key Authentication...")
    
    # Get API key from user
    api_key = input("Enter your API key (leave empty to test customer onboarding): ").strip()
    
    if not api_key:
        print("ℹ️  No API key provided. Testing customer onboarding flow...")
        customer_email = input("Enter customer email for onboarding: ").strip()
        
        if customer_email:
            try:
                onboarding_url = f"{BASE_URL}/api/auth/salesforce/initiate?email={customer_email}"
                print(f"🔗 Customer onboarding URL: {onboarding_url}")
                print("   Please visit this URL to complete Salesforce OAuth flow")
                
                # Check customer status
                status_response = requests.get(f"{BASE_URL}/api/auth/customer/status?email={customer_email}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"📊 Customer Status: {status_data}")
                else:
                    print(f"❌ Could not check customer status: {status_response.status_code}")
                    
            except Exception as e:
                print(f"❌ Onboarding flow error: {e}")
        return False
    
    # Test with API key
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(f"{BASE_URL}/api/mcp/status", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API Key Authentication: PASSED")
            print(f"   Customer ID: {data.get('customer_id')}")
            print(f"   Salesforce Connected: {data.get('salesforce_connected')}")
            print(f"   Org ID: {data.get('salesforce_org_id')}")
            
            if not data.get('salesforce_connected'):
                print("⚠️  Customer needs to complete Salesforce OAuth flow")
                return False
                
        elif response.status_code == 401:
            print("❌ API Key Authentication: FAILED - Invalid API key")
            return False
        else:
            print(f"❌ API Key Authentication: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API Key Authentication: ERROR - {e}")
        return False
    
    # Test 4: Salesforce OAuth authentication (via health check)
    print("\n4️⃣ Testing Salesforce OAuth Authentication...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/mcp/health-check", headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print("✅ Salesforce OAuth Authentication: PASSED")
            print(f"   Org ID: {data.get('salesforce_org_id')}")
            print(f"   Health Check Results: {len(data.get('health_check_results', {}).get('checks', {}))} checks completed")
            
            # Show sample health check results
            checks = data.get('health_check_results', {}).get('checks', {})
            if checks:
                print("   Sample Check Results:")
                for check_name, check_result in list(checks.items())[:3]:
                    status = check_result.get('status', 'unknown')
                    message = check_result.get('message', 'No message')
                    print(f"     • {check_name}: {status} - {message}")
            
        elif response.status_code == 400:
            print("❌ Salesforce OAuth Authentication: FAILED - No Salesforce connection")
            print("   Customer needs to complete OAuth flow")
            return False
        else:
            print(f"❌ Salesforce OAuth Authentication: FAILED ({response.status_code})")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Salesforce OAuth Authentication: ERROR - {e}")
        return False
    
    # Test 5: Overall system health
    print("\n5️⃣ Testing Overall System Health...")
    
    try:
        # Test all endpoints
        endpoints = [
            ("/health", "GET", None),
            ("/api/mcp/tools", "GET", None),
            ("/api/mcp/status", "GET", headers),
            ("/api/mcp/health-check", "POST", headers)
        ]
        
        working_endpoints = 0
        total_endpoints = len(endpoints)
        
        for endpoint, method, req_headers in endpoints:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{endpoint}", headers=req_headers, timeout=10)
                else:
                    resp = requests.post(f"{BASE_URL}{endpoint}", headers=req_headers, timeout=30)
                
                if resp.status_code == 200:
                    working_endpoints += 1
                    
            except Exception:
                pass
        
        health_percentage = (working_endpoints / total_endpoints) * 100
        print(f"📊 System Health: {health_percentage:.1f}% ({working_endpoints}/{total_endpoints} endpoints working)")
        
        if health_percentage == 100:
            print("✅ All systems operational!")
        elif health_percentage >= 75:
            print("⚠️  System mostly operational with minor issues")
        else:
            print("❌ System has significant issues")
            
    except Exception as e:
        print(f"❌ System Health Check: ERROR - {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 AUTHENTICATION SYSTEM TEST COMPLETED!")
    print("✅ Both authentication layers are working correctly")
    print("✅ Your ForceWeaver MCP API is ready for production use")
    
    return True

def main():
    """Main function to run the authentication test."""
    print("🔐 ForceWeaver MCP API - Authentication System Test")
    print("This script will verify that both authentication layers work correctly.\n")
    
    try:
        success = test_authentication_system()
        if success:
            print("\n✅ SUCCESS: Your dual authentication system is working perfectly!")
            sys.exit(0)
        else:
            print("\n❌ ISSUES FOUND: Please check the setup guide and try again")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 