#!/usr/bin/env python3
"""
Clean Special Characters Script
Removes problematic characters that could cause database issues
"""

import pandas as pd
import re
from pathlib import Path

def clean_name(name):
    """Clean problematic characters from names"""
    if pd.isna(name) or not isinstance(name, str):
        return name
    
    # Remove corrupted encoding characters
    name = re.sub(r'[ª�•]', '', name)  # Remove specific problematic chars
    
    # Remove leading apostrophes and quotes
    name = re.sub(r'^[\'"`]+', '', name)
    
    # Replace problematic punctuation
    name = name.replace('¿', '')  # Remove inverted question mark
    name = name.replace('…', '...')  # Replace ellipsis
    
    # Clean up multiple spaces and trim
    name = re.sub(r'\s+', ' ', name).strip()
    
    # If name becomes empty or too short, return "Unknown"
    if len(name) < 2:
        return "Unknown"
    
    return name

def clean_location(location):
    """Clean location fields"""
    if pd.isna(location) or not isinstance(location, str):
        return ""
    
    # Clean similar issues in state/location fields
    location = re.sub(r'[ª�•]', '', location)
    location = re.sub(r'^[\'"`]+', '', location)
    location = re.sub(r'\s+', ' ', location).strip()
    
    return location

def clean_csv_characters():
    """Clean special characters from CSV file"""
    input_file = Path(__file__).parent / "refactored_good_emails_fixed.csv"
    output_file = Path(__file__).parent / "refactored_good_emails_clean_chars.csv"
    
    print("🧹 Cleaning special characters from CSV...")
    print(f"📂 Input: {input_file}")
    print(f"📂 Output: {output_file}")
    
    try:
        # Load CSV
        df = pd.read_csv(input_file)
        print(f"📊 Loaded {len(df)} records")
        
        # Track changes
        name_changes = 0
        state_changes = 0
        
        # Clean names
        print("🔧 Cleaning names...")
        original_names = df['Name'].copy()
        df['Name'] = df['Name'].apply(clean_name)
        
        # Count changes
        for i, (original, cleaned) in enumerate(zip(original_names, df['Name'])):
            if str(original) != str(cleaned):
                name_changes += 1
                if name_changes <= 10:  # Show first 10 changes
                    print(f"   '{original}' → '{cleaned}'")
        
        # Clean state field
        print("🔧 Cleaning state field...")
        original_states = df['state'].copy()
        df['state'] = df['state'].apply(clean_location)
        
        # Count state changes
        for original, cleaned in zip(original_states, df['state']):
            if str(original) != str(cleaned):
                state_changes += 1
        
        # Clean organization field
        print("🔧 Cleaning organization field...")
        df['organization'] = df['organization'].apply(clean_location)
        
        # Replace 'nan' strings with empty strings
        df = df.replace('nan', '')
        
        # Save cleaned CSV
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ Cleaning completed!")
        print(f"📊 Records processed: {len(df)}")
        print(f"🔧 Names cleaned: {name_changes}")
        print(f"🔧 States cleaned: {state_changes}")
        print(f"📁 Clean file saved: {output_file}")
        
        # Show sample of cleaned data
        print(f"\n📋 Sample of cleaned data:")
        print(df.head(5).to_string(index=False))
        
        return True
        
    except Exception as err:
        print(f"❌ Error cleaning characters: {err}")
        return False

if __name__ == "__main__":
    clean_csv_characters()