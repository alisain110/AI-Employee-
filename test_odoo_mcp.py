"""
Test script for Odoo MCP Server
Demonstrates how to test one action (create test customer)
"""
import os
import json
import requests
from datetime import datetime

def test_create_customer():
    """Test creating a customer via the Odoo MCP server"""

    # Load environment variables
    odoo_api_key = os.getenv("ODOO_API_KEY", "your_odoo_mcp_api_key")
    odoo_mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    # Test data for creating a customer
    customer_data = {
        "name": f"Test Customer {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "email": f"test.customer.{int(datetime.now().timestamp())}@example.com",
        "phone": "+1234567890",
        "vat": "US123456789"
    }

    # Headers for authentication
    headers = {
        "Authorization": f"Bearer {odoo_api_key}",
        "Content-Type": "application/json"
    }

    print("Testing Odoo MCP Server - Create Customer")
    print("=" * 50)
    print(f"Target URL: {odoo_mcp_url}/create_customer")
    print(f"Customer data: {json.dumps(customer_data, indent=2)}")
    print()

    try:
        # Make the API call
        response = requests.post(
            f"{odoo_mcp_url}/create_customer",
            headers=headers,
            json=customer_data
        )

        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            print("\n✓ Customer creation request successful!")
            print(f"Status: {result.get('status')}")
            print(f"Message: {result.get('message')}")
            print(f"Approval file: {result.get('approval_file')}")
            print(f"Customer name: {result.get('customer_name')}")

            # Check if approval was requested
            if result.get('status') == 'approval_requested':
                print("\n⚠️  Action requires approval!")
                print("An approval request has been created in the Pending_Approval folder.")
                print("Move the approval file to Approved folder to allow execution.")
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Unable to connect to Odoo MCP server")
        print("Make sure the server is running on:", odoo_mcp_url)
        print("Start the server with: python odoo_mcp_server.py")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

def test_get_balance_sheet():
    """Test getting balance sheet summary via the Odoo MCP server"""

    # Load environment variables
    odoo_api_key = os.getenv("ODOO_API_KEY", "your_odoo_mcp_api_key")
    odoo_mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    # Headers for authentication
    headers = {
        "Authorization": f"Bearer {odoo_api_key}",
        "Content-Type": "application/json"
    }

    print("\nTesting Odoo MCP Server - Get Balance Sheet Summary")
    print("=" * 50)
    print(f"Target URL: {odoo_mcp_url}/get_balance_sheet_summary")
    print()

    try:
        # Make the API call
        response = requests.get(
            f"{odoo_mcp_url}/get_balance_sheet_summary",
            headers=headers
        )

        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            print("\n✓ Balance sheet summary retrieved successfully!")

            if result.get('status') == 'success':
                balance_sheet = result.get('balance_sheet', {})
                print(f"Total Assets: ${balance_sheet.get('total_assets', 0):,.2f}")
                print(f"Total Liabilities: ${balance_sheet.get('total_liabilities', 0):,.2f}")
                print(f"Total Equity: ${balance_sheet.get('total_equity', 0):,.2f}")
                print(f"Net Worth: ${balance_sheet.get('net_worth', 0):,.2f}")
        else:
            print(f"\n❌ Request failed with status {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Unable to connect to Odoo MCP server")
        print("Make sure the server is running on:", odoo_mcp_url)
        print("Start the server with: python odoo_mcp_server.py")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

def test_health_check():
    """Test the health check endpoint"""

    # Load environment variables
    odoo_mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    print("\nTesting Odoo MCP Server - Health Check")
    print("=" * 50)
    print(f"Target URL: {odoo_mcp_url}/health")
    print()

    try:
        # Make the API call (health check doesn't require auth)
        response = requests.get(f"{odoo_mcp_url}/health")

        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n✓ Health check successful!")
            print(f"Status: {result.get('status')}")
            print(f"Service: {result.get('service')}")
            print(f"Connected to Odoo: {result.get('odoo_connected')}")
            if result.get('odoo_connected'):
                print(f"User ID: {result.get('user_id')}")
        else:
            print(f"\n❌ Health check failed with status {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Unable to connect to Odoo MCP server")
        print("Make sure the server is running on:", odoo_mcp_url)
        print("Start the server with: python odoo_mcp_server.py")
    except Exception as e:
        print(f"❌ Error occurred: {e}")

def show_setup_instructions():
    """Show setup instructions"""
    print("Setup Instructions:")
    print("=" * 50)
    print("1. Copy .env_odoo_example to .env and update with your values:")
    print("   - ODOO_URL: Your Odoo instance URL (e.g. http://localhost:8069)")
    print("   - ODOO_DB: Your Odoo database name")
    print("   - ODOO_USERNAME: Your Odoo username")
    print("   - ODOO_PASSWORD: Your Odoo password")
    print("   - ODOO_API_KEY: Your API key for the MCP server")
    print()
    print("2. Start the Odoo MCP server:")
    print("   python odoo_mcp_server.py")
    print()
    print("3. To run this test script:")
    print("   python test_odoo_mcp.py")
    print()
    print("4. API endpoints available:")
    print("   POST /create_invoice - Create invoice (requires approval)")
    print("   POST /get_unpaid_invoices - Get unpaid invoices")
    print("   POST /create_customer - Create customer (requires approval)")
    print("   GET  /get_balance_sheet_summary - Get balance sheet summary")
    print("   GET  /get_profit_loss_last_30_days - Get P&L for last 30 days")
    print("   GET  /health - Health check")
    print()
    print("5. Sensitive actions (create_invoice, create_customer) automatically")
    print("   create approval requests in Pending_Approval/ folder.")
    print("   Move to Approved/ folder to execute the action.")

if __name__ == "__main__":
    show_setup_instructions()
    print()
    print("Running tests...")
    test_health_check()
    test_get_balance_sheet()
    test_create_customer()