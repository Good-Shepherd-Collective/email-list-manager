#!/usr/bin/env python3
"""
Properly fix CSV formatting issues
Re-create the CSV with proper quoting for all fields
"""

import csv
import pandas as pd
from pathlib import Path

def fix_csv_properly():
    """Read CSV with pandas and write back with proper CSV formatting"""
    
    input_file = Path(__file__).parent / "refactored_good_emails.csv"
    output_file = Path(__file__).parent / "refactored_good_emails_fixed.csv"
    
    print("🚀 Fixing CSV formatting...")
    print(f"📂 Input: {input_file}")
    print(f"📂 Output: {output_file}")
    
    try:
        # Read with pandas, handling the problematic formatting
        df = pd.read_csv(input_file, on_bad_lines='skip', encoding='utf-8')
        print(f"✅ Successfully loaded {len(df)} records")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Check for any problematic data
        issues_found = 0
        for idx, row in df.iterrows():
            name = str(row.get('Name', ''))
            if ',' in name and not (name.startswith('"') and name.endswith('"')):
                if issues_found < 5:  # Show first 5 issues
                    print(f"🔧 Found problematic name: '{name}'")
                issues_found += 1
        
        if issues_found > 0:
            print(f"⚠️  Found {issues_found} names with unescaped commas")
        
        # Write back with proper CSV formatting
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            
            # Write header
            writer.writerow(['Name', 'Email', 'state', 'organization'])
            
            # Write data rows
            for _, row in df.iterrows():
                writer.writerow([
                    str(row.get('Name', '')),
                    str(row.get('Email', '')),
                    str(row.get('state', '')),
                    str(row.get('organization', ''))
                ])
        
        print(f"✅ Fixed CSV created with {len(df)} records")
        print(f"📁 Saved to: {output_file}")
        
        # Verify the fix by checking line 100
        with open(output_file, 'r') as f:
            lines = f.readlines()
            if len(lines) > 100:
                print(f"🔍 Line 100 preview: {lines[100].strip()}")
        
        return True
        
    except Exception as err:
        print(f"❌ Error fixing CSV: {err}")
        return False

if __name__ == "__main__":
    fix_csv_properly()