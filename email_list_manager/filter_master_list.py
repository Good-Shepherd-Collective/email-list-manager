#!/usr/bin/env python3
"""
Filter Master List Script
Removes emails ending with co.il and names containing Hebrew characters from master.csv
"""

import pandas as pd
import re
from pathlib import Path

def contains_hebrew(text):
    """Check if text contains Hebrew characters"""
    if pd.isna(text) or not isinstance(text, str):
        return False
    
    # Hebrew Unicode range: \u0590-\u05FF
    hebrew_pattern = r'[\u0590-\u05FF]'
    return bool(re.search(hebrew_pattern, text))

def main():
    """Main function to filter master list"""
    print("🚀 Filtering master list to remove co.il emails and Hebrew names...")
    
    # Load master.csv
    master_file = Path(__file__).parent / "master.csv"
    if not master_file.exists():
        print(f"❌ master.csv not found")
        return
    
    try:
        df = pd.read_csv(master_file)
        initial_count = len(df)
        print(f"✅ Loaded master.csv with {initial_count} records")
        
    except Exception as err:
        print(f"❌ Error reading master.csv: {err}")
        return
    
    # Filter out emails ending with co.il
    co_il_mask = df['Email'].astype(str).str.lower().str.endswith('.co.il')
    co_il_count = co_il_mask.sum()
    df_filtered = df[~co_il_mask]
    print(f"✅ Removed {co_il_count} emails ending with .co.il")
    
    # Filter out names containing Hebrew characters
    hebrew_mask = df_filtered['Name'].apply(contains_hebrew)
    hebrew_count = hebrew_mask.sum()
    df_final = df_filtered[~hebrew_mask]
    print(f"✅ Removed {hebrew_count} names containing Hebrew characters")
    
    # Show total removed
    total_removed = initial_count - len(df_final)
    print(f"📊 Total removed: {total_removed} records")
    print(f"📈 Final count: {len(df_final)} clean emails")
    
    # Save filtered master list
    filtered_file = Path(__file__).parent / "master_filtered.csv"
    try:
        df_final.to_csv(filtered_file, index=False, encoding='utf-8')
        print(f"✅ Created master_filtered.csv with {len(df_final)} clean emails")
        print(f"📁 File saved to: {filtered_file}")
        
        # Also update the original master.csv
        df_final.to_csv(master_file, index=False, encoding='utf-8')
        print(f"✅ Updated master.csv with filtered results")
        
    except Exception as err:
        print(f"❌ Error writing filtered files: {err}")

if __name__ == "__main__":
    main()