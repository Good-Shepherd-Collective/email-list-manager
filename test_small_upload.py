#!/usr/bin/env python3
"""
Small batch test upload - first 100 records only
"""

import mysql.connector
import subprocess
import time
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

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
    print("🧪 Testing small batch upload (100 records)...")
    
    # Setup SSH tunnel
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        # Connect to database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        print("✅ Connected to database")
        
        # Load CSV and take first 100 records
        csv_file = Path(__file__).parent / "refactored_good_emails_fixed.csv"
        df = pd.read_csv(csv_file)
        test_df = df.head(100)  # First 100 records only
        
        print(f"📊 Testing with {len(test_df)} records from CSV")
        print(f"📋 Sample records:")
        for i in range(3):
            print(f"   {i+1}. {test_df.iloc[i]['Name']} ({test_df.iloc[i]['Email']})")
        
        # Upload test batch
        list_id = 11
        current_time = int(time.time())
        uploaded = 0
        duplicates = 0
        errors = 0
        
        print("\n📤 Starting test upload...")
        
        for index, row in test_df.iterrows():
            email = str(row['Email']).strip().lower()
            name = str(row['Name']).strip()
            
            if not email or '@' not in email:
                errors += 1
                continue
            
            try:
                # Check if exists
                cursor.execute("SELECT id FROM subscribers WHERE email = %s AND list = %s", (email, list_id))
                if cursor.fetchone():
                    duplicates += 1
                    continue
                
                # Insert
                cursor.execute("""
                    INSERT INTO subscribers (email, name, list, timestamp, join_date, confirmed, bounced, complaint, unsubscribed) 
                    VALUES (%s, %s, %s, %s, %s, 1, 0, 0, 0)
                """, (email, name, list_id, current_time, current_time))
                
                uploaded += 1
                
                # Progress every 10 records
                if (index + 1) % 10 == 0:
                    print(f"   📊 Processed {index + 1}/100 - ✅{uploaded} uploaded, 🔄{duplicates} duplicates, ❌{errors} errors")
                
            except Exception as err:
                print(f"❌ Error with {email}: {err}")
                errors += 1
        
        # Commit changes
        connection.commit()
        
        print(f"\n🎉 Test batch completed!")
        print(f"   ✅ Uploaded: {uploaded}")
        print(f"   🔄 Duplicates: {duplicates}")  
        print(f"   ❌ Errors: {errors}")
        
        if uploaded > 0:
            print("\n✅ Test successful! Ready for full upload.")
        else:
            print("\n⚠️  No new records uploaded - might all be duplicates.")
        
        cursor.close()
        connection.close()
        
    except Exception as err:
        print(f"❌ Error: {err}")
        
    finally:
        if ssh_process:
            print("🔗 Closing SSH tunnel...")
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()