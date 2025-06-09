#!/usr/bin/env python3
"""
Check duplicates in Sendy lists
"""

import mysql.connector
import subprocess
import time
from collections import Counter

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'Cody',
    'password': 'CVCRMg12!@',
    'database': 'gsc_email_DB',
    'port': 3306,
    'charset': 'utf8mb4',
}

def setup_ssh_tunnel():
    """Setup SSH tunnel to Amazon Sendy server"""
    print("🔗 Setting up SSH tunnel...")
    try:
        ssh_process = subprocess.Popen([
            'ssh', '-N', '-L', '3306:localhost:3306', 'amazon-sendy'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)
        if ssh_process.poll() is None:
            print("✅ SSH tunnel established")
            return ssh_process
        return None
    except Exception as err:
        print(f"❌ SSH tunnel error: {err}")
        return None

def find_list_id(cursor, list_name):
    """Find list ID by name"""
    cursor.execute("SELECT id, name FROM lists WHERE name LIKE %s", (f"%{list_name}%",))
    results = cursor.fetchall()
    
    if not results:
        print(f"❌ No lists found matching '{list_name}'")
        return None
    
    print(f"📋 Found lists matching '{list_name}':")
    for list_id, name in results:
        print(f"   ID {list_id}: {name}")
    
    return results[0][0] if len(results) == 1 else None

def check_duplicates_in_list(cursor, list_id, list_name):
    """Check for duplicate emails in a specific list"""
    print(f"\n🔍 Checking duplicates in list: {list_name} (ID: {list_id})")
    
    # Get all emails in the list
    cursor.execute("""
        SELECT email, COUNT(*) as count
        FROM subscribers 
        WHERE list = %s
        GROUP BY email
        ORDER BY count DESC, email
    """, (list_id,))
    
    results = cursor.fetchall()
    
    if not results:
        print("❌ No subscribers found in this list")
        return
    
    total_subscribers = sum(count for email, count in results)
    unique_emails = len(results)
    duplicates = [email for email, count in results if count > 1]
    duplicate_count = len(duplicates)
    total_duplicate_records = sum(count - 1 for email, count in results if count > 1)
    
    print(f"📊 List Statistics:")
    print(f"   Total subscriber records: {total_subscribers}")
    print(f"   Unique email addresses: {unique_emails}")
    print(f"   Duplicate email addresses: {duplicate_count}")
    print(f"   Extra duplicate records: {total_duplicate_records}")
    
    if duplicate_count > 0:
        print(f"\n🔄 Top duplicates:")
        for email, count in results[:10]:
            if count > 1:
                print(f"   {email}: {count} times")
        
        if duplicate_count > 10:
            print(f"   ... and {duplicate_count - 10} more duplicates")

def check_cross_list_duplicates(cursor):
    """Check for emails that appear in multiple lists"""
    print(f"\n🔍 Checking cross-list duplicates...")
    
    cursor.execute("""
        SELECT 
            s.email,
            COUNT(DISTINCT s.list) as list_count,
            GROUP_CONCAT(DISTINCT l.name) as list_names
        FROM subscribers s
        JOIN lists l ON s.list = l.id
        GROUP BY s.email
        HAVING list_count > 1
        ORDER BY list_count DESC
        LIMIT 20
    """)
    
    results = cursor.fetchall()
    
    if results:
        print(f"📊 Found {len(results)} emails in multiple lists:")
        for email, list_count, list_names in results[:10]:
            print(f"   {email}: in {list_count} lists ({list_names})")
    else:
        print("✅ No emails found in multiple lists")

def main():
    print("🔍 Checking for duplicates in Sendy database...")
    
    # Setup SSH tunnel
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        # Connect to database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        # Find gdrive list
        list_id = find_list_id(cursor, "gdrive")
        
        if list_id:
            check_duplicates_in_list(cursor, list_id, "gdrive list")
        
        # Also check the current upload list
        upload_list_id = find_list_id(cursor, "GDrive Refactored List")
        if upload_list_id and upload_list_id != list_id:
            check_duplicates_in_list(cursor, upload_list_id, "GDrive Refactored List")
        
        # Check cross-list duplicates
        check_cross_list_duplicates(cursor)
        
        cursor.close()
        connection.close()
        
    except Exception as err:
        print(f"❌ Error: {err}")
        
    finally:
        if ssh_process:
            print("\n🔗 Closing SSH tunnel...")
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()