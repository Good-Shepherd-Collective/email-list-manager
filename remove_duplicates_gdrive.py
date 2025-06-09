#!/usr/bin/env python3
"""
Remove duplicates from gdrive list (ID 10)
Keeps the first occurrence of each email, deletes the rest
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

def remove_duplicates(cursor, connection):
    """Remove duplicate emails from gdrive list"""
    
    # First, get current stats
    cursor.execute("""
        SELECT COUNT(*) as total_records,
               COUNT(DISTINCT email) as unique_emails
        FROM subscribers 
        WHERE list = 10
    """)
    
    before = cursor.fetchone()
    total_before, unique_before = before
    
    print(f"📊 Before cleanup:")
    print(f"   Total records: {total_before:,}")
    print(f"   Unique emails: {unique_before:,}")
    print(f"   Duplicates: {total_before - unique_before:,}")
    
    # Find duplicate IDs to delete (keep the lowest ID for each email)
    print("\n🔍 Finding duplicate records...")
    cursor.execute("""
        SELECT s1.id
        FROM subscribers s1
        INNER JOIN subscribers s2 ON s1.email = s2.email 
        WHERE s1.list = 10 
          AND s2.list = 10 
          AND s1.id > s2.id
    """)
    
    duplicate_ids = [row[0] for row in cursor.fetchall()]
    
    if not duplicate_ids:
        print("✅ No duplicates found to remove")
        return
    
    print(f"🗑️  Found {len(duplicate_ids):,} duplicate records to delete")
    
    # Confirm before deletion
    print(f"\n⚠️  This will DELETE {len(duplicate_ids):,} duplicate records from the gdrive list")
    print(f"   Keeping the oldest record for each email address")
    
    # Delete duplicates in batches
    batch_size = 1000
    deleted_count = 0
    
    print(f"\n🗑️  Starting deletion in batches of {batch_size}...")
    
    for i in range(0, len(duplicate_ids), batch_size):
        batch = duplicate_ids[i:i + batch_size]
        placeholders = ','.join(['%s'] * len(batch))
        
        cursor.execute(f"""
            DELETE FROM subscribers 
            WHERE id IN ({placeholders})
        """, batch)
        
        batch_deleted = cursor.rowcount
        deleted_count += batch_deleted
        
        print(f"   Deleted batch {i//batch_size + 1}: {batch_deleted:,} records (total: {deleted_count:,})")
        
        # Commit after each batch
        connection.commit()
    
    # Get final stats
    cursor.execute("""
        SELECT COUNT(*) as total_records,
               COUNT(DISTINCT email) as unique_emails
        FROM subscribers 
        WHERE list = 10
    """)
    
    after = cursor.fetchone()
    total_after, unique_after = after
    
    print(f"\n✅ Cleanup completed!")
    print(f"📊 After cleanup:")
    print(f"   Total records: {total_after:,}")
    print(f"   Unique emails: {unique_after:,}")
    print(f"   Records deleted: {deleted_count:,}")
    print(f"   Space saved: {((total_before - total_after) / total_before * 100):.1f}%")

def main():
    print("🗑️  Removing duplicates from gdrive list...")
    
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        remove_duplicates(cursor, connection)
        
        cursor.close()
        connection.close()
        
    except Exception as err:
        print(f"❌ Error: {err}")
        connection.rollback()
        
    finally:
        if ssh_process:
            print("\n🔗 Closing SSH tunnel...")
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()