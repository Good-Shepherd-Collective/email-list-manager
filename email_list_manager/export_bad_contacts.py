#!/usr/bin/env python3
"""
Sendy Database Export Script
Exports bounced emails, unsubscribed contacts, and complaints to CSV files
"""

import mysql.connector
import csv
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'Cody',
    'password': 'CVCRMg12!@',
    'database': 'gsc_email_DB',
    'port': 3306,
    'charset': 'utf8mb4',
}

def get_downloads_folder():
    """Get the user's downloads folder path"""
    home = Path.home()
    downloads = home / "Downloads"
    
    # Create downloads folder if it doesn't exist
    downloads.mkdir(exist_ok=True)
    return downloads

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

def export_to_csv(cursor, query, filename, headers):
    """Execute query and export results to CSV"""
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        
        downloads_path = get_downloads_folder()
        file_path = downloads_path / filename
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(results)
        
        print(f"✅ Exported {len(results)} records to {file_path}")
        return len(results)
    
    except mysql.connector.Error as err:
        print(f"❌ Error executing query for {filename}: {err}")
        return 0
    except Exception as err:
        print(f"❌ Error writing to {filename}: {err}")
        return 0

def main():
    """Main function to export all data"""
    print("🚀 Starting Sendy database export...")
    print(f"📁 Files will be saved to: {get_downloads_folder()}")
    
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
        
        # Timestamp for unique filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV headers
        headers = ['email', 'name', 'list_name', 'date_added', 'join_date', 'custom_fields', 'status']
        
        # Define queries and filenames
        exports = [
            {
                'name': 'Hard Bounces',
                'query': '''
                    SELECT 
                        s.email, 
                        s.name, 
                        l.name as list_name,
                        FROM_UNIXTIME(s.timestamp) as date_added,
                        FROM_UNIXTIME(s.join_date) as join_date,
                        s.custom_fields,
                        'Hard Bounce' as status
                    FROM subscribers s
                    JOIN lists l ON s.list = l.id
                    WHERE s.bounced = 1
                    ORDER BY s.timestamp DESC;
                ''',
                'filename': f'hard_bounces_{timestamp}.csv'
            },
            {
                'name': 'Soft Bounces',
                'query': '''
                    SELECT 
                        s.email, 
                        s.name, 
                        l.name as list_name,
                        FROM_UNIXTIME(s.timestamp) as date_added,
                        FROM_UNIXTIME(s.join_date) as join_date,
                        s.custom_fields,
                        'Soft Bounce' as status
                    FROM subscribers s
                    JOIN lists l ON s.list = l.id
                    WHERE s.bounce_soft = 1
                    ORDER BY s.timestamp DESC;
                ''',
                'filename': f'soft_bounces_{timestamp}.csv'
            },
            {
                'name': 'Unsubscribed',
                'query': '''
                    SELECT 
                        s.email, 
                        s.name, 
                        l.name as list_name,
                        FROM_UNIXTIME(s.timestamp) as date_added,
                        FROM_UNIXTIME(s.join_date) as join_date,
                        s.custom_fields,
                        'Unsubscribed' as status
                    FROM subscribers s
                    JOIN lists l ON s.list = l.id
                    WHERE s.unsubscribed = 1
                    ORDER BY s.timestamp DESC;
                ''',
                'filename': f'unsubscribed_{timestamp}.csv'
            },
            {
                'name': 'Complaints',
                'query': '''
                    SELECT 
                        s.email, 
                        s.name, 
                        l.name as list_name,
                        FROM_UNIXTIME(s.timestamp) as date_added,
                        FROM_UNIXTIME(s.join_date) as join_date,
                        s.custom_fields,
                        'Complaint' as status
                    FROM subscribers s
                    JOIN lists l ON s.list = l.id
                    WHERE s.complaint = 1
                    ORDER BY s.timestamp DESC;
                ''',
                'filename': f'complaints_{timestamp}.csv'
            },
            {
                'name': 'Combined (All Issues)',
                'query': '''
                    SELECT 
                        s.email, 
                        s.name, 
                        l.name as list_name,
                        FROM_UNIXTIME(s.timestamp) as date_added,
                        FROM_UNIXTIME(s.join_date) as join_date,
                        s.custom_fields,
                        CASE 
                            WHEN s.bounced = 1 THEN 'Hard Bounce'
                            WHEN s.bounce_soft = 1 THEN 'Soft Bounce'
                            WHEN s.unsubscribed = 1 THEN 'Unsubscribed' 
                            WHEN s.complaint = 1 THEN 'Complaint'
                        END as status
                    FROM subscribers s
                    JOIN lists l ON s.list = l.id
                    WHERE s.bounced = 1 OR s.bounce_soft = 1 OR s.unsubscribed = 1 OR s.complaint = 1
                    ORDER BY s.timestamp DESC;
                ''',
                'filename': f'all_issues_combined_{timestamp}.csv'
            }
        ]
        
        # Export each dataset
        total_records = 0
        for export in exports:
            print(f"\n📊 Exporting {export['name']}...")
            count = export_to_csv(cursor, export['query'], export['filename'], headers)
            total_records += count
        
        # Check and export suppression list if it has data
        try:
            cursor.execute("SELECT COUNT(*) FROM suppression_list")
            suppression_count = cursor.fetchone()[0]
            
            if suppression_count > 0:
                print(f"\n📊 Exporting Suppression List ({suppression_count} records)...")
                
                # First check the structure of suppression_list
                cursor.execute("DESCRIBE suppression_list")
                suppression_columns = [column[0] for column in cursor.fetchall()]
                
                # Build query based on available columns
                suppression_query = f"SELECT {', '.join(suppression_columns)} FROM suppression_list ORDER BY id DESC"
                
                count = export_to_csv(
                    cursor, 
                    suppression_query, 
                    f'suppression_list_{timestamp}.csv',
                    suppression_columns
                )
                total_records += count
            else:
                print("\n📊 Suppression list is empty - skipping")
                
        except mysql.connector.Error as err:
            print(f"❌ Error checking suppression list: {err}")
        
        # Close connections
        cursor.close()
        connection.close()
        
        print(f"\n🎉 Export completed!")
        print(f"📈 Total records exported: {total_records}")
        print(f"📁 Files saved to: {get_downloads_folder()}")
        
    finally:
        # Close SSH tunnel
        if ssh_process:
            print("🔗 Closing SSH tunnel...")
            ssh_process.terminate()
            ssh_process.wait()

if __name__ == "__main__":
    main()