"""
Odoo Integration Agent Skills
"""
import os
import json
import requests
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

@tool
def create_invoice(partner_id: int, products_list: List[Dict[str, Any]], amounts: Dict[str, float]) -> str:
    """
    Create an invoice in Odoo ERP system.

    This skill requests invoice creation which requires human approval before execution.

    Args:
        partner_id (int): Odoo partner/customer ID
        products_list (List[Dict[str, Any]]): List of products with their details
            [{"product_id": int, "quantity": float, "price": float}]
        amounts (Dict[str, float]): Amounts breakdown
            {"subtotal": float, "tax": float, "total": float}

    Returns:
        str: Status message about the approval request
    """
    api_key = os.getenv("ODOO_API_KEY")
    mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "partner_id": partner_id,
        "products_list": products_list,
        "amounts": amounts
    }

    try:
        response = requests.post(
            f"{mcp_url}/create_invoice",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            return f"Invoice creation requested. Status: {result['status']}. {result['message']}. Approval file: {result['approval_file']}"
        else:
            return f"Error creating invoice: {response.text}"
    except Exception as e:
        return f"Error creating invoice: {str(e)}"

@tool
def get_unpaid_invoices(partner_id: Optional[int] = None, domain: Optional[List] = None) -> Dict[str, Any]:
    """
    Get unpaid invoices from Odoo ERP system.

    Args:
        partner_id (Optional[int]): Specific partner ID to filter by
        domain (Optional[List]): Additional domain filters

    Returns:
        Dict[str, Any]: Dictionary containing invoices and metadata
    """
    api_key = os.getenv("ODOO_API_KEY")
    mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "partner_id": partner_id,
        "domain": domain
    }

    try:
        response = requests.post(
            f"{mcp_url}/get_unpaid_invoices",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "invoices": result["invoices"],
                "count": result["count"]
            }
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def create_customer(name: str, email: Optional[str] = None, phone: Optional[str] = None, vat: Optional[str] = None) -> str:
    """
    Create a customer in Odoo ERP system.

    This skill requests customer creation which requires human approval before execution.

    Args:
        name (str): Customer name
        email (Optional[str]): Customer email
        phone (Optional[str]): Customer phone number
        vat (Optional[str]): Customer VAT number

    Returns:
        str: Status message about the approval request
    """
    api_key = os.getenv("ODOO_API_KEY")
    mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "name": name,
        "email": email,
        "phone": phone,
        "vat": vat
    }

    try:
        response = requests.post(
            f"{mcp_url}/create_customer",
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            result = response.json()
            return f"Customer creation requested. Status: {result['status']}. {result['message']}. Approval file: {result['approval_file']}"
        else:
            return f"Error creating customer: {response.text}"
    except Exception as e:
        return f"Error creating customer: {str(e)}"

@tool
def get_balance_sheet_summary() -> Dict[str, Any]:
    """
    Get balance sheet summary from Odoo ERP system.

    Returns:
        Dict[str, Any]: Dictionary containing balance sheet data and summary
    """
    api_key = os.getenv("ODOO_API_KEY")
    mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{mcp_url}/get_balance_sheet_summary",
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@tool
def get_profit_loss_last_30_days() -> Dict[str, Any]:
    """
    Get profit and loss for the last 30 days from Odoo ERP system.

    Returns:
        Dict[str, Any]: Dictionary containing P&L data and period information
    """
    api_key = os.getenv("ODOO_API_KEY")
    mcp_url = os.getenv("ODOO_MCP_URL", "http://localhost:8002")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{mcp_url}/get_profit_loss_last_30_days",
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            return result
        else:
            return {"status": "error", "message": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}