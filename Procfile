web: gunicorn -w 4 -b 0.0.0.0:$PORT "app:create_app()" --timeout 120
release: python init_db.py 
web: gunicorn app:create_app()