import pandas as pd
import re
import glob
from pathlib import Path

def clean_email(email):
    """Clean and validate email addresses"""
    if pd.isna(email) or email == '':
        return None
    
    email = str(email).strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(email_pattern, email):
        return email
    return None

def extract_name_parts(name_str):
    """Extract first and last name from various formats"""
    if pd.isna(name_str) or name_str == '':
        return '', ''
    
    name_str = str(name_str).strip()
    parts = name_str.split()
    
    if len(parts) >= 2:
        return parts[0], ' '.join(parts[1:])
    elif len(parts) == 1:
        return parts[0], ''
    return '', ''

def process_file(file_path, source_name):
    """Process individual CSV file and return standardized DataFrame"""
    try:
        df = pd.read_csv(file_path)
        processed_data = []
        
        for _, row in df.iterrows():
            email = None
            name = ''
            state = ''
            organization = ''
            
            # Extract email based on file structure
            if 'Email' in df.columns:
                email = clean_email(row.get('Email'))
            elif 'From Email Address' in df.columns:
                email = clean_email(row.get('From Email Address'))
            
            # Extract name
            if 'Name' in df.columns:
                name = str(row.get('Name', '')).strip()
            elif 'First Name' in df.columns and 'Last Name' in df.columns:
                first = str(row.get('First Name', '')).strip()
                last = str(row.get('Last Name', '')).strip()
                name = f"{first} {last}".strip()
            elif 'Member Group' in df.columns:
                name = str(row.get('Member Group', '')).strip()
                organization = name
            
            # Extract other fields
            if 'State' in df.columns:
                state = str(row.get('State', '')).strip()
            elif 'State/Province/Region/County/Territory/Prefecture/Republic' in df.columns:
                state = str(row.get('State/Province/Region/County/Territory/Prefecture/Republic', '')).strip()
            
            if 'Org' in df.columns:
                organization = str(row.get('Org', '')).strip()
            
            # Only add if we have a valid email
            if email:
                processed_data.append({
                    'Name': name,
                    'Email': email,
                    'Source': source_name,
                    'State': state,
                    'Organization': organization
                })
        
        return pd.DataFrame(processed_data)
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return pd.DataFrame()

def consolidate_email_lists():
    """Main function to consolidate all email lists"""
    
    # Define file mappings
    file_mappings = {
        '2018_speaking_tour_contacts.csv': '2018 Speaking Tour',
        'Defund Racism Contact  - Everyone.csv': 'Defund Racism',
        'US Campaign supporters - Sheet1.csv': 'US Campaign Supporters',
        'US Campaign supporters - Sheet1 (1).csv': 'US Campaign Supporters',
        'good_shepherd_collective_contacts.csv': 'Good Shepherd Collective',
        'new_website_subscribers_backup.csv': 'Website Subscribers',
        '50,000 final 1_19_2018.csv - 50,000 final 1_19_2018.csv.csv': 'International Contacts',
        'Download.CSV - Download.CSV.csv': 'PayPal Subscribers',
        'final_cleaning_7_21_2018_valid - final_cleaning_7_21_2018_valid.csv': 'Cleaned 2018 List',
        'Untitled spreadsheet - Sheet1.csv': 'Additional Contacts',
        'bot_subscribers_to_delete.csv': 'Bot Subscribers',
        'wpforms-2013-Petition-ID-2013-2023-12-11-18-09-47 - wpforms-2013-Petition-ID-2013-2023-12-11-18-09-47.csv': 'Petition Signers',
        'new report - new report.csv': 'New Report',
        '2064876-6478ace66c7eaba50e79d802-jx7sWo - 2064876-6478ace66c7eaba50e79d802-jx7sWo.csv': 'Export Data',
        'HcmComm-Customers-Export--2024-10-27-06-55-16 - HcmComm-Customers-Export--2024-10-27-06-55-16.csv': 'HcmComm Customers',
        'Fundraising Report via SalesForce.xlsx - main.csv': 'SalesForce Fundraising'
    }
    
    all_data = []
    base_path = Path('/Users/codyorourke/Desktop/emails')
    
    # Process each file
    for filename, source_name in file_mappings.items():
        file_path = base_path / filename
        if file_path.exists():
            print(f"Processing: {filename}")
            df = process_file(file_path, source_name)
            if not df.empty:
                all_data.append(df)
                print(f"  - Added {len(df)} records")
            else:
                print(f"  - No valid records found")
        else:
            print(f"File not found: {filename}")
    
    # Combine all data
    if all_data:
        consolidated_df = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates based on email
        print(f"\nTotal records before deduplication: {len(consolidated_df)}")
        consolidated_df = consolidated_df.drop_duplicates(subset=['Email'], keep='first')
        print(f"Total records after deduplication: {len(consolidated_df)}")
        
        # Sort by name
        consolidated_df = consolidated_df.sort_values('Name')
        
        # Save consolidated list
        output_file = base_path / 'consolidated_email_list.csv'
        consolidated_df.to_csv(output_file, index=False)
        print(f"\nConsolidated email list saved to: {output_file}")
        
        # Print summary statistics
        print(f"\nSummary:")
        print(f"Total unique emails: {len(consolidated_df)}")
        print(f"Sources breakdown:")
        for source in consolidated_df['Source'].value_counts().items():
            print(f"  - {source[0]}: {source[1]} contacts")
        
        return consolidated_df
    else:
        print("No data to consolidate")
        return pd.DataFrame()

if __name__ == "__main__":
    consolidate_email_lists()