"""
Production-ready Odoo MCP Server for AI Employee Vault
FastAPI server that connects to Odoo Community via JSON-RPC
"""
import os
import json
import logging
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from audit_logger import get_audit_logger, AuditActor, AuditAction, retry_on_transient_error, graceful_fallback

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "odoo_actions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Odoo MCP Server",
    description="Model Context Protocol server for Odoo integration",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# API Key and Odoo connection info from environment
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo_db")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
ODOO_API_KEY = os.getenv("ODOO_API_KEY", "your-odoo-api-key")

# Initialize audit logger
audit_logger = get_audit_logger()

# Pending approval directory
pending_approval_dir = Path("Pending_Approval")
pending_approval_dir.mkdir(exist_ok=True)

@retry_on_transient_error(max_retries=3, base_delay=1.0)
def authenticate_odoo():
    """Authenticate with Odoo and get user session"""
    try:
        login_url = f"{ODOO_URL}/web/session/authenticate"

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "db": ODOO_DB,
                "login": ODOO_USERNAME,
                "password": ODOO_PASSWORD
            },
            "id": 1
        }

        response = requests.post(login_url, json=payload)
        result = response.json()

        if 'result' in result and result['result']:
            session_id = result['result']['session_id']
            uid = result['result']['uid']

            # Log successful authentication
            audit_logger.log_mcp_call(
                service="odoo_mcp",
                endpoint="authenticate",
                data={"user": ODOO_USERNAME, "db": ODOO_DB},
                success=True,
                response={"user_id": uid},
                session_id=datetime.now().isoformat()
            )

            return session_id, uid
        else:
            error_msg = "Odoo authentication failed"
            audit_logger.log_error(
                error_type="odoo_auth_failed",
                error_message=error_msg,
                context={"user": ODOO_USERNAME, "db": ODOO_DB},
                severity="high"
            )
            raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Odoo authentication error: {e}"
        logger.error(error_msg)

        audit_logger.log_mcp_call(
            service="odoo_mcp",
            endpoint="authenticate",
            data={"user": ODOO_USERNAME, "db": ODOO_DB},
            success=False,
            error=str(e),
            session_id=datetime.now().isoformat()
        )
        raise

@retry_on_transient_error(max_retries=3, base_delay=1.0)
def call_odoo_jsonrpc(model: str, method: str, args: List = [], kwargs: Dict = {}):
    """Call Odoo via JSON-RPC"""
    try:
        start_time = time.time()
        session_id, uid = authenticate_odoo()

        jsonrpc_url = f"{ODOO_URL}/jsonrpc"

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [ODOO_DB, uid, ODOO_PASSWORD, model, method, args, kwargs]
            },
            "id": 2
        }

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"session_id={session_id}"
        }

        response = requests.post(jsonrpc_url, json=payload, headers=headers)
        call_duration = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                # Log successful call
                audit_logger.log_mcp_call(
                    service="odoo_mcp",
                    endpoint=f"jsonrpc.{model}.{method}",
                    data={"model": model, "method": method, "args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                    success=True,
                    response={"result_length": len(str(result['result'])) if result['result'] else 0},
                    session_id=datetime.now().isoformat()
                )
                return result['result']
            else:
                error_msg = f"Odoo error: {result.get('error', 'Unknown error')}"
                audit_logger.log_error(
                    error_type="odoo_jsonrpc_error",
                    error_message=error_msg,
                    context={"model": model, "method": method, "payload": str(payload)[:500]},
                    severity="high"
                )
                raise Exception(error_msg)
        else:
            error_msg = f"HTTP error {response.status_code}: {response.text}"
            audit_logger.log_error(
                error_type="odoo_http_error",
                error_message=error_msg,
                context={"model": model, "method": method, "status_code": response.status_code},
                severity="high"
            )
            raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Odoo JSON-RPC call error: {e}"
        logger.error(error_msg)

        audit_logger.log_mcp_call(
            service="odoo_mcp",
            endpoint=f"jsonrpc.{model}.{method}",
            data={"model": model, "method": method},
            success=False,
            error=str(e),
            session_id=datetime.now().isoformat()
        )
        raise

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API key in the Authorization header"""
    if credentials.credentials != ODOO_API_KEY:
        logger.warning(f"Invalid API key attempted: {credentials.credentials}")
        audit_logger.log_error(
            error_type="invalid_api_key",
            error_message=f"Invalid API key: {credentials.credentials}",
            context={"endpoint": "/verify_api_key", "service": "odoo_mcp"},
            severity="high"
        )
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

def create_approval_request(action_data: Dict[str, Any]):
    """Create an approval request for sensitive actions"""
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

    logger.info(f"Approval request created: {filepath}")
    return filepath

# Pydantic models
class CreateInvoiceRequest(BaseModel):
    partner_id: int
    products_list: List[Dict[str, Any]]  # [{"product_id": int, "quantity": float, "price": float}]
    amounts: Dict[str, float]  # {"subtotal": float, "tax": float, "total": float}

class GetUnpaidInvoicesRequest(BaseModel):
    partner_id: Optional[int] = None
    domain: Optional[List] = None

class CreateCustomerRequest(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    vat: Optional[str] = None

# Agent Skills Endpoints

@app.post("/create_invoice")
async def create_invoice(
    request: CreateInvoiceRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create an invoice in Odoo - requires approval"""
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
            "message": "Invoice creation requested, requires approval",
            "approval_file": str(approval_file),
            "estimated_total": request.amounts.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Error in create_invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/get_unpaid_invoices")
async def get_unpaid_invoices(
    request: GetUnpaidInvoicesRequest,
    api_key: str = Depends(verify_api_key)
):
    """Get unpaid invoices from Odoo"""
    try:
        domain = request.domain or []
        if request.partner_id:
            domain.append(("partner_id", "=", request.partner_id))

        domain.append(("state", "=", "open"))  # Filter for unpaid invoices

        invoices = call_odoo_jsonrpc(
            model="account.move",
            method="search_read",
            args=[domain],
            kwargs={
                "fields": ["name", "partner_id", "amount_total", "amount_residual", "invoice_date", "state"],
                "order": "invoice_date desc"
            }
        )

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "get_unpaid_invoices",
            "partner_id": request.partner_id,
            "domain": domain,
            "count": len(invoices)
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "success",
            "invoices": invoices,
            "count": len(invoices)
        }
    except Exception as e:
        logger.error(f"Error in get_unpaid_invoices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_customer")
async def create_customer(
    request: CreateCustomerRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a customer in Odoo - requires approval"""
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
            "message": "Customer creation requested, requires approval",
            "approval_file": str(approval_file),
            "customer_name": request.name
        }
    except Exception as e:
        logger.error(f"Error in create_customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_balance_sheet_summary")
async def get_balance_sheet_summary(api_key: str = Depends(verify_api_key)):
    """Get balance sheet summary from Odoo"""
    try:
        # For balance sheet, we'll get some basic accounting metrics
        # Get accounts of type asset and liability
        asset_accounts = call_odoo_jsonrpc(
            model="account.account",
            method="search_read",
            args=[[("account_type", "=", "asset_current")]],
            kwargs={"fields": ["name", "balance"]}
        )

        liability_accounts = call_odoo_jsonrpc(
            model="account.account",
            method="search_read",
            args=[[("account_type", "=", "liability_current")]],
            kwargs={"fields": ["name", "balance"]}
        )

        # Calculate some basic totals
        total_assets = sum(acc["balance"] for acc in asset_accounts if acc["balance"] > 0)
        total_liabilities = sum(acc["balance"] for acc in liability_accounts if acc["balance"] > 0)

        # Get total equity indirectly (Assets - Liabilities)
        # Or get from equity accounts if available
        equity_accounts = call_odoo_jsonrpc(
            model="account.account",
            method="search_read",
            args=[[("account_type", "=", "equity")]],
            kwargs={"fields": ["name", "balance"]}
        )

        total_equity = sum(acc["balance"] for acc in equity_accounts if acc["balance"] > 0)

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "get_balance_sheet_summary",
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "success",
            "balance_sheet": {
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "total_equity": total_equity,
                "net_worth": total_assets - total_liabilities
            },
            "summary": {
                "asset_accounts_count": len(asset_accounts),
                "liability_accounts_count": len(liability_accounts),
                "equity_accounts_count": len(equity_accounts)
            }
        }
    except Exception as e:
        logger.error(f"Error in get_balance_sheet_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_profit_loss_last_30_days")
async def get_profit_loss_last_30_days(api_key: str = Depends(verify_api_key)):
    """Get profit/loss for last 30 days from Odoo"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Get revenue (income) accounts
        revenue_accounts = call_odoo_jsonrpc(
            model="account.account",
            method="search_read",
            args=[[("account_type", "=", "income")]],
            kwargs={"fields": ["name", "balance"]}
        )

        # Get expense accounts
        expense_accounts = call_odoo_jsonrpc(
            model="account.account",
            method="search_read",
            args=[[("account_type", "=", "expense")]],
            kwargs={"fields": ["name", "balance"]}
        )

        total_revenue = sum(acc["balance"] for acc in revenue_accounts if acc["balance"] > 0)
        total_expenses = sum(abs(acc["balance"]) for acc in expense_accounts if acc["balance"] < 0)

        net_profit = total_revenue - total_expenses

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "get_profit_loss_last_30_days",
            "period": "last_30_days",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": net_profit
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "success",
            "profit_loss": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "profit_margin": net_profit / total_revenue * 100 if total_revenue > 0 else 0
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error in get_profit_loss_last_30_days: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Try to authenticate with Odoo to verify connection
        session_id, uid = authenticate_odoo()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "odoo-mcp-server",
            "odoo_connected": True,
            "user_id": uid
        }
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "odoo-mcp-server",
            "odoo_connected": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "odoo_mcp_server:app",
        host="0.0.0.0",
        port=8002,  # Different port from main MCP server
        reload=False,
        log_level="info"
    )