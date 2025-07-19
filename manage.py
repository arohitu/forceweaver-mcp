#!/usr/bin/env python3
"""
Database management script for ForceWeaver MCP API
"""

from flask_migrate import Migrate
from app import create_app, db
import click

app = create_app()
migrate = Migrate(app, db)

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")

if __name__ == '__main__':
    app.cli() 