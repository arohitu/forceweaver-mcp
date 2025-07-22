#!/usr/bin/env python3
"""
Test script to verify MCP compliance of ForceWeaver API
"""

import requests
import json
import sys

def test_mcp_compliance(base_url="http://localhost:5000", api_key=None):
    """Test MCP compliance and functionality."""
    
    print("🧪 Testing ForceWeaver MCP API Compliance")
    print("=" * 50)
    
    # Test 1: Check MCP server identification
    print("\n1️⃣ Testing MCP Server Identification...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            if "protocol" in data and data["protocol"]["name"] == "Model Context Protocol":
                print("✅ MCP server properly identified")
                print(f"   Protocol: {data['protocol']['name']} v{data['protocol']['version']}")
            else:
                print("❌ MCP protocol not properly identified")
        else:
            print(f"❌ Server not responding: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing server identification: {e}")
    
    # Test 2: Check tools endpoint
    print("\n2️⃣ Testing Tools Discovery...")
    try:
        response = requests.get(f"{base_url}/api/mcp/tools")
        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", [])
            print(f"✅ Tools endpoint working - Found {len(tools)} tools")
            
            # Check tool schema compliance
            for tool in tools:
                print(f"   📋 Tool: {tool['name']}")
                print(f"      Description: {tool['description']}")
                if 'inputSchema' in tool:
                    properties = tool['inputSchema'].get('properties', {})
                    print(f"      Parameters: {', '.join(properties.keys()) if properties else 'None'}")
                    
        else:
            print(f"❌ Tools endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing tools endpoint: {e}")
    
    # Test 3: Check tool invocation (requires API key)
    if api_key:
        print("\n3️⃣ Testing Tool Invocation...")
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with MCP standard format
            payload = {
                "name": "revenue_cloud_health_check",
                "arguments": {
                    "check_types": ["basic_org_info"]
                }
            }
            
            response = requests.post(f"{base_url}/api/mcp/health-check", 
                                   json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "content" in data and not data.get("isError", True):
                    print("✅ Tool invocation successful (MCP format)")
                    print(f"   Response type: MCP-compliant content format")
                    print(f"   Metadata: {data.get('_meta', {})}")
                else:
                    print("❌ Tool invocation failed")
                    print(f"   Error: {data}")
            else:
                print(f"❌ Tool invocation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
            # Test with direct format for backwards compatibility
            print("\n   Testing Direct Format...")
            direct_payload = {
                "check_types": ["basic_org_info"],
                "api_version": "v64.0"
            }
            
            response = requests.post(f"{base_url}/api/mcp/health-check", 
                                   json=direct_payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if "content" in data and not data.get("isError", True):
                    print("✅ Direct format also supported")
                else:
                    print("❌ Direct format failed")
            else:
                print(f"❌ Direct format failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing tool invocation: {e}")
    else:
        print("\n3️⃣ Skipping Tool Invocation Test (no API key provided)")
        print("   To test tool invocation, provide an API key as the second argument")
    
    # Test 4: Check status endpoint
    if api_key:
        print("\n4️⃣ Testing Status Endpoint...")
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(f"{base_url}/api/mcp/status", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Status endpoint working")
                print(f"   Service Status: {data.get('service_status')}")
                print(f"   Salesforce Connected: {data.get('salesforce_connected')}")
                print(f"   API Version: {data.get('effective_api_version')}")
            else:
                print(f"❌ Status endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing status endpoint: {e}")
    else:
        print("\n4️⃣ Skipping Status Endpoint Test (no API key provided)")
    
    print("\n" + "=" * 50)
    print("🎯 MCP Compliance Test Complete!")
    
    if api_key:
        print("\n📝 Example AI Agent Usage:")
        print(f"""
# MCP Standard Format:
curl -X POST {base_url}/api/mcp/health-check \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "name": "revenue_cloud_health_check",
    "arguments": {{
      "check_types": ["basic_org_info", "sharing_model"],
      "api_version": "v64.0"
    }}
  }}'

# Direct Format (for simplicity):
curl -X POST {base_url}/api/mcp/health-check \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "check_types": ["basic_org_info", "sharing_model"],
    "api_version": "v64.0"
  }}'
        """)

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python test_mcp_compliance.py <base_url> [api_key]")
        print("Example: python test_mcp_compliance.py http://localhost:5000 your_api_key_here")
        sys.exit(1)
    
    base_url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    test_mcp_compliance(base_url, api_key)

if __name__ == "__main__":
    main() 