#!/usr/bin/env python3
"""
Upload to Sendy Script
Uploads refactored email list to a Sendy list via SSH tunnel to database
"""

import mysql.connector
import csv
import subprocess
import time
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# Database configuration (same as export_bad_contacts.py)
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
    print("🔗 Setting up SSH tunnel to amazon-sendy...")
    try:
        # Start SSH tunnel in background
        ssh_process = subprocess.Popen([
            'ssh', '-N', '-L', '3306:localhost:3306', 'amazon-sendy'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give tunnel time to establish
        time.sleep(3)
        
        # Check if tunnel is working
        if ssh_process.poll() is None:
            print("✅ SSH tunnel established")
            return ssh_process
        else:
            stdout, stderr = ssh_process.communicate()
            print(f"❌ SSH tunnel failed: {stderr.decode()}")
            return None
            
    except Exception as err:
        print(f"❌ Error setting up SSH tunnel: {err}")
        return None

def connect_to_database():
    """Connect to the MariaDB database"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected to database successfully")
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Error connecting to database: {err}")
        return None

def get_or_create_list(cursor, list_name, app_id=1):
    """Get existing list or create new one"""
    try:
        # Check if list exists
        cursor.execute("SELECT id, name FROM lists WHERE name = %s", (list_name,))
        result = cursor.fetchone()
        
        if result:
            list_id = result[0]
            print(f"✅ Found existing list: {list_name} (ID: {list_id})")
            return list_id
        else:
            # First, check the actual structure of the lists table
            cursor.execute("DESCRIBE lists")
            columns = [column[0] for column in cursor.fetchall()]
            print(f"📋 Available columns in lists table: {columns}")
            
            # Create new list with basic required fields
            cursor.execute("""
                INSERT INTO lists (name, app, userID) 
                VALUES (%s, %s, 1)
            """, (list_name, app_id))
            
            list_id = cursor.lastrowid
            print(f"✅ Created new list: {list_name} (ID: {list_id})")
            return list_id
            
    except mysql.connector.Error as err:
        print(f"❌ Error with list operations: {err}")
        return None

def load_checkpoint(checkpoint_file):
    """Load checkpoint data"""
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            return json.load(f)
    return {'last_processed': -1, 'uploaded_count': 0, 'duplicate_count': 0, 'error_count': 0}

def save_checkpoint(checkpoint_file, data):
    """Save checkpoint data"""
    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)

def upload_subscribers(cursor, connection, csv_file, list_id, batch_size=500):
    """Upload subscribers from CSV to Sendy list with batching and checkpoints"""
    try:
        # Set up checkpoint file
        checkpoint_file = csv_file.parent / f"upload_checkpoint_{list_id}.json"
        checkpoint = load_checkpoint(checkpoint_file)
        
        # Load CSV
        df = pd.read_csv(csv_file)
        print(f"📊 Loaded {len(df)} records from CSV")
        print(f"📋 Columns found: {list(df.columns)}")
        
        if 'Email' not in df.columns:
            print("❌ CSV must have 'Email' column")
            return 0
        
        # Resume from checkpoint
        start_index = checkpoint['last_processed'] + 1
        if start_index > 0:
            print(f"🔄 Resuming from record {start_index + 1} (checkpoint found)")
            print(f"📊 Previous progress: ✅{checkpoint['uploaded_count']} uploaded, 🔄{checkpoint['duplicate_count']} duplicates, ❌{checkpoint['error_count']} errors")
        
        # Initialize counters from checkpoint
        uploaded_count = checkpoint['uploaded_count']
        duplicate_count = checkpoint['duplicate_count'] 
        error_count = checkpoint['error_count']
        current_time = int(time.time())
        
        print("📤 Starting batch upload...")
        print(f"📊 Target list ID: {list_id}")
        print(f"📦 Batch size: {batch_size}")
        print(f"📋 Records to process: {len(df) - start_index}")
        if start_index == 0:
            print(f"📋 First few emails to upload:")
            for i in range(min(3, len(df))):
                print(f"   {i+1}. {df.iloc[i]['Name']} ({df.iloc[i]['Email']})")
        print()
        
        batch_count = 0
        
        for index, row in df.iterrows():
            # Skip already processed records
            if index < start_index:
                continue
            email = str(row.get('Email', '')).strip().lower()
            name = str(row.get('Name', '')).strip()
            
            # Skip empty emails
            if not email or '@' not in email:
                error_count += 1
                continue
            
            try:
            
                # Check if email already exists in this list
                cursor.execute("""
                    SELECT id FROM subscribers 
                    WHERE email = %s AND list = %s
                """, (email, list_id))
                
                if cursor.fetchone():
                    duplicate_count += 1
                    continue
                
                # Insert new subscriber
                cursor.execute("""
                    INSERT INTO subscribers (
                        email, 
                        name, 
                        list, 
                        timestamp, 
                        join_date,
                        confirmed,
                        bounced,
                        complaint,
                        unsubscribed
                    ) VALUES (%s, %s, %s, %s, %s, 1, 0, 0, 0)
                """, (email, name, list_id, current_time, current_time))
                
                uploaded_count += 1
                
                batch_count += 1
                
                # Batch commit and checkpoint save
                if batch_count >= batch_size:
                    connection.commit()
                    
                    # Save checkpoint
                    checkpoint_data = {
                        'last_processed': index,
                        'uploaded_count': uploaded_count,
                        'duplicate_count': duplicate_count,
                        'error_count': error_count,
                        'timestamp': datetime.now().isoformat()
                    }
                    save_checkpoint(checkpoint_file, checkpoint_data)
                    
                    print(f"✅ Batch {(index - start_index + 1) // batch_size} completed: Processed {index + 1}/{len(df)} records")
                    print(f"   📊 Stats: ✅{uploaded_count} uploaded, 🔄{duplicate_count} duplicates, ❌{error_count} errors")
                    print(f"   💾 Checkpoint saved at record {index + 1}")
                    
                    batch_count = 0
                    
            except mysql.connector.Error as err:
                print(f"❌ Error inserting {email}: {err}")
                error_count += 1
                continue
        
        # Final commit and checkpoint
        connection.commit()
        
        # Save final checkpoint
        final_checkpoint = {
            'last_processed': len(df) - 1,
            'uploaded_count': uploaded_count,
            'duplicate_count': duplicate_count, 
            'error_count': error_count,
            'timestamp': datetime.now().isoformat(),
            'completed': True
        }
        save_checkpoint(checkpoint_file, final_checkpoint)
        
        print(f"✅ Upload completed!")
        print(f"   📈 Successfully uploaded: {uploaded_count}")
        print(f"   🔄 Duplicates skipped: {duplicate_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   💾 Final checkpoint saved")
        
        return uploaded_count
        
    except Exception as err:
        print(f"❌ Error uploading subscribers: {err}")
        return 0

def main():
    """Main function to upload emails to Sendy"""
    print("🚀 Starting Sendy email upload...")
    
    # Configuration
    csv_file = Path(__file__).parent.parent / "refactored_good_emails_clean_chars.csv"
    list_name = "GDrive Refactored List"  # Change this to your desired list name
    
    # Check if CSV file exists
    if not csv_file.exists():
        print(f"❌ CSV file not found: {csv_file}")
        print("Please ensure refactored_good_emails.csv exists in the parent directory")
        return
    
    # Setup SSH tunnel
    ssh_process = setup_ssh_tunnel()
    if not ssh_process:
        return
    
    try:
        # Connect to database
        connection = connect_to_database()
        if not connection:
            return
        
        cursor = connection.cursor()
        
        # Get or create list
        list_id = get_or_create_list(cursor, list_name)
        if not list_id:
            return
        
        # Upload subscribers
        uploaded_count = upload_subscribers(cursor, connection, csv_file, list_id)
        
        # Commit changes
        connection.commit()
        
        # Close connections
        cursor.close()
        connection.close()
        
        print(f"\n🎉 Upload completed!")
        print(f"📋 List: {list_name} (ID: {list_id})")
        print(f"📈 Total uploaded: {uploaded_count} subscribers")
        
    except Exception as err:
        print(f"❌ Unexpected error: {err}")
        
    finally:
        # Close SSH tunnel
        if ssh_process:
            print("🔗 Closing SSH tunnel...")
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()