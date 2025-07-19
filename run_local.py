#!/usr/bin/env python3
"""
ForceWeaver MCP API - Local Development Server
Runs the API locally with test data for development and testing
"""

import os
import sys
import subprocess
import signal
import time

def setup_environment():
    """Setup local development environment"""
    print("🔧 Setting up local development environment...")
    
    # Set development environment variables if not already set
    env_vars = {
        'SECRET_KEY': 'dev-secret-key-for-local-development',
        'DATABASE_URL': 'sqlite:///local_dev.db',
        'ENCRYPTION_KEY': 'ZGV2LWVuY3J5cHRpb24ta2V5LWZvci1sb2NhbC1kZXZlbG9wbWVudC0xMjM0NTY3ODkwYWJjZGVmZw==',
        'SALESFORCE_CLIENT_ID': 'dev-client-id',
        'SALESFORCE_CLIENT_SECRET': 'dev-client-secret',
        'SALESFORCE_REDIRECT_URI': 'http://localhost:5000/api/auth/salesforce/callback',
        'FLASK_ENV': 'development',
        'FLASK_DEBUG': '1'
    }
    
    for key, value in env_vars.items():
        if not os.environ.get(key):
            os.environ[key] = value
    
    print("✅ Environment variables set")

def initialize_database():
    """Initialize database with test data"""
    print("📊 Initializing database with test data...")
    
    try:
        # Run the initialization script
        result = subprocess.run([sys.executable, 'init_db.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database initialized")
        else:
            print(f"⚠️  Database initialization warning: {result.stderr}")
        
        # Create test data
        result = subprocess.run([sys.executable, 'setup_test_data.py', 'setup'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test data created")
            # Extract API keys from output
            lines = result.stdout.split('\n')
            api_keys = []
            for line in lines:
                if '🔑 API Key:' in line and 'EXISTING' not in line:
                    api_key = line.split('🔑 API Key: ')[1].strip()
                    api_keys.append(api_key)
            
            if api_keys:
                print("\n🔑 Available API Keys for testing:")
                for i, key in enumerate(api_keys[:3], 1):
                    print(f"   {i}. {key}")
        else:
            print(f"⚠️  Test data creation warning: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False
    
    return True

def show_startup_info():
    """Show startup information and testing instructions"""
    print("\n" + "=" * 60)
    print("🚀 ForceWeaver MCP API - Local Development Server")
    print("=" * 60)
    print("📍 Server URL: http://localhost:5000")
    print("📖 API Documentation: http://localhost:5000/")
    print("🏥 Health Check: http://localhost:5000/health")
    print("🔧 MCP Tools: http://localhost:5000/api/mcp/tools")
    
    print("\n📋 Available Endpoints:")
    print("   GET  /                          - API information")
    print("   GET  /health                    - Health check")
    print("   GET  /api/mcp/tools             - MCP tool definitions")
    print("   GET  /api/mcp/status            - Service status (auth required)")
    print("   POST /api/mcp/health-check      - Revenue Cloud health check (auth required)")
    print("   GET  /api/auth/salesforce/initiate - Start OAuth flow")
    print("   GET  /api/auth/customer/status  - Check customer status")
    
    print("\n🧪 Testing Commands:")
    print("   # Basic endpoints")
    print("   curl http://localhost:5000/health")
    print("   curl http://localhost:5000/api/mcp/tools")
    print("")
    print("   # Authenticated endpoints (use API key from above)")
    print("   curl -H 'Authorization: Bearer YOUR_API_KEY' \\")
    print("        http://localhost:5000/api/mcp/status")
    print("")
    print("   curl -X POST \\")
    print("        -H 'Authorization: Bearer YOUR_API_KEY' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        http://localhost:5000/api/mcp/health-check")
    
    print("\n📚 Additional Testing:")
    print("   python test_local.py            - Run unit tests")
    print("   python test_integration.py      - Run integration tests")
    print("   python run_all_tests.py         - Run all tests")
    
    print("\n⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)

def run_server():
    """Run the development server"""
    print("🚀 Starting development server...")
    
    try:
        # Import and run the Flask app
        from app import create_app
        
        app = create_app()
        
        # Run the server
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False
    
    return True

def cleanup_on_exit():
    """Cleanup function for graceful shutdown"""
    print("\n🧹 Cleaning up...")
    
    # Kill any remaining processes on port 5000
    try:
        subprocess.run(['lsof', '-ti:5000'], capture_output=True)
    except:
        pass
    
    print("✅ Cleanup completed")

def main():
    """Main function to run the local development server"""
    
    try:
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\n\n🛑 Received shutdown signal")
            cleanup_on_exit()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Check if dependencies are installed
        try:
            import flask
            import sqlalchemy
            import cryptography
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("💡 Install dependencies with: pip install -r requirements.txt")
            return False
        
        # Setup environment
        setup_environment()
        
        # Initialize database and test data
        if not initialize_database():
            print("❌ Database initialization failed")
            return False
        
        # Show startup information
        show_startup_info()
        
        # Run the server
        run_server()
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        cleanup_on_exit()
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 