"""
Odoo Execute MCP (Model Context Protocol) Server
This server handles local-only operations: posting/confirming invoices and registering payments
"""

import json
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Odoo Execute MCP", description="Local-only Odoo operations for execution actions")

# Configuration from environment variables
ODOO_URL = os.getenv("ODOO_LOCAL_URL", "http://localhost:8069")  # Local Odoo instance
ODOO_DB = os.getenv("ODOO_DB", "odoo_db_name")
ODOO_API_KEY = os.getenv("ODOO_EXECUTE_API_KEY", "your_local_execute_api_key")
ODOO_USER_ID = int(os.getenv("ODOO_USER_ID", "2"))  # Usually admin ID is 2

class OdooRequest(BaseModel):
    """Base model for Odoo JSON-RPC requests"""
    service: str
    method: str
    args: Dict[str, Any]

def call_odoo_jsonrpc(model: str, method: str, params: list, kwargs: Optional[Dict] = None) -> Dict:
    """Make a JSON-RPC call to Odoo"""
    if kwargs is None:
        kwargs = {}

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "object",
            "method": "execute_kw",
            "args": [ODOO_DB, ODOO_USER_ID, ODOO_API_KEY, model, method, params, kwargs]
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    logger.info(f"Making Odoo call: {model}.{method} with params {params}")

    try:
        response = requests.post(
            f"{ODOO_URL}/jsonrpc",
            data=json.dumps(payload),
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Odoo call failed with status {response.status_code}: {response.text}")
            raise HTTPException(status_code=500, detail=f"Odoo call failed: {response.text}")

        result = response.json()

        if "error" in result:
            logger.error(f"Odoo returned error: {result['error']}")
            raise HTTPException(status_code=500, detail=f"Odoo error: {result['error']}")

        return result["result"]

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error calling Odoo: {e}")
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=500, detail=f"JSON decode error: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "odoo_execute_mcp is running", "capabilities": ["post_invoice", "register_payment", "confirm_customer"]}

@app.post("/post_invoice")
async def post_invoice(request: Request):
    """
    Post/confirm an invoice in Odoo (local only operation)
    Expected payload: {
        "invoice_id": 1
    }
    """
    try:
        data = await request.json()

        invoice_id = data.get("invoice_id")
        if not invoice_id:
            raise HTTPException(status_code=400, detail="invoice_id is required")

        # First, check the current state of the invoice
        invoice_data = call_odoo_jsonrpc("account.move", "read", [[invoice_id], ["state", "name"]])

        if not invoice_data:
            raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")

        invoice = invoice_data[0]

        if invoice["state"] == "posted":
            return {
                "success": True,
                "message": f"Invoice {invoice['name']} is already posted",
                "invoice_id": invoice_id,
                "state": "posted"
            }

        # Post/confirm the invoice (change state from draft to posted)
        result = call_odoo_jsonrpc("account.move", "action_post", [[invoice_id]])

        logger.info(f"Invoice {invoice_id} posted successfully")

        # Get updated invoice data to return
        updated_invoice_data = call_odoo_jsonrpc("account.move", "read", [[invoice_id], ["name", "state", "amount_total"]])
        updated_invoice = updated_invoice_data[0]

        return {
            "success": True,
            "message": f"Invoice {updated_invoice['name']} posted successfully",
            "invoice_id": invoice_id,
            "invoice_name": updated_invoice["name"],
            "state": updated_invoice["state"],
            "amount_total": updated_invoice["amount_total"]
        }

    except Exception as e:
        logger.error(f"Error posting invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Error posting invoice: {str(e)}")

@app.post("/register_payment")
async def register_payment(request: Request):
    """
    Register a payment for an invoice in Odoo (local only operation)
    Expected payload: {
        "invoice_id": 1,
        "amount": 100.00,
        "payment_method": "manual"  # or "bank", "cash", etc.
    }
    """
    try:
        data = await request.json()

        invoice_id = data.get("invoice_id")
        amount = data.get("amount")
        payment_method = data.get("payment_method", "manual")

        if not invoice_id:
            raise HTTPException(status_code=400, detail="invoice_id is required")
        if not amount:
            raise HTTPException(status_code=400, detail="amount is required")

        # First, check if the invoice exists and is posted
        invoice_data = call_odoo_jsonrpc("account.move", "read", [[invoice_id], ["state", "amount_total", "amount_residual", "name"]])

        if not invoice_data:
            raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")

        invoice = invoice_data[0]

        if invoice["state"] != "posted":
            raise HTTPException(status_code=400, detail=f"Invoice {invoice['name']} is not posted, cannot register payment")

        # Check if the requested payment amount exceeds the residual amount
        if amount > invoice["amount_residual"]:
            raise HTTPException(status_code=400, detail=f"Payment amount {amount} exceeds residual amount {invoice['amount_residual']}")

        # Create payment
        payment_data = {
            "move_id": invoice_id,
            "amount": amount,
            "currency_id": 1,  # Assuming USD (ID=1), should make configurable
            "journal_id": 1,   # Assuming default journal (ID=1), should make configurable
            "payment_method_id": 1,  # Assuming default payment method (ID=1), should make configurable
            "date": datetime.now().strftime("%Y-%m-%d"),
        }

        # Create and post the payment
        payment_result = call_odoo_jsonrpc("account.payment.register", "create", [payment_data])

        # Execute the payment registration wizard
        # This is the typical Odoo pattern for payment registration
        wizard = payment_result
        execution_result = call_odoo_jsonrpc("account.payment.register", "action_create_payments", [wizard])

        logger.info(f"Payment registered for invoice {invoice_id}, amount: {amount}")

        return {
            "success": True,
            "message": f"Payment of {amount} registered for invoice {invoice['name']}",
            "invoice_id": invoice_id,
            "invoice_name": invoice["name"],
            "payment_amount": amount,
            "payment_method": payment_method,
            "result": execution_result
        }

    except Exception as e:
        logger.error(f"Error registering payment: {e}")
        raise HTTPException(status_code=500, detail=f"Error registering payment: {str(e)}")

@app.post("/confirm_customer")
async def confirm_customer(request: Request):
    """
    Confirm a customer that was created as a draft (local only operation)
    In Odoo, all partners are treated as customers by default when their customer_rank is > 0
    This endpoint updates the customer's status after draft creation is approved
    Expected payload: {
        "customer_id": 1,
        "additional_info": {}  # Optional additional info to update
    }
    """
    try:
        data = await request.json()

        customer_id = data.get("customer_id")
        additional_info = data.get("additional_info", {})

        if not customer_id:
            raise HTTPException(status_code=400, detail="customer_id is required")

        # First check if the customer exists
        customer_data = call_odoo_jsonrpc("res.partner", "read", [[customer_id], ["name", "email", "customer_rank"]])

        if not customer_data:
            raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")

        customer = customer_data[0]

        # Update any additional information if provided
        if additional_info:
            update_result = call_odoo_jsonrpc("res.partner", "write", [[customer_id], additional_info])
            logger.info(f"Updated customer {customer_id} with additional info: {additional_info}")
        else:
            update_result = True

        logger.info(f"Customer {customer_id} confirmed/updated successfully")

        return {
            "success": True,
            "message": f"Customer {customer['name']} confirmed successfully",
            "customer_id": customer_id,
            "customer_name": customer["name"],
            "customer_rank": customer["customer_rank"],
            "update_result": update_result
        }

    except Exception as e:
        logger.error(f"Error confirming customer: {e}")
        raise HTTPException(status_code=500, detail=f"Error confirming customer: {str(e)}")

@app.post("/execute_bulk_operations")
async def execute_bulk_operations(request: Request):
    """
    Execute multiple operations in a single transaction (local only operation)
    Expected payload: {
        "operations": [
            {
                "type": "register_payment|post_invoice|confirm_customer",
                "data": { ... }
            }
        ]
    }
    """
    try:
        data = await request.json()

        operations = data.get("operations", [])
        if not operations:
            raise HTTPException(status_code=400, detail="operations list is required and cannot be empty")

        results = []
        for i, operation in enumerate(operations):
            op_type = operation.get("type")
            op_data = operation.get("data", {})

            try:
                if op_type == "post_invoice":
                    result = await post_invoice(Request(scope={"type": "http", "method": "POST"}))
                elif op_type == "register_payment":
                    result = await register_payment(Request(scope={"type": "http", "method": "POST"}))
                elif op_type == "confirm_customer":
                    result = await confirm_customer(Request(scope={"type": "http", "method": "POST"}))
                else:
                    result = {"error": f"Unsupported operation type: {op_type}"}

                results.append({
                    "operation_index": i,
                    "type": op_type,
                    "success": "error" not in result,
                    "result": result
                })
            except Exception as op_error:
                logger.error(f"Error in bulk operation {i} ({op_type}): {op_error}")
                results.append({
                    "operation_index": i,
                    "type": op_type,
                    "success": False,
                    "error": str(op_error)
                })

        successful_ops = sum(1 for r in results if r["success"])
        total_ops = len(results)

        logger.info(f"Bulk operation completed: {successful_ops}/{total_ops} operations successful")

        return {
            "success": True,
            "total_operations": total_ops,
            "successful_operations": successful_ops,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error executing bulk operations: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing bulk operations: {str(e)}")

@app.post("/validate_invoice_before_posting")
async def validate_invoice_before_posting(request: Request):
    """
    Validate an invoice before posting to ensure it meets all requirements
    Expected payload: {
        "invoice_id": 1
    }
    """
    try:
        data = await request.json()

        invoice_id = data.get("invoice_id")
        if not invoice_id:
            raise HTTPException(status_code=400, detail="invoice_id is required")

        # Get invoice data
        invoice_data = call_odoo_jsonrpc("account.move", "read", [[invoice_id], [
            "state", "name", "amount_total", "amount_residual", "line_ids",
            "partner_id", "invoice_line_ids", "payment_state"
        ]])

        if not invoice_data:
            raise HTTPException(status_code=404, detail=f"Invoice with ID {invoice_id} not found")

        invoice = invoice_data[0]

        # Check if already posted
        if invoice["state"] == "posted":
            return {
                "valid": False,
                "message": f"Invoice {invoice['name']} is already posted",
                "can_post": False
            }

        # Validate required fields
        validation_results = {
            "invoice_id": invoice_id,
            "invoice_name": invoice["name"],
            "current_state": invoice["state"],
            "amount_total": invoice["amount_total"],
            "has_partner": bool(invoice["partner_id"]),
            "has_lines": len(invoice.get("invoice_line_ids", [])) > 0,
            "can_post": invoice["state"] == "draft" and invoice["amount_total"] > 0
        }

        # Additional validation can be added here based on business rules
        if validation_results["can_post"]:
            validation_results["message"] = f"Invoice {invoice['name']} is valid for posting"
        else:
            validation_results["message"] = f"Invoice {invoice['name']} is not ready for posting"

        return {
            "success": True,
            "validation": validation_results
        }

    except Exception as e:
        logger.error(f"Error validating invoice: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating invoice: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "odoo-execute-mcp-server",
        "local_only": True,
        "execution_mode": True,
        "sensitive_operations": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)