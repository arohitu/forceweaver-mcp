#!/usr/bin/env python3
"""
Query all tables from the Heroku PostgreSQL database.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_heroku_db_url():
    """Get the Heroku database URL from environment variables"""
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return database_url

def connect_db():
    """Connect to the Heroku PostgreSQL database"""
    database_url = get_heroku_db_url()
    if not database_url:
        print("❌ DATABASE_URL environment variable not found.")
        print("Please set the DATABASE_URL environment variable with your Heroku database URL.")
        return None
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        print(f"✅ Connected to Heroku database successfully!")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return "None"
    try:
        if isinstance(dt, str):
            return dt
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return str(dt)

def truncate_field(value, max_length=50):
    """Truncate long field values"""
    if value is None:
        return "None"
    str_val = str(value)
    return str_val[:max_length] + "..." if len(str_val) > max_length else str_val

def query_users(conn):
    """Query users table"""
    print("\n" + "="*80)
    print("🧑‍💼 USERS TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, email, first_name, last_name, is_active, is_verified, 
               created_at, last_login, google_id
        FROM "user" 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No users found.")
        return
    
    headers = ["ID", "Email", "First Name", "Last Name", "Active", "Verified", 
               "Created At", "Last Login", "Google ID"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row['id'],
            truncate_field(row['email'], 30),
            truncate_field(row['first_name'], 15) or "None",
            truncate_field(row['last_name'], 15) or "None",
            "Yes" if row['is_active'] else "No",
            "Yes" if row['is_verified'] else "No",
            format_datetime(row['created_at']),
            format_datetime(row['last_login']),
            truncate_field(row['google_id'], 20) or "None"
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total users: {len(rows)}")

def query_customers(conn):
    """Query customers table"""
    print("\n" + "="*80)
    print("👥 CUSTOMERS TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, email, created_at 
        FROM customer 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No customers found.")
        return
    
    headers = ["ID", "User ID", "Email", "Created At"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row['id'],
            row['user_id'] or "None",
            truncate_field(row['email'], 30),
            format_datetime(row['created_at'])
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total customers: {len(rows)}")

def query_api_keys(conn):
    """Query api_key table"""
    print("\n" + "="*80)
    print("🔑 API KEYS TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, customer_id, hashed_key, is_active, created_at, last_used 
        FROM api_key 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No API keys found.")
        return
    
    headers = ["ID", "Name", "Customer ID", "Hashed Key", "Active", "Created At", "Last Used"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row['id'],
            truncate_field(row['name'], 20) or "None",
            row['customer_id'],
            truncate_field(row['hashed_key'], 20),
            "Yes" if row['is_active'] else "No",
            format_datetime(row['created_at']),
            format_datetime(row['last_used'])
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total API keys: {len(rows)}")

def query_salesforce_connections(conn):
    """Query salesforce_connection table"""
    print("\n" + "="*80)
    print("⚡ SALESFORCE CONNECTIONS TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, customer_id, salesforce_org_id, org_name, org_type, 
               instance_url, is_sandbox, created_at, updated_at, 
               preferred_api_version, available_api_versions,
               encrypted_refresh_token IS NOT NULL as has_refresh_token
        FROM salesforce_connection 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No Salesforce connections found.")
        return
    
    headers = ["ID", "Customer ID", "Org ID", "Org Name", "Type", "Instance URL", 
               "Sandbox", "API Version", "Created At", "Updated At"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row['id'],
            row['customer_id'],
            truncate_field(row['salesforce_org_id'], 20),
            truncate_field(row['org_name'], 20) or "None",
            truncate_field(row['org_type'], 15) or "None",
            truncate_field(row['instance_url'], 30),
            "Yes" if row['is_sandbox'] else "No",
            row['preferred_api_version'] or "None",
            format_datetime(row['created_at']),
            format_datetime(row['updated_at'])
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total Salesforce connections: {len(rows)}")
    
    # Show additional details
    if rows:
        print("\n📋 Connection Details:")
        for i, row in enumerate(rows, 1):
            print(f"\n--- Connection {i} ---")
            print(f"ID: {row['id']}")
            print(f"Customer ID: {row['customer_id']}")
            print(f"Org ID: {row['salesforce_org_id']}")
            print(f"Instance URL: {row['instance_url']}")
            print(f"Has Refresh Token: {'Yes' if row['has_refresh_token'] else 'No'}")
            print(f"Preferred API Version: {row['preferred_api_version'] or 'None'}")
            if row['available_api_versions']:
                try:
                    versions = json.loads(row['available_api_versions'])
                    if isinstance(versions, list) and len(versions) > 0:
                        print(f"Available API Versions: {', '.join(versions[:3])}{'...' if len(versions) > 3 else ''}")
                    else:
                        print(f"Available API Versions: {truncate_field(str(versions), 50)}")
                except:
                    print(f"Available API Versions: {truncate_field(row['available_api_versions'], 50)}")
            else:
                print("Available API Versions: None")

def query_health_check_history(conn):
    """Query health_check_history table"""
    print("\n" + "="*80)
    print("📊 HEALTH CHECK HISTORY TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, user_id, customer_id, salesforce_org_id, overall_health_grade, 
               overall_health_score, checks_performed, checks_passed, checks_failed, 
               checks_warnings, created_at, triggered_by, execution_time_seconds
        FROM health_check_history 
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No health check history found.")
        return
    
    headers = ["ID", "User ID", "Customer ID", "Org ID", "Grade", "Score", "Total", 
               "Passed", "Failed", "Warnings", "Created At", "Triggered By", "Time (s)"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row['id'],
            row['user_id'],
            row['customer_id'],
            truncate_field(row['salesforce_org_id'], 15),
            row['overall_health_grade'] or "None",
            row['overall_health_score'] or "None",
            row['checks_performed'] or 0,
            row['checks_passed'] or 0,
            row['checks_failed'] or 0,
            row['checks_warnings'] or 0,
            format_datetime(row['created_at']),
            row['triggered_by'] or "None",
            row['execution_time_seconds'] or "None"
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total health check records: {len(rows)}")
    
    # Show full results for recent records
    if rows:
        print("\n📋 Recent Health Check Details:")
        cursor.execute("""
            SELECT id, full_results, execution_time_seconds, triggered_by 
            FROM health_check_history 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        detail_rows = cursor.fetchall()
        
        for i, detail_row in enumerate(detail_rows, 1):
            print(f"\n--- Health Check {i} (ID: {detail_row['id']}) ---")
            print(f"Execution Time: {detail_row['execution_time_seconds']}s" if detail_row['execution_time_seconds'] else "Execution Time: Unknown")
            print(f"Triggered By: {detail_row['triggered_by'] or 'Unknown'}")
            if detail_row['full_results']:
                try:
                    results = json.loads(detail_row['full_results'])
                    print(f"Full Results Preview: {json.dumps(results, indent=2)[:300]}...")
                except:
                    print(f"Full Results Preview: {truncate_field(detail_row['full_results'], 200)}")
            else:
                print("No full results stored")

def get_table_counts(conn):
    """Get record counts for all tables"""
    tables = ['user', 'customer', 'api_key', 'salesforce_connection', 'health_check_history']
    counts = {}
    
    cursor = conn.cursor()
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
            counts[table] = cursor.fetchone()[0]
        except Exception as e:
            print(f"Warning: Could not count records in {table}: {e}")
            counts[table] = "Error"
    
    return counts

def main():
    """Main function"""
    print("🔍 FORCEWEAVER MCP HEROKU DATABASE CONTENTS")
    print("="*80)
    print(f"Query executed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Connect to database
    conn = connect_db()
    if not conn:
        return
    
    try:
        # Show overview
        counts = get_table_counts(conn)
        print("\n📊 Database Overview:")
        print("-" * 30)
        for table, count in counts.items():
            print(f"{table.replace('_', ' ').title()}: {count} records")
        
        # Query all tables
        query_users(conn)
        query_customers(conn) 
        query_api_keys(conn)
        query_salesforce_connections(conn)
        query_health_check_history(conn)
        
        print("\n" + "="*80)
        print("✅ Database query completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 