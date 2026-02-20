"""
Gmail Draft MCP Server - Model Context Protocol server for draft email operations
Cloud-only version that creates drafts but doesn't send emails
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
        logging.FileHandler(logs_dir / "gmail_draft_actions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gmail Draft MCP Server",
    description="Model Context Protocol server for draft email operations (cloud-only)",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# API Key from environment
GMAIL_API_KEY = os.getenv("GMAIL_DRAFT_API_KEY", "your-gmail-draft-api-key")

# Pending approval directory (cloud-specific)
pending_approval_dir = Path("Pending_Approval") / "cloud"
pending_approval_dir.mkdir(parents=True, exist_ok=True)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API key in the Authorization header"""
    if credentials.credentials != GMAIL_API_KEY:
        logger.warning(f"Invalid API key attempted: {credentials.credentials}")
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

def create_approval_request(action_data: Dict[str, Any]):
    """Create an approval request for email sending (requires local execution)"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"email_approval_{timestamp}_{action_data.get('action', 'generic')}.json"
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

    logger.info(f"Email approval request created: {filepath}")
    return filepath

# Pydantic models
class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

class CreateDraftRequest(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None

class SearchEmailsRequest(BaseModel):
    query: str
    max_results: Optional[int] = 10

@app.post("/send_email")
async def send_email(
    request: SendEmailRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Create an approval request for sending email (cloud only - no actual sending)
    """
    try:
        # Instead of sending, create an approval request
        approval_data = {
            "action": "send_email",
            "to": request.to,
            "subject": request.subject,
            "body_preview": request.body[:200] + "..." if len(request.body) > 200 else request.body,
            "cc": request.cc,
            "bcc": request.bcc
        }

        approval_file = create_approval_request(approval_data)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "email_send_requested",
            "to": request.to,
            "subject": request.subject,
            "approval_file": str(approval_file)
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "approval_requested",
            "message": "Email send requested, requires local approval",
            "approval_file": str(approval_file)
        }

    except Exception as e:
        logger.error(f"Error in send_email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create_draft")
async def create_draft(
    request: CreateDraftRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Create a draft email (cloud only - stores as file for local processing)
    """
    try:
        # Create a draft file in the local system for later processing
        drafts_dir = Path("Drafts")
        drafts_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_filename = f"draft_{timestamp}_{len(request.to[:10])}.json"
        draft_file = drafts_dir / draft_filename

        draft_data = {
            "timestamp": datetime.now().isoformat(),
            "to": request.to,
            "subject": request.subject,
            "body": request.body,
            "cc": request.cc,
            "bcc": request.bcc,
            "status": "draft_created_cloud"
        }

        with open(draft_file, 'w') as f:
            json.dump(draft_data, f, indent=2)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "email_draft_created",
            "to": request.to,
            "subject": request.subject,
            "draft_file": str(draft_file)
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "draft_created",
            "message": "Draft email created in cloud",
            "draft_file": str(draft_file)
        }

    except Exception as e:
        logger.error(f"Error in create_draft: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search_emails")
async def search_emails(
    request: SearchEmailsRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Search for emails (cloud only - would require local mailbox access in real implementation)
    """
    try:
        # This would normally connect to Gmail API for searching
        # For cloud implementation, we return a placeholder
        # In real system, this would require the actual email system

        result = {
            "status": "search_completed",
            "query": request.query,
            "results_count": 0,
            "message": "Search functionality requires local email access. Cloud provides draft capability only."
        }

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "email_search",
            "query": request.query,
            "max_results": request.max_results
        }
        logger.info(json.dumps(log_entry))

        return result

    except Exception as e:
        logger.error(f"Error in search_emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "gmail-draft-mcp-server",
        "cloud_only": True,
        "draft_mode": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "gmail_draft_mcp:app",
        host="0.0.0.0",
        port=8004,  # Gmail Draft MCP server on port 8004
        reload=False,
        log_level="info"
    )