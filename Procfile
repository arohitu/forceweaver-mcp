web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()" --timeout 120
release: echo "No database migrations needed for MCP server"
worker: python server.py