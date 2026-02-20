"""
FastAPI MCP Server for external actions
"""
import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from pydantic import BaseModel
from typing import Optional
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mcp_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Employee MCP Server",
    description="Model Context Protocol server for external actions",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# API Key from environment
API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key")

# Pydantic models
class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    html_body: Optional[str] = None

class ActionRequest(BaseModel):
    action_type: str
    parameters: dict

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API key in the Authorization header"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

def send_gmail_smtp(to: str, subject: str, body: str, html_body: Optional[str] = None):
    """Send email using Gmail SMTP"""
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_username or not smtp_password:
        raise Exception("SMTP credentials not configured")

    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to
    msg['Subject'] = subject

    # Add body to email
    if html_body:
        msg.attach(MIMEText(html_body, 'html'))
        # Also add plain text version as fallback
        msg.attach(MIMEText(body, 'plain'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_username, to, text)
        server.quit()
        logger.info(f"Email sent successfully to {to}")
        return {"success": True, "message": f"Email sent to {to}"}
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {str(e)}")
        raise e

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    response = await call_next(request)

    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")

    return response

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "MCP Server is running", "timestamp": datetime.now().isoformat()}

@app.post("/send_email")
async def send_email(request: EmailRequest, api_key: str = Depends(verify_api_key)):
    """
    Send an email via SMTP
    """
    try:
        logger.info(f"Received request to send email to {request.to}")

        result = send_gmail_smtp(
            to=request.to,
            subject=request.subject,
            body=request.body,
            html_body=request.html_body
        )

        # Log the action
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "send_email",
            "to": request.to,
            "subject": request.subject,
            "status": "success"
        }
        logger.info(f"Action log: {json.dumps(log_entry)}")

        return result
    except Exception as e:
        logger.error(f"Error in send_email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/execute_action")
async def execute_action(action: ActionRequest, api_key: str = Depends(verify_api_key)):
    """
    Execute a generic action
    """
    try:
        logger.info(f"Received request to execute action: {action.action_type}")

        # Log the action request
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action.action_type,
            "parameters": action.parameters,
            "status": "executing"
        }
        logger.info(f"Action execution request: {json.dumps(log_entry)}")

        # Handle different action types
        if action.action_type == "send_email":
            # Extract email parameters and call send_email functionality
            email_params = action.parameters
            result = send_gmail_smtp(
                to=email_params.get("to"),
                subject=email_params.get("subject"),
                body=email_params.get("body", ""),
                html_body=email_params.get("html_body")
            )
        elif action.action_type == "log_message":
            # Just log the message
            message = action.parameters.get("message", "")
            logger.info(f"Logged message: {message}")
            result = {"success": True, "message": "Message logged successfully"}
        else:
            # For other actions, just log them
            logger.warning(f"Unknown action type: {action.action_type}")
            result = {"success": True, "message": f"Action {action.action_type} received but not implemented"}

        # Update log entry for completion
        log_entry["status"] = "completed"
        logger.info(f"Action completed: {json.dumps(log_entry)}")

        return result
    except Exception as e:
        logger.error(f"Error in execute_action: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute action: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "mcp-server"
    }

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    import pathlib
    pathlib.Path("logs").mkdir(exist_ok=True)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level="info"
    )