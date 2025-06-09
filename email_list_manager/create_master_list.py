#!/usr/bin/env python3
"""
Create Master List Script
Creates master.csv by removing all emails from omit.csv from consolidated_email_list.csv
"""

import csv
import pandas as pd
from pathlib import Path

def load_omit_emails():
    """Load emails from omit.csv"""
    omit_file = Path(__file__).parent / "omit.csv"
    if not omit_file.exists():
        print(f"❌ omit.csv not found. Please run create_omit_list.py first.")
        return None
    
    try:
        df = pd.read_csv(omit_file)
        if 'email' not in df.columns:
            print(f"❌ No 'email' column found in omit.csv")
            return None
        
        # Convert to lowercase and strip whitespace for consistent matching
        omit_emails = set(df['email'].astype(str).str.lower().str.strip())
        print(f"✅ Loaded {len(omit_emails)} emails to omit")
        return omit_emails
        
    except Exception as err:
        print(f"❌ Error reading omit.csv: {err}")
        return None

def load_consolidated_emails():
    """Load emails from consolidated_email_list.csv"""
    consolidated_file = Path(__file__).parent / "consolidated_email_list.csv"
    if not consolidated_file.exists():
        print(f"❌ consolidated_email_list.csv not found")
        return None
    
    try:
        df = pd.read_csv(consolidated_file)
        print(f"✅ Loaded consolidated list with {len(df)} total records")
        print(f"📊 Columns: {list(df.columns)}")
        return df
        
    except Exception as err:
        print(f"❌ Error reading consolidated_email_list.csv: {err}")
        return None

def create_master_list(consolidated_df, omit_emails):
    """Create master list by filtering out omit emails"""
    
    # Find the email column (could be 'email', 'Email', etc.)
    email_column = None
    for col in consolidated_df.columns:
        if 'email' in col.lower():
            email_column = col
            break
    
    if email_column is None:
        print(f"❌ No email column found in consolidated list")
        return None
    
    print(f"📧 Using email column: {email_column}")
    
    # Create normalized email column for comparison
    consolidated_df['normalized_email'] = consolidated_df[email_column].astype(str).str.lower().str.strip()
    
    # Filter out emails that are in the omit list
    initial_count = len(consolidated_df)
    master_df = consolidated_df[~consolidated_df['normalized_email'].isin(omit_emails)]
    
    # Remove the normalized column before saving
    master_df = master_df.drop('normalized_email', axis=1)
    
    removed_count = initial_count - len(master_df)
    print(f"✅ Filtered out {removed_count} bad emails")
    print(f"📈 Master list contains {len(master_df)} clean emails")
    
    return master_df

def main():
    """Main function to create master list"""
    print("🚀 Creating master email list...")
    
    # Load omit emails
    omit_emails = load_omit_emails()
    if omit_emails is None:
        return
    
    # Load consolidated emails
    consolidated_df = load_consolidated_emails()
    if consolidated_df is None:
        return
    
    # Create master list
    master_df = create_master_list(consolidated_df, omit_emails)
    if master_df is None:
        return
    
    # Save master list
    master_file = Path(__file__).parent / "master.csv"
    try:
        master_df.to_csv(master_file, index=False, encoding='utf-8')
        print(f"✅ Created master.csv with {len(master_df)} clean emails")
        print(f"📁 File saved to: {master_file}")
        
    except Exception as err:
        print(f"❌ Error writing master.csv: {err}")

if __name__ == "__main__":
    main()