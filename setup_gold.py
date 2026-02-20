"""
Gold Tier Setup for AI Employee Vault
This script installs required packages and sets up Gold Tier features:
- Accounting (Odoo integration)
- Social Media Summaries (FB/IG/X)
- Audits and CEO Briefings
- Ralph Logs
"""
import os
import sys
import subprocess
import pathlib

def install_packages():
    """Install required packages for Gold Tier features"""
    packages = [
        "requests",
        "odoorpc",
        "facebook-business",
        "tweepy",
        "python-dotenv",
        "xmlrpc"
    ]

    print("Installing required packages for Gold Tier...")
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[SUCCESS] {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"[ERROR] Failed to install {package}")

def create_env_template():
    """Create .env template with placeholders for API keys"""
    env_content = """# Gold Tier API Keys and Configuration

# Odoo ERP Configuration
ODOO_URL=your-odoo-instance.com
ODOO_DB=your-database-name
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-api-key

# Meta (Facebook/Instagram) API Configuration
META_ACCESS_TOKEN=your-meta-access-token
META_ACCOUNT_ID=your-instagram-account-id
FB_PAGE_ID=your-facebook-page-id

# X (Twitter) API Configuration
X_API_KEY=your-x-api-key
X_API_SECRET=your-x-api-secret
X_ACCESS_TOKEN=your-x-access-token
X_ACCESS_TOKEN_SECRET=your-x-access-token-secret
X_BEARER_TOKEN=your-x-bearer-token

# Additional configuration
LOG_LEVEL=INFO
DATA_RETENTION_DAYS=30
"""

    env_path = pathlib.Path(".") / ".env"
    if not env_path.exists():
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("[SUCCESS] .env template created with API key placeholders")
    else:
        print("[INFO] .env file already exists, skipping template creation")

def create_odoo_config():
    """Create Odoo configuration template"""
    odoo_config_content = """# Odoo ERP Configuration Template

## Connection Details
- URL: [Your Odoo Instance URL]
- Database: [Database Name]
- Username: [Your Username]
- API Key: [Your API Key]

## Required Permissions
- Read/Write access to Sales Orders
- Read/Write access to Invoices
- Read access to Products
- Read/Write access to Contacts

## Integration Points
- Daily sales reports
- Inventory tracking
- Customer management
- Financial auditing

## API Endpoints Used
- /api/sales_orders
- /api/invoices
- /api/products
- /api/contacts

## Scheduled Tasks
- Daily sync: 2:00 AM
- Weekly audit: Sunday 3:00 AM
- Monthly reports: 1st of month 4:00 AM
"""

    odoo_config_path = pathlib.Path("Accounting") / "odoo_config.md"
    with open(odoo_config_path, "w", encoding="utf-8") as f:
        f.write(odoo_config_content)
    print("[SUCCESS] Accounting/odoo_config.md created with connection info template")

def create_gold_directories():
    """Create additional Gold Tier directory structure"""
    gold_dirs = [
        "Accounting/Exports",
        "Accounting/Audits",
        "Accounting/Reports",
        "Social_Summaries/Facebook",
        "Social_Summaries/Instagram",
        "Social_Summaries/X",
        "Audits/Weekly_Briefings",
        "Audits/Financial",
        "Audits/Compliance",
        "Ralph_Logs/Traces",
        "Ralph_Logs/Analysis",
        "Ralph_Logs/Reports"
    ]

    for directory in gold_dirs:
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
    print("[SUCCESS] Gold Tier directory structure created")

def update_requirements():
    """Add Gold Tier packages to requirements.txt"""
    gold_packages = [
        "odoorpc>=1.2.0",
        "facebook-business>=18.0.0",
        "tweepy>=4.14.0",
        "xmlrpc>=1.0.0"
    ]

    # Read existing requirements
    with open("requirements.txt", "r", encoding="utf-8") as f:
        requirements = f.read()

    # Add Gold Tier packages if not already present
    for package in gold_packages:
        if package not in requirements:
            requirements += f"\n# Gold Tier - Accounting and Social Media\n{package}\n"

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write(requirements)

    print("[SUCCESS] Gold Tier packages added to requirements.txt")

def create_setup_instructions():
    """Create run instructions for Gold Tier setup"""
    instructions = """# Gold Tier Setup Instructions

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
"""

    with open("GOLD_SETUP_INSTRUCTIONS.md", "w", encoding="utf-8") as f:
        f.write(instructions)
    print("[SUCCESS] GOLD_SETUP_INSTRUCTIONS.md created with run instructions")

def main():
    """Main setup function"""
    print("[SETUP] AI Employee Vault - Gold Tier Setup")
    print("=" * 50)

    # Create directory structure
    create_gold_directories()

    # Install required packages
    install_packages()

    # Create .env template
    create_env_template()

    # Create Odoo config
    create_odoo_config()

    # Update requirements
    update_requirements()

    # Create setup instructions
    create_setup_instructions()

    print("=" * 50)
    print("[SUCCESS] Gold Tier setup complete!")
    print("[INFO] Next: Follow instructions in GOLD_SETUP_INSTRUCTIONS.md")
    print("[INFO] Don't forget to add your API keys to .env")
    print("[INFO] Run: python test_gold_connections.py to verify setup")

if __name__ == "__main__":
    main()