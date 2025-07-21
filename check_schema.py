#!/usr/bin/env python3
"""
Check Database Schema - Customer Table
"""

from app import create_app, db
from sqlalchemy import inspect

def check_schema():
    app = create_app()
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            # Check customer table columns
            print("=== CURRENT CUSTOMER TABLE SCHEMA ===")
            if inspector.has_table('customer'):
                columns = inspector.get_columns('customer')
                for col in columns:
                    print(f"  {col['name']}: {col['type']}")
            else:
                print("  customer table does not exist!")
            
            # Check user table columns
            print("\n=== CURRENT USER TABLE SCHEMA ===")
            if inspector.has_table('user'):
                columns = inspector.get_columns('user') 
                for col in columns:
                    print(f"  {col['name']}: {col['type']}")
            else:
                print("  user table does not exist!")
                
            # Check all tables
            print("\n=== ALL TABLES ===")
            tables = inspector.get_table_names()
            for table in tables:
                print(f"  - {table}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_schema() 