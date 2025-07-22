#!/usr/bin/env python3
"""
Quick test script to verify staging deployment
"""

import requests
import json
import sys

def test_post_deployment(base_url="https://staging-api.forceweaver.com"):
    """Test key endpoints after deployment."""
    
    print("🧪 Testing Post-Deployment Status")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1️⃣ Testing Root Endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            if "protocol" in data:
                print("✅ Root endpoint working - MCP identified")
                print(f"   Protocol: {data['protocol']['name']} v{data['protocol']['version']}")
            else:
                print("❌ Root endpoint missing protocol info")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 2: Tools endpoint
    print("\n2️⃣ Testing Tools Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/mcp/tools")
        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", [])
            print(f"✅ Tools endpoint working - Found {len(tools)} tools")
            if tools:
                tool = tools[0]
                print(f"   Tool: {tool['name']}")
                print(f"   Schema: {len(tool.get('inputSchema', {}).get('properties', {}))} parameters")
        else:
            print(f"❌ Tools endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Tools endpoint error: {e}")
    
    # Test 3: Health check without auth (should get auth error, not 500)
    print("\n3️⃣ Testing Health Check Endpoint (no auth)...")
    try:
        response = requests.post(f"{base_url}/api/mcp/health-check", 
                               json={"check_types": ["basic_org_info"]})
        if response.status_code == 401:
            print("✅ Health check endpoint working - Returns auth error as expected")
        elif response.status_code == 500:
            print("❌ Health check still returning 500 - deployment may not be complete")
            print(f"   Response: {response.text}")
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Health check endpoint error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Post-Deployment Test Complete!")
    print("\n💡 Next Steps:")
    print("   - If all tests pass: API is ready for AI agents")
    print("   - If 500 errors persist: Check deployment logs")
    print("   - Test with API key for full functionality")

if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://staging-api.forceweaver.com"
    test_post_deployment(base_url) 