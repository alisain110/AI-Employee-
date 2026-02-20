# Gold Tier Setup Instructions

## Prerequisites
- Python 3.8+
- Valid API keys for Odoo, Meta, and X
- Administrative access to configure system

## Setup Steps

### 1. Run the setup script
```bash
python setup_gold.py
```

### 2. Configure API keys
Edit the `.env` file and add your API keys:
```bash
# Odoo Configuration
ODOO_URL=your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-api-key

# Meta Configuration
META_ACCESS_TOKEN=your-meta-access-token
META_ACCOUNT_ID=your-instagram-account-id

# X Configuration
X_API_KEY=your-x-api-key
X_API_SECRET=your-x-api-secret
```

### 3. Test connections
Run the connection test script:
```bash
python test_gold_connections.py
```

### 4. Verify directory structure
Ensure all Gold Tier folders exist:
```
Accounting/
├── Exports/
├── Audits/
├── Reports/
└── odoo_config.md
Social_Summaries/
├── Facebook/
├── Instagram/
└── X/
Audits/
├── Weekly_Briefings/
├── Financial/
└── Compliance/
Ralph_Logs/
├── Traces/
├── Analysis/
└── Reports/
```

### 5. Update system configuration
Add Gold Tier skills to your agent by implementing:
- `skills/accounting_automation.py`
- `skills/social_media_manager.py`
- `skills/audit_reporter.py`
- `skills/ralph_analyzer.py`

## Next Steps
After setup, you should implement Gold Tier skills that will:
1. Connect to Odoo ERP for accounting automation
2. Generate social media summaries for FB/IG/X
3. Create weekly CEO briefings and audit reports
4. Maintain Ralph Wiggum loop traces for debugging
