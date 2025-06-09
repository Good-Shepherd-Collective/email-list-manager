#!/usr/bin/env python3
"""
Debug upload script - test each component
"""

import subprocess
import time
from pathlib import Path

def test_ssh_connection():
    """Test SSH tunnel setup"""
    print("🔗 Testing SSH tunnel...")
    try:
        ssh_process = subprocess.Popen([
            'ssh', '-N', '-L', '3306:localhost:3306', 'amazon-sendy'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        if ssh_process.poll() is None:
            print("✅ SSH tunnel established")
            ssh_process.terminate()
            ssh_process.wait()
            return True
        else:
            stdout, stderr = ssh_process.communicate()
            print(f"❌ SSH tunnel failed: {stderr.decode()}")
            return False
            
    except Exception as err:
        print(f"❌ SSH error: {err}")
        return False

def test_csv_file():
    """Test CSV file access"""
    print("📄 Testing CSV file...")
    csv_file = Path(__file__).parent / "refactored_good_emails_fixed.csv"
    
    if csv_file.exists():
        print(f"✅ CSV file exists: {csv_file}")
        print(f"📊 File size: {csv_file.stat().st_size:,} bytes")
        
        # Test reading first few lines
        with open(csv_file, 'r') as f:
            lines = f.readlines()[:5]
            print(f"📋 First 5 lines:")
            for i, line in enumerate(lines):
                print(f"   {i+1}: {line.strip()}")
        return True
    else:
        print(f"❌ CSV file not found: {csv_file}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🗄️  Testing database connection...")
    try:
        import mysql.connector
        
        # SSH tunnel first
        ssh_process = subprocess.Popen([
            'ssh', '-N', '-L', '3306:localhost:3306', 'amazon-sendy'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        
        if ssh_process.poll() is not None:
            print("❌ SSH tunnel failed")
            return False
        
        # Database connection
        DB_CONFIG = {
            'host': '127.0.0.1',
            'user': 'Cody',
            'password': 'CVCRMg12!@',
            'database': 'gsc_email_DB',
            'port': 3306,
            'charset': 'utf8mb4',
        }
        
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM lists WHERE id = 11")
        result = cursor.fetchone()
        print(f"✅ Database connected. List 11 exists: {result[0] > 0}")
        
        cursor.close()
        connection.close()
        ssh_process.terminate()
        ssh_process.wait()
        
        return True
        
    except Exception as err:
        print(f"❌ Database error: {err}")
        if 'ssh_process' in locals():
            ssh_process.terminate()
            ssh_process.wait()
        return False

def main():
    print("🧪 Running upload diagnostics...\n")
    
    ssh_ok = test_ssh_connection()
    print()
    
    csv_ok = test_csv_file()
    print()
    
    db_ok = test_database_connection()
    print()
    
    if ssh_ok and csv_ok and db_ok:
        print("✅ All components working! Upload should succeed.")
    else:
        print("❌ Found issues that need to be fixed.")

if __name__ == "__main__":
    main()