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
            
            # Check and fix customer table schema
            if 'customer' in tables:
                columns = inspector.get_columns('customer')
                column_names = [col['name'] for col in columns]
                
                # Define expected columns for Customer model
                expected_columns = {
                    'user_id': 'INTEGER',
                    'created_at': 'TIMESTAMP'
                }
                
                missing_columns = []
                for col_name, col_type in expected_columns.items():
                    if col_name not in column_names:
                        missing_columns.append((col_name, col_type))
                
                if missing_columns:
                    print(f"\n⚠️  WARNING: customer table missing {len(missing_columns)} column(s)!")
                    for col_name, col_type in missing_columns:
                        print(f"   - {col_name} ({col_type})")
                    
                    # Add missing columns one by one
                    from sqlalchemy import text
                    for col_name, col_type in missing_columns:
                        try:
                            print(f"   Attempting to add {col_name} column...")
                            with db.engine.connect() as conn:
                                if col_name == 'created_at':
                                    # Add timestamp column with default value
                                    conn.execute(text(f'ALTER TABLE customer ADD COLUMN {col_name} TIMESTAMP DEFAULT NOW();'))
                                else:
                                    # Add regular column
                                    conn.execute(text(f'ALTER TABLE customer ADD COLUMN {col_name} {col_type};'))
                                conn.commit()
                            print(f"   ✅ {col_name} column added successfully!")
                        except Exception as e:
                            print(f"   ❌ Failed to add {col_name} column: {e}")
                else:
                    print("\n✅ customer table has all required columns")
            
            # Check and fix api_key table schema  
            if 'api_key' in tables:
                columns = inspector.get_columns('api_key')
                column_names = [col['name'] for col in columns]
                
                expected_columns = {
                    'created_at': 'TIMESTAMP',
                    'last_used': 'TIMESTAMP',
                    'is_active': 'BOOLEAN',
                    'name': 'VARCHAR(100)'
                }
                
                missing_columns = []
                for col_name, col_type in expected_columns.items():
                    if col_name not in column_names:
                        missing_columns.append((col_name, col_type))
                
                if missing_columns:
                    print(f"\n⚠️  WARNING: api_key table missing {len(missing_columns)} column(s)!")
                    from sqlalchemy import text
                    for col_name, col_type in missing_columns:
                        try:
                            print(f"   Adding {col_name} column...")
                            with db.engine.connect() as conn:
                                if col_name == 'created_at':
                                    conn.execute(text(f'ALTER TABLE api_key ADD COLUMN {col_name} TIMESTAMP DEFAULT NOW();'))
                                elif col_name == 'last_used':
                                    conn.execute(text(f'ALTER TABLE api_key ADD COLUMN {col_name} TIMESTAMP;'))
                                elif col_name == 'is_active':
                                    conn.execute(text(f'ALTER TABLE api_key ADD COLUMN {col_name} BOOLEAN DEFAULT TRUE;'))
                                elif col_name == 'name':
                                    conn.execute(text(f'ALTER TABLE api_key ADD COLUMN {col_name} VARCHAR(100) DEFAULT \'Default API Key\';'))
                                else:
                                    conn.execute(text(f'ALTER TABLE api_key ADD COLUMN {col_name} {col_type};'))
                                conn.commit()
                            print(f"   ✅ {col_name} column added!")
                        except Exception as e:
                            print(f"   ❌ Failed to add {col_name}: {e}")
                else:
                    print("\n✅ api_key table schema is complete")
            
            # Check and fix salesforce_connection table schema
            if 'salesforce_connection' in tables:
                columns = inspector.get_columns('salesforce_connection')
                column_names = [col['name'] for col in columns]
                
                expected_columns = {
                    'created_at': 'TIMESTAMP',
                    'updated_at': 'TIMESTAMP',
                    'org_name': 'VARCHAR(255)',
                    'org_type': 'VARCHAR(50)',
                    'is_sandbox': 'BOOLEAN'
                }
                
                missing_columns = []
                for col_name, col_type in expected_columns.items():
                    if col_name not in column_names:
                        missing_columns.append((col_name, col_type))
                
                if missing_columns:
                    print(f"\n⚠️  WARNING: salesforce_connection table missing {len(missing_columns)} column(s)!")
                    from sqlalchemy import text
                    for col_name, col_type in missing_columns:
                        try:
                            print(f"   Adding {col_name} column...")
                            with db.engine.connect() as conn:
                                if col_name in ['created_at', 'updated_at']:
                                    conn.execute(text(f'ALTER TABLE salesforce_connection ADD COLUMN {col_name} TIMESTAMP DEFAULT NOW();'))
                                elif col_name == 'is_sandbox':
                                    conn.execute(text(f'ALTER TABLE salesforce_connection ADD COLUMN {col_name} BOOLEAN DEFAULT FALSE;'))
                                else:
                                    conn.execute(text(f'ALTER TABLE salesforce_connection ADD COLUMN {col_name} {col_type};'))
                                conn.commit()
                            print(f"   ✅ {col_name} column added!")
                        except Exception as e:
                            print(f"   ❌ Failed to add {col_name}: {e}")
                else:
                    print("\n✅ salesforce_connection table schema is complete")
            
            print("\nDatabase schema migration complete!")
            
        except Exception as e:
            print(f"Error during database initialization: {e}")
            raise

if __name__ == '__main__':
    init_database() 