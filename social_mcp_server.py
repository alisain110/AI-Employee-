"""
Social MCP Server - Model Context Protocol server for social media operations
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

from audit_logger import get_audit_logger, AuditActor, AuditAction, retry_on_transient_error

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "social_mcp_actions.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Social MCP Server",
    description="Model Context Protocol server for social media operations",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# API Key from environment
SOCIAL_API_KEY = os.getenv("SOCIAL_API_KEY", "your-social-mcp-api-key")

# Initialize audit logger
audit_logger = get_audit_logger()

# Pending approval directory
pending_approval_dir = Path("Pending_Approval")
pending_approval_dir.mkdir(exist_ok=True)

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the API key in the Authorization header"""
    if credentials.credentials != SOCIAL_API_KEY:
        logger.warning(f"Invalid API key attempted: {credentials.credentials}")
        audit_logger.log_error(
            error_type="invalid_api_key",
            error_message=f"Invalid API key: {credentials.credentials}",
            context={"endpoint": "/verify_api_key"},
            severity="high"
        )
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return credentials.credentials

def create_approval_request(action_data: Dict[str, Any]):
    """Create an approval request for sensitive actions"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"social_approval_{timestamp}_{action_data.get('action', 'generic')}.json"
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
class FacebookPostRequest(BaseModel):
    text: str
    image_url: Optional[str] = None
    page_id: Optional[str] = None
    access_token: Optional[str] = None

class XPostRequest(BaseModel):
    text: str
    media_ids: Optional[List[str]] = None
    reply_to: Optional[str] = None

class SocialSummaryRequest(BaseModel):
    platform: str  # facebook, instagram, x

@retry_on_transient_error(max_retries=3, base_delay=1.0)
@app.post("/facebook_post")
async def facebook_post(
    request: FacebookPostRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Process Facebook post request via agent skill"""
    try:
        # Import the agent skill directly to handle the post
        from skills.facebook_poster import facebook_poster

        # Log the MCP call
        audit_logger.log_mcp_call(
            service="social_mcp",
            endpoint="facebook_post",
            data={"text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                  "has_image": bool(request.image_url),
                  "page_id": request.page_id},
            success=True,
            session_id=datetime.now().isoformat()
        )

        # Check if the post is sales-related to determine if approval is needed
        sales_keywords = ['buy', 'sale', 'discount', 'offer', 'deal', 'price', 'shop', 'order', 'purchase', 'promo']
        is_sales_related = any(keyword in request.text.lower() for keyword in sales_keywords)

        if is_sales_related:
            # Create approval request for sales-related posts
            approval_data = {
                "action": "facebook_post",
                "text": request.text,
                "image_url": request.image_url,
                "page_id": request.page_id,
                "is_sales_related": True
            }

            approval_file = create_approval_request(approval_data)

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "facebook_post_requested",
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "approval_file": str(approval_file)
            }
            logger.info(json.dumps(log_entry))

            return {
                "status": "approval_requested",
                "message": "Facebook post requested, requires approval",
                "approval_file": str(approval_file)
            }
        else:
            # For non-sales posts, call the skill directly
            result = facebook_poster(
                text=request.text,
                image_url=request.image_url,
                page_id=request.page_id,
                access_token=request.access_token
            )

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "facebook_post",
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "result": result
            }
            logger.info(json.dumps(log_entry))

            return {
                "status": "success",
                "result": result
            }

    except Exception as e:
        error_msg = f"Error in facebook_post: {e}"
        logger.error(error_msg)

        audit_logger.log_error(
            error_type="facebook_post_error",
            error_message=str(e),
            context={"endpoint": "/facebook_post", "text_preview": request.text[:100]},
            severity="high"
        )

        # Log the failed MCP call
        audit_logger.log_mcp_call(
            service="social_mcp",
            endpoint="facebook_post",
            data={"text": request.text[:100] + "..." if len(request.text) > 100 else request.text},
            success=False,
            error=str(e),
            session_id=datetime.now().isoformat()
        )

        raise HTTPException(status_code=500, detail=str(e))

@retry_on_transient_error(max_retries=3, base_delay=1.0)
@app.post("/x_post")
async def x_post(
    request: XPostRequest,
    api_key: str = Depends(verify_api_key),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Process X (Twitter) post request via agent skill"""
    try:
        from skills.x_poster_and_summary import post_tweet

        # Log the MCP call
        audit_logger.log_mcp_call(
            service="social_mcp",
            endpoint="x_post",
            data={"text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                  "has_media": bool(request.media_ids),
                  "reply_to": request.reply_to},
            success=True,
            session_id=datetime.now().isoformat()
        )

        # Check if the post is sensitive
        sensitive_keywords = ['buy', 'sale', 'discount', 'offer', 'deal', 'price', 'shop', 'order', 'purchase', 'promo', 'hate', 'angry', 'kill', 'harm']
        is_sensitive = any(keyword in request.text.lower() for keyword in sensitive_keywords)

        if is_sensitive:
            # Create approval request for sensitive posts
            approval_data = {
                "action": "x_post",
                "text": request.text,
                "media_ids": request.media_ids,
                "reply_to": request.reply_to,
                "is_sensitive": True
            }

            approval_file = create_approval_request(approval_data)

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "x_post_requested",
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "approval_file": str(approval_file)
            }
            logger.info(json.dumps(log_entry))

            return {
                "status": "approval_requested",
                "message": "X post requested, requires approval",
                "approval_file": str(approval_file)
            }
        else:
            # For non-sensitive posts, call the skill directly
            result = post_tweet(
                text=request.text,
                media_ids=request.media_ids,
                reply_to=request.reply_to
            )

            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": "x_post",
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "result": result
            }
            logger.info(json.dumps(log_entry))

            return {
                "status": "success",
                "result": result
            }

    except Exception as e:
        error_msg = f"Error in x_post: {e}"
        logger.error(error_msg)

        audit_logger.log_error(
            error_type="x_post_error",
            error_message=str(e),
            context={"endpoint": "/x_post", "text_preview": request.text[:100]},
            severity="high"
        )

        # Log the failed MCP call
        audit_logger.log_mcp_call(
            service="social_mcp",
            endpoint="x_post",
            data={"text": request.text[:100] + "..." if len(request.text) > 100 else request.text},
            success=False,
            error=str(e),
            session_id=datetime.now().isoformat()
        )

        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_facebook_summary")
async def generate_facebook_summary(
    request: SocialSummaryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate Facebook summary via agent skill"""
    try:
        from skills.social_summary_generator import social_summary_generator

        result = social_summary_generator(platform="facebook")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "generate_facebook_summary",
            "result": result
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error in generate_facebook_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_x_summary")
async def generate_x_summary(
    request: SocialSummaryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate X (Twitter) summary via agent skill"""
    try:
        from skills.social_summary_generator import social_summary_generator

        result = social_summary_generator(platform="x")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "generate_x_summary",
            "result": result
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error in generate_x_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_instagram_summary")
async def generate_instagram_summary(
    request: SocialSummaryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Generate Instagram summary via agent skill"""
    try:
        from skills.social_summary_generator import social_summary_generator

        result = social_summary_generator(platform="instagram")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "generate_instagram_summary",
            "result": result
        }
        logger.info(json.dumps(log_entry))

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"Error in generate_instagram_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "social-mcp-server"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "social_mcp_server:app",
        host="0.0.0.0",
        port=8003,  # Social MCP server on port 8003
        reload=False,
        log_level="info"
    )