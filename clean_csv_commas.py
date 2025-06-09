#!/usr/bin/env python3
"""
Clean CSV Commas Script
Removes extra commas from names in CSV files to fix parsing issues
"""

import csv
import re
from pathlib import Path

def clean_name(name):
    """Clean commas and other problematic characters from names"""
    if not name or name.strip() == '':
        return name
    
    # Remove extra commas and clean up
    cleaned = name.strip()
    
    # Replace commas with spaces or remove them
    cleaned = re.sub(r',+', ' ', cleaned)  # Replace one or more commas with space
    
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def clean_csv_file(input_file, output_file):
    """Clean commas from CSV file"""
    try:
        rows_processed = 0
        rows_cleaned = 0
        
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            
            # Read first line to get header
            header_line = infile.readline().strip()
            outfile.write(header_line + '\n')
            
            print(f"📋 Header: {header_line}")
            
            # Process each data line
            for line_num, line in enumerate(infile, 2):
                line = line.strip()
                if not line:
                    continue
                
                rows_processed += 1
                
                # Use CSV reader to properly parse the line
                import csv
                from io import StringIO
                
                try:
                    # Parse the line properly
                    reader = csv.reader(StringIO(line))
                    row = next(reader)
                    
                    if len(row) >= 2:
                        # Clean the name (first field)
                        original_name = row[0].strip()
                        cleaned_name = clean_name(original_name)
                        
                        if original_name != cleaned_name:
                            rows_cleaned += 1
                            print(f"🔧 Line {line_num}: '{original_name}' → '{cleaned_name}'")
                        
                        # Update the row
                        row[0] = cleaned_name
                        
                        # Write back as proper CSV
                        writer_buffer = StringIO()
                        writer = csv.writer(writer_buffer)
                        writer.writerow(row)
                        cleaned_line = writer_buffer.getvalue().strip()
                        outfile.write(cleaned_line + '\n')
                    else:
                        # Keep line as is if it doesn't have enough parts
                        outfile.write(line + '\n')
                        
                except Exception as e:
                    # If CSV parsing fails, keep original line
                    print(f"⚠️  Line {line_num}: CSV parsing failed, keeping original")
                    outfile.write(line + '\n')
                
                # Progress indicator
                if rows_processed % 1000 == 0:
                    print(f"   Processed {rows_processed} rows...")
        
        print(f"\n✅ Cleaning completed!")
        print(f"📊 Total rows processed: {rows_processed}")
        print(f"🔧 Rows with names cleaned: {rows_cleaned}")
        print(f"📁 Clean file saved to: {output_file}")
        
        return True
        
    except Exception as err:
        print(f"❌ Error cleaning CSV: {err}")
        return False

def main():
    """Main function"""
    print("🚀 Starting CSV comma cleaning...")
    
    # Input and output files
    input_file = Path(__file__).parent / "refactored_good_emails.csv"
    output_file = Path(__file__).parent / "refactored_good_emails_clean.csv"
    
    # Check if input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("Please ensure refactored_good_emails.csv exists in the same directory")
        return
    
    print(f"📂 Input file: {input_file}")
    print(f"📂 Output file: {output_file}")
    
    # Clean the CSV file
    success = clean_csv_file(input_file, output_file)
    
    if success:
        print(f"\n🎉 CSV cleaning successful!")
        print(f"📋 Use {output_file.name} for uploading to Sendy")
    else:
        print(f"\n❌ CSV cleaning failed!")

if __name__ == "__main__":
    main()