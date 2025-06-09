#!/usr/bin/env python3
"""
Check if emails from gdrive list appear in other lists
"""

import mysql.connector
import subprocess
import time

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

def get_all_lists(cursor):
    """Get all lists in the database"""
    cursor.execute("SELECT id, name FROM lists ORDER BY id")
    return cursor.fetchall()

def check_gdrive_cross_duplicates(cursor):
    """Check for gdrive list emails that appear in other lists"""
    
    print("📋 Getting all lists...")
    all_lists = get_all_lists(cursor)
    
    print("📊 All lists in database:")
    for list_id, name in all_lists:
        cursor.execute("SELECT COUNT(*) FROM subscribers WHERE list = %s", (list_id,))
        count = cursor.fetchone()[0]
        marker = " ← gdrive list" if list_id == 10 else ""
        print(f"   ID {list_id}: {name} ({count:,} subscribers){marker}")
    
    print(f"\n🔍 Checking gdrive list emails across other lists...")
    
    # Find gdrive emails that appear in other lists
    cursor.execute("""
        SELECT 
            gdrive.email,
            COUNT(other.id) as other_lists_count,
            GROUP_CONCAT(DISTINCT CONCAT(l.id, ':', l.name) SEPARATOR ' | ') as other_lists
        FROM subscribers gdrive
        LEFT JOIN subscribers other ON gdrive.email = other.email AND other.list != 10
        LEFT JOIN lists l ON other.list = l.id
        WHERE gdrive.list = 10
        GROUP BY gdrive.email
        HAVING other_lists_count > 0
        ORDER BY other_lists_count DESC
    """)
    
    cross_duplicates = cursor.fetchall()
    
    if not cross_duplicates:
        print("✅ No gdrive list emails found in other lists")
        return
    
    print(f"📊 Found {len(cross_duplicates):,} gdrive emails that also appear in other lists")
    
    # Summary by list
    print(f"\n📋 Cross-duplicate summary by target list:")
    cursor.execute("""
        SELECT 
            l.id,
            l.name,
            COUNT(DISTINCT gdrive.email) as duplicate_count
        FROM subscribers gdrive
        INNER JOIN subscribers other ON gdrive.email = other.email
        INNER JOIN lists l ON other.list = l.id
        WHERE gdrive.list = 10 AND other.list != 10
        GROUP BY l.id, l.name
        ORDER BY duplicate_count DESC
    """)
    
    list_summary = cursor.fetchall()
    
    for list_id, name, dup_count in list_summary:
        print(f"   ID {list_id}: {name} - {dup_count:,} duplicates")
    
    # Show top individual duplicates
    print(f"\n🔄 Top 20 emails with most cross-list appearances:")
    for i, (email, count, lists) in enumerate(cross_duplicates[:20], 1):
        print(f"   {i:2d}. {email} - appears in {count} other lists")
        if i <= 5:  # Show list names for top 5
            list_info = [info.split(':')[1] for info in lists.split(' | ')]
            print(f"       Lists: {', '.join(list_info)}")
    
    # Overall statistics
    total_gdrive = len(cross_duplicates) + (38397 - len(cross_duplicates))  # Assuming 38397 total from previous cleanup
    unique_to_gdrive = 38397 - len(cross_duplicates)
    
    print(f"\n📊 Cross-duplicate statistics:")
    print(f"   Total gdrive emails: 38,397")
    print(f"   Emails in other lists: {len(cross_duplicates):,}")
    print(f"   Unique to gdrive only: {unique_to_gdrive:,}")
    print(f"   Cross-duplicate percentage: {(len(cross_duplicates)/38397*100):.1f}%")

def main():
    print("🔍 Checking gdrive list cross-duplicates...")
    
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        check_gdrive_cross_duplicates(cursor)
        
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