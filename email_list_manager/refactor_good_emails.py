#!/usr/bin/env python3
"""
Refactor Good Emails Script
Converts good_emails.csv to match sample.csv structure with cleaned names
"""

import pandas as pd
import re
from pathlib import Path

def extract_name_from_email(email):
    """Extract potential name from email address"""
    if pd.isna(email) or not isinstance(email, str):
        return "Unknown"
    
    # Get the part before @
    local_part = email.split('@')[0] if '@' in email else email
    
    # Remove common separators and numbers
    name_part = re.sub(r'[._\-\d]+', ' ', local_part)
    
    # Capitalize each word
    name_part = ' '.join(word.capitalize() for word in name_part.split() if word)
    
    return name_part if name_part else "Unknown"

def clean_name(name):
    """Clean and fix problematic names"""
    if pd.isna(name) or not isinstance(name, str):
        return None
    
    name = str(name).strip()
    
    # Skip obvious bad names
    bad_patterns = [
        r'^#NAME\?',           # Excel errors
        r'^\d{2}-\d{2}-\d{4}', # Dates
        r'^\d+\s*nan',         # Numbers with nan
        r'^[.,\s]*$',          # Just punctuation
        r'nan',                # Contains 'nan'
        r'^\d+$',              # Just numbers
    ]
    
    for pattern in bad_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            return None
    
    # Clean duplicated names like "(Alice) Louise (Alice) Louise"
    # Remove content in parentheses and duplicates
    name = re.sub(r'\([^)]*\)', '', name)  # Remove parentheses content
    words = name.split()
    
    # Remove duplicated consecutive words
    cleaned_words = []
    for word in words:
        if not cleaned_words or word.lower() != cleaned_words[-1].lower():
            cleaned_words.append(word.title())
    
    cleaned_name = ' '.join(cleaned_words).strip()
    
    # Must have at least 2 characters and contain letters
    if len(cleaned_name) < 2 or not re.search(r'[a-zA-Z]', cleaned_name):
        return None
    
    return cleaned_name

def refactor_good_emails():
    """Main function to refactor good_emails.csv"""
    print("🚀 Refactoring good_emails.csv to match sample.csv structure...")
    
    # Load good_emails.csv
    input_file = Path(__file__).parent / "good_emails.csv"
    if not input_file.exists():
        print(f"❌ good_emails.csv not found")
        return
    
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df)} records from good_emails.csv")
        print(f"📊 Original columns: {list(df.columns)}")
        
    except Exception as err:
        print(f"❌ Error reading good_emails.csv: {err}")
        return
    
    # Create new dataframe with sample.csv structure
    refactored_df = pd.DataFrame()
    
    # Process Name column first (to match sample order)
    print("🔧 Processing names...")
    names = []
    cleaned_count = 0
    extracted_count = 0
    
    for idx, row in df.iterrows():
        original_name = row.get('Name', '')
        email = row.get('Email', '')
        
        # Try to clean the existing name first
        cleaned_name = clean_name(original_name)
        
        if cleaned_name:
            names.append(cleaned_name)
            if cleaned_name != original_name:
                cleaned_count += 1
        else:
            # Extract name from email as fallback
            extracted_name = extract_name_from_email(email)
            names.append(extracted_name)
            extracted_count += 1
    
    # Build dataframe in correct order to match sample.csv exactly
    refactored_df['Name'] = names
    refactored_df['Email'] = df['Email']
    refactored_df['state'] = df.get('State', '').fillna('')
    refactored_df['organization'] = df.get('Organization', '').fillna('')
    
    print(f"✅ Cleaned {cleaned_count} existing names")
    print(f"✅ Extracted {extracted_count} names from email addresses")
    
    # Save refactored file with exact sample.csv formatting
    output_file = Path(__file__).parent / "refactored_good_emails.csv"
    try:
        # Write with custom formatting to match sample exactly
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            # Write header with quotes
            f.write('"Name","Email","state","organization"\n')
            
            # Write data rows
            for _, row in refactored_df.iterrows():
                name = str(row['Name']).replace('"', '""')  # Escape quotes
                email = str(row['Email']).replace('"', '""')
                state = str(row['state']).replace('"', '""') if pd.notna(row['state']) else ''
                org = str(row['organization']).replace('"', '""') if pd.notna(row['organization']) else ''
                
                f.write(f'{name},{email},{state},{org}\n')
        print(f"✅ Created refactored_good_emails.csv with {len(refactored_df)} records")
        print(f"📁 File saved to: {output_file}")
        
        # Show sample of results
        print(f"\n📋 Sample of refactored data:")
        print(refactored_df.head(10).to_string(index=False))
        
    except Exception as err:
        print(f"❌ Error writing refactored file: {err}")

if __name__ == "__main__":
    refactor_good_emails()