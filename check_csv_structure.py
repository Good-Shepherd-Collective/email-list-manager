#!/usr/bin/env python3
"""
Check CSV structure for issues
"""

import csv
import pandas as pd

def check_csv_structure():
    csv_file = "/Users/codyorourke/Desktop/emails/refactored_good_emails_fixed.csv"
    
    print("🔍 Checking CSV structure...")
    
    # Check with pandas first
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Pandas loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"📋 Columns: {list(df.columns)}")
        print()
    except Exception as e:
        print(f"❌ Pandas error: {e}")
        return
    
    # Manual CSV check for problematic lines
    print("🔍 Checking for problematic lines...")
    problem_lines = 0
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if len(row) != 4:
                print(f"❌ Line {i+1}: {len(row)} fields - {row}")
                problem_lines += 1
                if problem_lines >= 10:  # Limit output
                    print("... (showing first 10 problems)")
                    break
    
    if problem_lines == 0:
        print("✅ All lines have exactly 4 fields")
    else:
        print(f"❌ Found {problem_lines} problematic lines")
    
    # Check for names with commas
    print("\n🔍 Checking for names with unescaped commas...")
    comma_names = 0
    for i, row in df.iterrows():
        name = str(row['Name'])
        if ',' in name:
            comma_names += 1
            if comma_names <= 5:  # Show first 5
                print(f"⚠️  Row {i+2}: '{name}'")
    
    if comma_names > 0:
        print(f"⚠️  Found {comma_names} names with commas")
    else:
        print("✅ No names with commas found")

if __name__ == "__main__":
    check_csv_structure()