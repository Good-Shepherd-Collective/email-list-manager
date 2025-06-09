#!/usr/bin/env python3
"""
Check unique emails in gdrive list only
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
            return ssh_process
        return None
    except Exception as err:
        print(f"❌ SSH tunnel error: {err}")
        return None

def main():
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check gdrive list (ID 10)
        cursor.execute("""
            SELECT COUNT(*) as total_records,
                   COUNT(DISTINCT email) as unique_emails
            FROM subscribers 
            WHERE list = 10
        """)
        
        result = cursor.fetchone()
        total_records, unique_emails = result
        
        print(f"📊 'gdrive list' (ID 10) Statistics:")
        print(f"   Total records: {total_records:,}")
        print(f"   Unique emails: {unique_emails:,}")
        
        if total_records > unique_emails:
            duplicates = total_records - unique_emails
            print(f"   Duplicates: {duplicates:,}")
        else:
            print("   ✅ No duplicates")
        
        cursor.close()
        connection.close()
        
    except Exception as err:
        print(f"❌ Error: {err}")
        
    finally:
        if ssh_process:
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()