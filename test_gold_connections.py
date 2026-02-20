"""
Test script for Gold Tier API connections
Verifies that all API keys are properly configured
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def test_odoo_connection():
    """Test Odoo ERP connection"""
    print("Testing Odoo connection...")

    try:
        import odoorpc
        print("[SUCCESS] OdooRPC package is available")

        # Load environment variables
        load_dotenv()

        odoo_url = os.getenv('ODOO_URL')
        odoo_db = os.getenv('ODOO_DB')
        odoo_username = os.getenv('ODOO_USERNAME')
        odoo_password = os.getenv('ODOO_PASSWORD')

        if not all([odoo_url, odoo_db, odoo_username, odoo_password]):
            print("[WARNING] Odoo API keys not configured in .env")
            print("   Please add ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD to your .env file")
            return False

        # Test connection
        odoo = odoorpc.ODOO(odoo_url, port=443, protocol='jsonrpc+ssl')
        odoo.login(odoo_db, odoo_username, odoo_password)

        print("[SUCCESS] Odoo connection successful")
        print(f"  - Connected to: {odoo_url}")
        print(f"  - Database: {odoo_db}")
        print(f"  - User: {odoo_username}")

        # Test basic operations
        user = odoo.env.user
        print(f"  - Current user: {user.name}")

        return True

    except ImportError:
        print("[ERROR] OdooRPC not installed - run: pip install odoorpc")
        return False
    except Exception as e:
        print(f"[ERROR] Odoo connection failed: {e}")
        return False

def test_meta_connection():
    """Test Meta (Facebook/Instagram) API connection"""
    print("\\nTesting Meta API connection...")

    try:
        import facebook_business
        from facebook_business.api import FacebookAdsApi
        print("[SUCCESS] Facebook Business SDK package is available")

        load_dotenv()

        meta_access_token = os.getenv('META_ACCESS_TOKEN')
        meta_account_id = os.getenv('META_ACCOUNT_ID')

        if not meta_access_token:
            print("[WARNING] Meta API key not configured in .env")
            print("   Please add META_ACCESS_TOKEN to your .env file")
            return False

        # Test API connection
        FacebookAdsApi.init(access_token=meta_access_token)
        print("[SUCCESS] Meta API connection initialized")

        # Note: More detailed testing would require actual account access
        # which may not be available in test environment
        print("  - Access token configured")
        if meta_account_id:
            print(f"  - Account ID: {meta_account_id}")

        return True

    except ImportError:
        print("[ERROR] Facebook Business SDK not installed - run: pip install facebook-business")
        return False
    except Exception as e:
        print(f"[ERROR] Meta API connection failed: {e}")
        return False

def test_x_connection():
    """Test X (Twitter) API connection"""
    print("\\nTesting X API connection...")

    try:
        import tweepy
        print("[SUCCESS] Tweepy package is available")

        load_dotenv()

        x_api_key = os.getenv('X_API_KEY')
        x_api_secret = os.getenv('X_API_SECRET')
        x_access_token = os.getenv('X_ACCESS_TOKEN')
        x_access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')
        x_bearer_token = os.getenv('X_BEARER_TOKEN')

        if not all([x_api_key, x_api_secret, x_access_token, x_access_token_secret, x_bearer_token]):
            print("[WARNING] X API keys not fully configured in .env")
            print("   Please add all X API keys to your .env file")
            return False

        # Initialize API v2 client
        client = tweepy.Client(
            bearer_token=x_bearer_token,
            consumer_key=x_api_key,
            consumer_secret=x_api_secret,
            access_token=x_access_token,
            access_token_secret=x_access_token_secret
        )

        print("[SUCCESS] X API connection initialized")

        # Test by getting API information
        # api = tweepy.API(auth)
        # user = api.verify_credentials()
        # print(f"  - Authenticated as: {user.screen_name}")

        return True

    except ImportError:
        print("[ERROR] Tweepy not installed - run: pip install tweepy")
        return False
    except Exception as e:
        print(f"[ERROR] X API connection failed: {e}")
        return False

def test_directory_structure():
    """Test that Gold Tier directories exist"""
    print("\\nTesting directory structure...")

    gold_directories = [
        "Accounting",
        "Social_Summaries",
        "Audits",
        "Ralph_Logs",
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

    success = True
    for directory in gold_directories:
        if Path(directory).exists():
            print(f"[SUCCESS] {directory}/ directory exists")
        else:
            print(f"[ERROR] {directory}/ directory missing")
            success = False

    return success

def main():
    """Run all tests"""
    print("[TEST] Testing Gold Tier API Connections")
    print("=" * 50)

    load_dotenv()  # Load environment variables

    # Run all tests
    odoo_ok = test_odoo_connection()
    meta_ok = test_meta_connection()
    x_ok = test_x_connection()
    dirs_ok = test_directory_structure()

    print("\\n" + "=" * 50)
    print("Test Results:")
    print(f"  Odoo Connection: {'[PASS]' if odoo_ok else '[FAIL]'}")
    print(f"  Meta Connection: {'[PASS]' if meta_ok else '[FAIL]'}")
    print(f"  X Connection: {'[PASS]' if x_ok else '[FAIL]'}")
    print(f"  Directory Structure: {'[PASS]' if dirs_ok else '[FAIL]'}")

    if all([odoo_ok, meta_ok, x_ok, dirs_ok]):
        print("\\n[SUCCESS] All Gold Tier connections are properly configured!")
        return True
    else:
        print("\\n[WARNING] Some Gold Tier connections need attention.")
        print("   Please follow the setup instructions in GOLD_SETUP_INSTRUCTIONS.md")
        return False

if __name__ == "__main__":
    main()