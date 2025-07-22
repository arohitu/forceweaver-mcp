#!/usr/bin/env python3
"""
Simple database query script using raw SQL to avoid schema mismatch issues.
"""

import sqlite3
import os
from tabulate import tabulate
from datetime import datetime
import json

def connect_db():
    """Connect to the local SQLite database"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'forceweaver_local.db')
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return None
    return sqlite3.connect(db_path)

def format_datetime(dt_str):
    """Format datetime string for display"""
    if not dt_str:
        return "None"
    try:
        # Try to parse and reformat
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except:
        return dt_str

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
    cursor.execute("SELECT id, email, first_name, last_name, is_active, created_at, last_login FROM user")
    rows = cursor.fetchall()
    
    if not rows:
        print("No users found.")
        return
    
    headers = ["ID", "Email", "First Name", "Last Name", "Active", "Created At", "Last Login"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row[0],
            truncate_field(row[1], 30),
            truncate_field(row[2], 15) or "None",
            truncate_field(row[3], 15) or "None",
            "Yes" if row[4] else "No",
            format_datetime(row[5]),
            format_datetime(row[6])
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total users: {len(rows)}")

def query_customers(conn):
    """Query customers table"""
    print("\n" + "="*80)
    print("👥 CUSTOMERS TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, email, created_at FROM customer")
    rows = cursor.fetchall()
    
    if not rows:
        print("No customers found.")
        return
    
    headers = ["ID", "User ID", "Email", "Created At"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row[0],
            row[1] or "None",
            truncate_field(row[2], 30),
            format_datetime(row[3])
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total customers: {len(rows)}")

def query_api_keys(conn):
    """Query api_key table"""
    print("\n" + "="*80)
    print("🔑 API KEYS TABLE")
    print("="*80)
    
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, customer_id, hashed_key, is_active, created_at, last_used FROM api_key")
    rows = cursor.fetchall()
    
    if not rows:
        print("No API keys found.")
        return
    
    headers = ["ID", "Name", "Customer ID", "Hashed Key", "Active", "Created At", "Last Used"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row[0],
            truncate_field(row[1], 20) or "None",
            row[2],
            truncate_field(row[3], 20),
            "Yes" if row[4] else "No",
            format_datetime(row[5]),
            format_datetime(row[6])
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
               instance_url, is_sandbox, created_at, updated_at, encrypted_refresh_token
        FROM salesforce_connection
    """)
    rows = cursor.fetchall()
    
    if not rows:
        print("No Salesforce connections found.")
        return
    
    headers = ["ID", "Customer ID", "Org ID", "Org Name", "Type", "Instance URL", 
               "Sandbox", "Created At", "Updated At"]
    formatted_rows = []
    
    for row in rows:
        formatted_rows.append([
            row[0],
            row[1],
            truncate_field(row[2], 20),
            truncate_field(row[3], 20) or "None",
            truncate_field(row[4], 15) or "None",
            truncate_field(row[5], 30),
            "Yes" if row[6] else "No",
            format_datetime(row[7]),
            format_datetime(row[8])
        ])
    
    print(tabulate(formatted_rows, headers=headers, tablefmt="grid"))
    print(f"Total Salesforce connections: {len(rows)}")
    
    # Show additional details
    if rows:
        print("\n📋 Connection Details:")
        for i, row in enumerate(rows, 1):
            print(f"\n--- Connection {i} ---")
            print(f"ID: {row[0]}")
            print(f"Org ID: {row[2]}")
            print(f"Instance URL: {row[5]}")
            print(f"Refresh Token Present: {'Yes' if row[9] else 'No'}")
            print(f"Refresh Token Length: {len(row[9]) if row[9] else 0} chars")

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
            row[0],
            row[1],
            row[2],
            truncate_field(row[3], 15),
            row[4] or "None",
            row[5] or "None",
            row[6] or 0,
            row[7] or 0,
            row[8] or 0,
            row[9] or 0,
            format_datetime(row[10]),
            row[11] or "None",
            row[12] or "None"
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
            print(f"\n--- Health Check {i} (ID: {detail_row[0]}) ---")
            print(f"Execution Time: {detail_row[2]}s" if detail_row[2] else "Execution Time: Unknown")
            print(f"Triggered By: {detail_row[3] or 'Unknown'}")
            if detail_row[1]:
                try:
                    results = json.loads(detail_row[1])
                    print(f"Full Results Preview: {json.dumps(results, indent=2)[:300]}...")
                except:
                    print(f"Full Results Preview: {truncate_field(detail_row[1], 200)}")
            else:
                print("No full results stored")

def get_table_counts(conn):
    """Get record counts for all tables"""
    tables = ['user', 'customer', 'api_key', 'salesforce_connection', 'health_check_history']
    counts = {}
    
    cursor = conn.cursor()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = cursor.fetchone()[0]
    
    return counts

def main():
    """Main function"""
    print("🔍 FORCEWEAVER MCP LOCAL DATABASE CONTENTS")
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