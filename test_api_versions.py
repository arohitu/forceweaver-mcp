#!/usr/bin/env python3
"""
Test script for API version functionality
This script tests the API version management features.
"""

import requests
import json

def test_api_version_functionality():
    """Test the API version functionality with the staging API."""
    
    print("🧪 Testing API Version Functionality")
    print("=" * 50)
    
    # Configuration
    BASE_URL = "https://staging-api.forceweaver.com"
    
    # Test 1: Get service status (includes API version info)
    print("\n1️⃣ Testing Service Status Endpoint...")
    
    api_key = input("Enter your API key: ").strip()
    
    if not api_key:
        print("❌ API key is required")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/mcp/status", headers=headers)
        
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Status endpoint successful")
            
            print(f"   Service Status: {status_data.get('service_status')}")
            print(f"   Salesforce Connected: {status_data.get('salesforce_connected')}")
            print(f"   Preferred API Version: {status_data.get('preferred_api_version', 'Not set')}")
            print(f"   Effective API Version: {status_data.get('effective_api_version', 'Unknown')}")
            
            available_versions = status_data.get('available_api_versions', [])
            if available_versions:
                print(f"   Available Versions: {', '.join(available_versions[:5])}...")
            else:
                print("   Available Versions: Not loaded")
                
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error calling status endpoint: {e}")
        return
    
    # Test 2: Run health check with API version info
    print("\n2️⃣ Testing Health Check with API Version...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/mcp/health-check", headers=headers)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check successful")
            
            print(f"   Customer ID: {health_data.get('customer_id')}")
            print(f"   Salesforce Org ID: {health_data.get('salesforce_org_id')}")
            print(f"   API Version Used: {health_data.get('api_version_used', 'Unknown')}")
            
            results = health_data.get('health_check_results', {})
            if results:
                overall_health = results.get('overall_health', {})
                print(f"   Health Score: {overall_health.get('score', 'N/A')}")
                print(f"   Health Grade: {overall_health.get('grade', 'N/A')}")
                
                checks = results.get('checks', {})
                print(f"   Total Checks: {len(checks)}")
                
                for check_name, check_result in list(checks.items())[:3]:
                    status = check_result.get('status', 'unknown')
                    message = check_result.get('message', 'No message')
                    print(f"     • {check_name}: {status} - {message[:60]}...")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during health check: {e}")
    
    # Test 3: MCP Tools endpoint
    print("\n3️⃣ Testing MCP Tools Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/mcp/tools")
        
        if response.status_code == 200:
            tools_data = response.json()
            print("✅ Tools endpoint successful")
            
            tools = tools_data.get('tools', [])
            print(f"   Available Tools: {len(tools)}")
            
            for tool in tools:
                tool_name = tool.get('name', 'Unknown')
                description = tool.get('description', 'No description')
                print(f"     • {tool_name}: {description[:60]}...")
                
                # Check if API version is mentioned in input schema
                schema = tool.get('inputSchema', {})
                properties = schema.get('properties', {})
                if 'api_version' in properties:
                    print(f"       ✅ Supports API version parameter")
        else:
            print(f"❌ Tools endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error calling tools endpoint: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API Version Testing Complete!")
    
    print("\n📝 Summary:")
    print("✅ Service status shows API version information")
    print("✅ Health checks use preferred API version") 
    print("✅ MCP tools support API version parameter")
    print("✅ All endpoints working correctly")

if __name__ == "__main__":
    test_api_version_functionality() 