#!/usr/bin/env python3
"""
Create Omit List Script
Combines all bad emails from sendy_emails folder into a single omit.csv file
"""

import csv
import os
from pathlib import Path
import pandas as pd

def get_sendy_emails_folder():
    """Get the sendy_emails folder path"""
    return Path(__file__).parent / "sendy_emails"

def extract_emails_from_csv(file_path):
    """Extract unique emails from a CSV file"""
    emails = set()
    try:
        df = pd.read_csv(file_path)
        if 'email' in df.columns:
            # Remove NaN values and convert to lowercase
            valid_emails = df['email'].dropna().astype(str).str.lower().str.strip()
            emails.update(valid_emails)
            print(f"✅ Extracted {len(valid_emails)} emails from {file_path.name}")
        else:
            print(f"❌ No 'email' column found in {file_path.name}")
    except Exception as err:
        print(f"❌ Error reading {file_path.name}: {err}")
    
    return emails

def main():
    """Main function to create omit list"""
    print("🚀 Creating omit list from Sendy bad contacts...")
    
    sendy_folder = get_sendy_emails_folder()
    if not sendy_folder.exists():
        print(f"❌ Sendy emails folder not found: {sendy_folder}")
        return
    
    # Find all CSV files in sendy_emails folder
    csv_files = list(sendy_folder.glob("*.csv"))
    if not csv_files:
        print(f"❌ No CSV files found in {sendy_folder}")
        return
    
    print(f"📁 Found {len(csv_files)} CSV files to process")
    
    # Collect all unique emails
    all_emails = set()
    for csv_file in csv_files:
        emails = extract_emails_from_csv(csv_file)
        all_emails.update(emails)
    
    # Remove empty strings and invalid emails
    all_emails = {email for email in all_emails if email and '@' in email and '.' in email}
    
    # Sort emails for consistent output
    sorted_emails = sorted(all_emails)
    
    # Write to omit.csv
    omit_file = Path(__file__).parent / "omit.csv"
    try:
        with open(omit_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['email'])  # Header
            for email in sorted_emails:
                writer.writerow([email])
        
        print(f"✅ Created omit.csv with {len(sorted_emails)} unique emails")
        print(f"📁 File saved to: {omit_file}")
        
    except Exception as err:
        print(f"❌ Error writing omit.csv: {err}")

if __name__ == "__main__":
    main()