#!/usr/bin/env python3
"""
Database initialization script for ForceWeaver MCP API
"""

from app import create_app, db
from app.models import Customer, APIKey, SalesforceConnection

def init_database():
    """Initialize the database with tables."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Print table information
        print("\nCreated tables:")
        print("- Customer")
        print("- APIKey")
        print("- SalesforceConnection")
        
        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database() 