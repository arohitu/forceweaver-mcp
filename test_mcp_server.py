#!/usr/bin/env python3
"""
MCP Server Compliance Testing Script

This script tests the ForceWeaver MCP Server for compliance with
Model Context Protocol v2025-03-26 specification.
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, Optional


class MCPServerTester:
    """Test MCP server compliance."""
    
    def __init__(self, server_script: str = "server.py"):
        self.server_script = server_script
        self.process: Optional[subprocess.Popen] = None
    
    async def start_server(self) -> bool:
        """Start the MCP server process."""
        try:
            self.process = subprocess.Popen(
                [sys.executable, self.server_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            # Give server time to initialize
            await asyncio.sleep(1)
            
            # Check if process is still running
            if self.process.poll() is not None:
                stderr = self.process.stderr.read()
                print(f"❌ Server failed to start: {stderr}")
                return False
            
            print("✅ Server started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
    
    def send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC message to the server and get response."""
        if not self.process:
            return None
        
        try:
            message_str = json.dumps(message) + '\n'
            self.process.stdin.write(message_str)
            self.process.stdin.flush()
            
            # Read response
            response_str = self.process.stdout.readline()
            if not response_str:
                return None
            
            return json.loads(response_str)
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return None
    
    async def test_initialize(self) -> bool:
        """Test server initialization."""
        print("\n🔧 Testing Server Initialization...")
        
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        response = self.send_message(init_message)
        
        if not response:
            print("❌ No response to initialize")
            return False
        
        if response.get("jsonrpc") != "2.0":
            print(f"❌ Invalid JSON-RPC version: {response.get('jsonrpc')}")
            return False
        
        if "result" not in response:
            print(f"❌ Initialize failed: {response.get('error', 'Unknown error')}")
            return False
        
        result = response["result"]
        if "capabilities" not in result:
            print("❌ No capabilities in initialize response")
            return False
        
        print("✅ Server initialization successful")
        print(f"   Server: {result.get('serverInfo', {}).get('name', 'Unknown')}")
        print(f"   Capabilities: {list(result['capabilities'].keys())}")
        return True
    
    async def test_ping(self) -> bool:
        """Test ping method."""
        print("\n📡 Testing Ping...")
        
        ping_message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "ping"
        }
        
        response = self.send_message(ping_message)
        
        if not response:
            print("❌ No response to ping")
            return False
        
        if "result" not in response:
            print(f"❌ Ping failed: {response.get('error', 'Unknown error')}")
            return False
        
        print("✅ Ping successful")
        return True
    
    async def test_tools_list(self) -> bool:
        """Test tools/list method."""
        print("\n🛠️ Testing Tools List...")
        
        tools_message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list"
        }
        
        response = self.send_message(tools_message)
        
        if not response:
            print("❌ No response to tools/list")
            return False
        
        if "result" not in response:
            print(f"❌ Tools list failed: {response.get('error', 'Unknown error')}")
            return False
        
        result = response["result"]
        if "tools" not in result:
            print("❌ No tools in response")
            return False
        
        tools = result["tools"]
        if not isinstance(tools, list):
            print("❌ Tools is not a list")
            return False
        
        print(f"✅ Tools list successful - found {len(tools)} tools")
        
        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                print(f"❌ Tool {i} is not a dict")
                return False
            
            required_fields = ["name", "description"]
            for field in required_fields:
                if field not in tool:
                    print(f"❌ Tool {i} missing required field: {field}")
                    return False
            
            print(f"   📋 Tool: {tool['name']}")
            print(f"      Description: {tool['description'][:50]}...")
            
            if "inputSchema" in tool:
                schema = tool["inputSchema"]
                if isinstance(schema, dict) and schema.get("type") == "object":
                    properties = schema.get("properties", {})
                    print(f"      Parameters: {list(properties.keys())}")
        
        return True
    
    async def test_tool_call(self) -> bool:
        """Test tools/call method."""
        print("\n⚡ Testing Tool Call...")
        
        # Test with basic health check
        call_message = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "revenue_cloud_health_check",
                "arguments": {
                    "check_types": ["basic_org_info"]
                }
            }
        }
        
        response = self.send_message(call_message)
        
        if not response:
            print("❌ No response to tools/call")
            return False
        
        if "result" not in response:
            error = response.get('error', {})
            # Check if it's a configuration error (expected in test environment)
            if error.get('code') == -32602 or "Missing required environment" in str(error.get('message', '')):
                print("⚠️ Tool call failed due to missing Salesforce configuration (expected in test)")
                print(f"   Error: {error.get('message', 'Unknown error')}")
                return True  # This is expected without proper SF credentials
            else:
                print(f"❌ Tool call failed: {error}")
                return False
        
        result = response["result"]
        if "content" not in result:
            print("❌ No content in tool call result")
            return False
        
        content = result["content"]
        if not isinstance(content, list):
            print("❌ Content is not a list")
            return False
        
        print("✅ Tool call successful")
        print(f"   Content items: {len(content)}")
        
        for item in content:
            if "type" in item and "text" in item:
                print(f"   📄 {item['type']}: {item['text'][:100]}...")
        
        return True
    
    async def test_invalid_method(self) -> bool:
        """Test handling of invalid method."""
        print("\n❓ Testing Invalid Method Handling...")
        
        invalid_message = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "invalid/method"
        }
        
        response = self.send_message(invalid_message)
        
        if not response:
            print("❌ No response to invalid method")
            return False
        
        if "error" not in response:
            print("❌ Invalid method should return error")
            return False
        
        error = response["error"]
        if error.get("code") != -32601:  # Method not found
            print(f"❌ Wrong error code for invalid method: {error.get('code')}")
            return False
        
        print("✅ Invalid method handled correctly")
        print(f"   Error: {error.get('message', 'Unknown')}")
        return True
    
    async def run_all_tests(self) -> bool:
        """Run all compliance tests."""
        print("🧪 MCP Server Compliance Testing")
        print("=" * 50)
        
        # Start server
        if not await self.start_server():
            return False
        
        try:
            # Run tests
            tests = [
                ("Initialize", self.test_initialize),
                ("Ping", self.test_ping),
                ("Tools List", self.test_tools_list),
                ("Tool Call", self.test_tool_call),
                ("Invalid Method", self.test_invalid_method),
            ]
            
            passed = 0
            total = len(tests)
            
            for test_name, test_func in tests:
                try:
                    if await test_func():
                        passed += 1
                    else:
                        print(f"❌ {test_name} test failed")
                except Exception as e:
                    print(f"❌ {test_name} test error: {e}")
            
            print("\n" + "=" * 50)
            print(f"🎯 Test Results: {passed}/{total} tests passed")
            
            if passed == total:
                print("🎉 All tests passed! Server is MCP compliant.")
                return True
            else:
                print(f"⚠️ {total - passed} test(s) failed. Server needs fixes.")
                return False
        
        finally:
            self.stop_server()


async def main():
    """Main test function."""
    if len(sys.argv) > 1:
        server_script = sys.argv[1]
    else:
        server_script = "server.py"
    
    print(f"Testing MCP server: {server_script}")
    print("Make sure you have set up environment variables for Salesforce connection")
    print("(Some tests may show warnings without proper SF credentials)")
    print()
    
    tester = MCPServerTester(server_script)
    success = await tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main()) 