"""
MCP Client Skill - Connects to local MCP server to perform external actions
"""
import os
import requests
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool
import json
from utilities.human_approval import requires_human_approval

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
MCP_API_KEY = os.getenv("MCP_API_KEY", "your-secret-api-key")

def make_mcp_request(endpoint: str, data: dict):
    """Make a request to the MCP server with proper authentication"""
    headers = {
        "Authorization": f"Bearer {MCP_API_KEY}",
        "Content-Type": "application/json"
    }

    url = f"{MCP_SERVER_URL}{endpoint}"

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"MCP server request failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f" - Server returned: {error_detail}"
            except:
                error_msg += f" - Server returned: {e.response.text[:200]}..."
        return {"error": error_msg}

@tool
@requires_human_approval
def send_email_skill(to: str, subject: str, body: str, html_body: Optional[str] = None) -> str:
    """
    Send an email using the MCP server.

    Args:
        to (str): Recipient email address
        subject (str): Email subject
        body (str): Plain text email body
        html_body (Optional[str]): HTML version of email body (optional)

    Returns:
        str: Result message indicating success or failure
    """
    data = {
        "to": to,
        "subject": subject,
        "body": body,
        "html_body": html_body
    }

    result = make_mcp_request("/send_email", data)

    if "error" in result:
        return f"Failed to send email: {result['error']}"
    else:
        return f"Email sent successfully: {result.get('message', 'Unknown status')}"

@tool
@requires_human_approval
def execute_action_skill(action_type: str, parameters: dict) -> str:
    """
    Execute a generic action via the MCP server.

    Args:
        action_type (str): Type of action to execute
        parameters (dict): Parameters for the action

    Returns:
        str: Result message indicating success or failure
    """
    data = {
        "action_type": action_type,
        "parameters": parameters
    }

    result = make_mcp_request("/execute_action", data)

    if "error" in result:
        return f"Failed to execute action: {result['error']}"
    else:
        return f"Action executed successfully: {result.get('message', 'Unknown status')}"

# Also add a simple health check tool
@tool
def mcp_server_health_check() -> str:
    """
    Check if the MCP server is running and accessible.

    Returns:
        str: Health status of the MCP server
    """
    headers = {
        "Authorization": f"Bearer {MCP_API_KEY}"
    }

    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", headers=headers, timeout=10)
        response.raise_for_status()
        health_info = response.json()
        return f"MCP Server is healthy: {json.dumps(health_info)}"
    except requests.exceptions.RequestException as e:
        return f"MCP Server health check failed: {str(e)}"