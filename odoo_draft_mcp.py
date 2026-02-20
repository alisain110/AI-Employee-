"""
Odoo Draft MCP Server - Model Context Protocol server for draft Odoo operations
Cloud-only version that creates draft actions but doesn't execute them
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "odoo_draft_actions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo Draft MCP Server",
    description="Model Context Protocol server for draft Odoo operations (cloud-only)",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# API Key from environment
ODOO_DRAFT_API_KEY = os.getenv("ODOO_DRAFT_API_KEY", "your-odoo-draft-api-key")

# Pending approval directory (cloud-specific)
pending_approval_dir = Path("Pending_Approval") / "cloud"
pending_approval_dir.mkdir(parents=True, exist_ok=True)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API key in the Authorization header"""
    if credentials.credentials != ODOO_DRAFT_API_KEY:
        logger.warning(f"Invalid API key attempted: {credentials.credentials}")
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

def create_approval_request(action_data: Dict[str, Any]):
    """Create an approval request for Odoo operations (requires local execution)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"odoo_approval_{timestamp}_{action_data.get('action', 'generic')}.json"
    filepath = pending_approval_dir / filename

    approval_data = {
        "timestamp": datetime.now().isoformat(),
        "action": action_data.get('action'),
        "details": action_data,
        "status": "pending",
        "approved": False
    }

    with open(filepath, 'w') as f:
        json.dump(approval_data, f, indent=2)

    logger.info(f"Odoo approval request created: {filepath}")
    return filepath

# Pydantic models
class CreateInvoiceRequest(BaseModel):
    partner_id: int
    products_list: List[Dict[str, Any]]  # [{"product_id": int, "quantity": float, "price": float}]
    amounts: Dict[str, float]  # {"subtotal": float, "tax": float, "total": float}

class CreateCustomerRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    vat: Optional[str] = None

class GetUnpaidInvoicesRequest(BaseModel):
    partner_id: Optional[int] = None
    domain: Optional[List] = None

@app.post("/create_invoice")
async def create_invoice(
    request: CreateInvoiceRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create an approval request for invoice creation (cloud only - no actual creation)
    """
    try:
        # Create approval request for this sensitive action
        approval_data = {
            "action": "create_invoice",
            "partner_id": request.partner_id,
            "products": request.products_list,
            "amounts": request.amounts
        }

        approval_file = create_approval_request(approval_data)

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "create_invoice_requested",
            "partner_id": request.partner_id,
            "total": request.amounts.get("total", 0),
            "approval_file": str(approval_file)
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "approval_requested",
            "message": "Invoice creation requested, requires local approval",
            "approval_file": str(approval_file),
            "estimated_total": request.amounts.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error in create_invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_customer")
async def create_customer(
    request: CreateCustomerRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create an approval request for customer creation (cloud only - no actual creation)
    """
    try:
        # Create approval request for this sensitive action
        approval_data = {
            "action": "create_customer",
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "vat": request.vat
        }

        approval_file = create_approval_request(approval_data)

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "create_customer_requested",
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "approval_file": str(approval_file)
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "approval_requested",
            "message": "Customer creation requested, requires local approval",
            "approval_file": str(approval_file),
            "customer_name": request.name
        }
    except Exception as e:
        logger.error(f"Error in create_customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_unpaid_invoices")
async def get_unpaid_invoices(
    request: GetUnpaidInvoicesRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Get unpaid invoices (draft mode - would require local Odoo connection in real implementation)
    """
    try:
        # This would normally query the local Odoo instance
        # For cloud implementation, we return a placeholder response
        # indicating that this requires local execution

        result = {
            "status": "read_only_mode",
            "message": "Unpaid invoices query requires local Odoo connection",
            "requires_local_access": True,
            "suggestion": "Create approval request for local processing",
            "query_params": {
                "partner_id": request.partner_id,
                "domain": request.domain
            }
        }

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "get_unpaid_invoices_query",
            "partner_id": request.partner_id,
            "domain": request.domain
        }
        logger.info(json.dumps(log_entry))

        return result
    except Exception as e:
        logger.error(f"Error in get_unpaid_invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_balance_sheet_summary")
async def get_balance_sheet_summary(api_key: str = Depends(verify_api_key)):
    """
    Get balance sheet summary (draft mode - requires local Odoo connection)
    """
    try:
        # This would normally query the local Odoo instance
        result = {
            "status": "read_only_mode",
            "message": "Balance sheet query requires local Odoo connection",
            "requires_local_access": True,
            "suggestion": "Create approval request for local processing"
        }

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "get_balance_sheet_summary_query"
        }
        logger.info(json.dumps(log_entry))

        return result
    except Exception as e:
        logger.error(f"Error in get_balance_sheet_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_profit_loss_last_30_days")
async def get_profit_loss_last_30_days(api_key: str = Depends(verify_api_key)):
    """
    Get profit/loss for last 30 days (draft mode - requires local Odoo connection)
    """
    try:
        # This would normally query the local Odoo instance
        result = {
            "status": "read_only_mode",
            "message": "Profit/loss query requires local Odoo connection",
            "requires_local_access": True,
            "suggestion": "Create approval request for local processing"
        }

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "get_profit_loss_query"
        }
        logger.info(json.dumps(log_entry))

        return result
    except Exception as e:
        logger.error(f"Error in get_profit_loss_last_30_days: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "odoo-draft-mcp-server",
        "cloud_only": True,
        "draft_mode": True,
        "read_only": True,
        "no_exec": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "odoo_draft_mcp:app",
        host="0.0.0.0",
        port=8005,  # Odoo Draft MCP server on port 8005
        reload=False,
        log_level="info"
    )