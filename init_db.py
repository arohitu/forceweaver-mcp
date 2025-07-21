#!/usr/bin/env python3
"""
Database initialization script for ForceWeaver MCP API
"""

from app import create_app, db
from app.models import User, Customer, APIKey, SalesforceConnection, HealthCheckHistory

def init_database():
    """Initialize the database with tables."""
    app = create_app()
    
    with app.app_context():
        try:
            # Import all models to ensure they're registered
            from app.models import User, Customer, APIKey, SalesforceConnection, HealthCheckHistory
            
            # Create all tables
            db.create_all()
            print("Database tables created successfully!")
            
            # Check which tables actually exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("\nActual database tables:")
            for table in sorted(tables):
                print(f"- {table}")
            
            # Check customer table columns
            if 'customer' in tables:
                print("\nCustomer table columns:")
                columns = inspector.get_columns('customer')
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            
            # Check if user_id column exists in customer table
            if 'customer' in tables:
                columns = inspector.get_columns('customer')
                column_names = [col['name'] for col in columns]
                if 'user_id' not in column_names:
                    print("\n⚠️  WARNING: customer table missing user_id column!")
                    print("   This needs to be added via database migration.")
                    
                    # Try to add the column
                    try:
                        print("   Attempting to add user_id column...")
                        from sqlalchemy import text
                        with db.engine.connect() as conn:
                            conn.execute(text('ALTER TABLE customer ADD COLUMN user_id INTEGER;'))
                            conn.commit()
                        print("   ✅ user_id column added successfully!")
                    except Exception as e:
                        print(f"   ❌ Failed to add user_id column: {e}")
                        print("   Will attempt alternative migration method...")
                else:
                    print("\n✅ customer table has user_id column")
            
            print("\nDatabase initialization complete!")
            
        except Exception as e:
            print(f"Error during database initialization: {e}")
            raise

if __name__ == '__main__':
    init_database() 