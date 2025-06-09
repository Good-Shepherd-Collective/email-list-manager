#!/usr/bin/env python3
"""
Simple test upload to Sendy - just first 10 records
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

def main():
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        # Test with properly fixed CSV file
        import pandas as pd
        df = pd.read_csv("/Users/codyorourke/Desktop/emails/refactored_good_emails_fixed.csv")
        print(f"📊 Loaded {len(df)} records from fixed CSV")
        
        # Test with first 5 records
        test_records = []
        for i in range(min(5, len(df))):
            row = df.iloc[i]
            test_records.append((str(row['Name']), str(row['Email'])))
        
        print(f"🧪 Testing with {len(test_records)} records")
        
        list_id = 11  # Use existing list
        current_time = int(time.time())
        uploaded = 0
        
        for name, email in test_records:
            try:
                # Check if exists
                cursor.execute("SELECT id FROM subscribers WHERE email = %s AND list = %s", (email, list_id))
                if cursor.fetchone():
                    print(f"⚠️  {email} already exists")
                    continue
                
                # Insert
                cursor.execute("""
                    INSERT INTO subscribers (email, name, list, timestamp, join_date, confirmed, bounced, complaint, unsubscribed) 
                    VALUES (%s, %s, %s, %s, %s, 1, 0, 0, 0)
                """, (email, name, list_id, current_time, current_time))
                
                uploaded += 1
                print(f"✅ Uploaded: {name} ({email})")
                
            except Exception as err:
                print(f"❌ Error with {email}: {err}")
        
        connection.commit()
        print(f"\n🎉 Test completed! Uploaded {uploaded} records")
        
        cursor.close()
        connection.close()
        
    finally:
        if ssh_process:
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()