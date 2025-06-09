# Email List Management Tools

A Python project for managing and cleaning email lists, specifically designed to work with Sendy email marketing platform data.

## Overview

This project provides a complete workflow for extracting bad contacts from a Sendy database, consolidating email lists, and creating clean master lists suitable for email marketing campaigns.

## Features

- **Database Export**: Extract bounced, unsubscribed, and complaint emails from Sendy database via SSH tunnel
- **Email Consolidation**: Combine multiple CSV email lists into a single consolidated list
- **Bad Contact Filtering**: Create omit lists and filter out problematic emails
- **Geographic Filtering**: Remove emails from specific domains (e.g., .co.il) and names with non-Latin characters
- **Deduplication**: Automatic removal of duplicate emails across all operations

## Scripts

### 1. `export_bad_contacts.py`
Exports problematic contacts from your Sendy database via SSH tunnel.

**Exports:**
- Hard bounces
- Soft bounces  
- Unsubscribed contacts
- Complaints
- Suppression list
- Combined file with all issues

**Usage:**
```bash
python3 export_bad_contacts.py
```

**Requirements:**
- SSH access to your Sendy server configured as `amazon-sendy`
- Database credentials configured in the script
- `mysql-connector-python` package

### 2. `consolidate_emails.py`
Combines multiple CSV files containing email lists into a single consolidated list.

**Features:**
- Processes all CSV files in `emails_from_google_drive/` folder
- Standardizes column names (Name, Email, Source, State, Organization)
- Removes duplicates based on email addresses
- Handles various CSV formats and encodings

**Usage:**
```bash
python3 consolidate_emails.py
```

### 3. `create_omit_list.py`
Creates a master omit list from all bad contact files in the `sendy_emails/` folder.

**Usage:**
```bash
python3 create_omit_list.py
```

**Output:** `omit.csv` containing all unique bad email addresses

### 4. `create_master_list.py`
Creates a clean master email list by removing all emails from the omit list.

**Usage:**
```bash
python3 create_master_list.py
```

**Input:** 
- `consolidated_email_list.csv`
- `omit.csv`

**Output:** `master.csv` with clean, marketable emails

### 5. `filter_master_list.py`
Applies additional filters to remove specific types of emails and names.

**Filters:**
- Emails ending with `.co.il`
- Names containing Hebrew characters

**Usage:**
```bash
python3 filter_master_list.py
```

## Workflow

1. **Export bad contacts** from Sendy database:
   ```bash
   python3 export_bad_contacts.py
   ```

2. **Consolidate** all your email lists:
   ```bash
   python3 consolidate_emails.py
   ```

3. **Create omit list** from bad contacts:
   ```bash
   python3 create_omit_list.py
   ```

4. **Generate clean master list**:
   ```bash
   python3 create_master_list.py
   ```

5. **Apply additional filters**:
   ```bash
   python3 filter_master_list.py
   ```

## File Structure

```
├── emails_from_google_drive/     # Input: Raw email CSV files
├── sendy_emails/                 # Input: Bad contacts from Sendy
├── consolidated_email_list.csv   # Output: Combined email list
├── omit.csv                      # Output: Emails to exclude
├── master.csv                    # Output: Final clean email list
└── scripts/                      # Python scripts
```

## Dependencies

- `pandas`: Data manipulation and analysis
- `mysql-connector-python`: MySQL database connectivity
- `csv`: CSV file handling
- `pathlib`: File path operations

## Installation

```bash
pip install pandas mysql-connector-python
```

## Configuration

### Database Configuration
Update the `DB_CONFIG` in `export_bad_contacts.py`:

```python
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'your_database',
    'port': 3306,
    'charset': 'utf8mb4',
}
```

### SSH Configuration
Ensure your SSH config has an entry for your Sendy server:

```
# ~/.ssh/config
Host amazon-sendy
    HostName your-server.com
    User your-username
    IdentityFile ~/.ssh/your-key.pem
```

## Output Statistics

Based on recent run:
- **Total consolidated emails**: 67,818
- **Bad contacts identified**: 12,283 unique emails
- **Final clean master list**: 56,024 emails
- **Geographic filters removed**: 51 additional emails

## Security Notes

- Database credentials are stored in plain text - consider using environment variables
- SSH keys should be properly secured
- Review all email lists before using for marketing campaigns
- Ensure compliance with email marketing regulations (CAN-SPAM, GDPR, etc.)

## License

MIT License - feel free to modify and distribute as needed.