"""
Approval Executor for Platinum Tier AI Employee Vault
Watches for approved requests in /Approved/ and executes final actions
"""
import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import requests
from core.agent import AIAgent
from audit_logger import get_audit_logger, AuditActor, AuditAction

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "approval_executor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ApprovalExecutor:
    """Executes approved requests from cloud orchestrator"""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.approved_dir = self.vault_path / "Approved"
        self.archived_dir = self.vault_path / "Approved" / "archived"  # Archive executed approvals
        self.rejected_dir = self.vault_path / "Rejected"

        # MCP endpoints for real actions
        self.mcp_endpoints = self.load_mcp_endpoints()

        # Initialize agent for direct skill execution
        self.agent = AIAgent()

        # Initialize audit logger
        self.audit_logger = get_audit_logger()

        # Create directories
        self.archived_dir.mkdir(parents=True, exist_ok=True)

    def load_mcp_endpoints(self):
        """Load MCP endpoints configuration from file"""
        config_file = self.vault_path / 'mcp_endpoints.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"MCP endpoints configuration not found: {config_file}")
            return {}

    def call_mcp_endpoint(self, mcp_service: str, endpoint: str, data: dict = None):
        """Dynamically call an MCP endpoint based on configuration"""
        if not self.mcp_endpoints or mcp_service not in self.mcp_endpoints:
            logger.error(f"MCP service {mcp_service} not found in configuration")
            return {"error": f"MCP service {mcp_service} not configured"}

        service_config = self.mcp_endpoints[mcp_service]
        service_url = service_config['url']

        # Get the specific endpoint path
        endpoint_path = service_config['endpoints'].get(endpoint)
        if not endpoint_path:
            logger.error(f"Endpoint {endpoint} not found for service {mcp_service}")
            return {"error": f"Endpoint {endpoint} not found for service {mcp_service}"}

        full_url = f"{service_url}{endpoint_path}"

        # Prepare headers
        headers = {"Content-Type": "application/json"}

        # Add authentication if required
        if service_config.get('auth_required', False):
            api_key_env = service_config.get('api_key_env')
            if api_key_env:
                api_key = os.getenv(api_key_env)
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                else:
                    logger.warning(f"API key environment variable {api_key_env} not set for {mcp_service}")

        try:
            if data is None:
                data = {}

            response = requests.post(full_url, json=data, headers=headers, timeout=30)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"MCP call failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "details": response.text}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling MCP endpoint {full_url}: {e}")
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error calling MCP endpoint {full_url}: {e}")
            return {"error": str(e)}

    def execute_email_sending(self, approval_data: Dict[str, Any]):
        """Execute real email sending"""
        logger.info("Executing real email sending...")

        try:
            # Get email details from approval data
            email_details = approval_data.get('details', {})
            to = email_details.get('to', '')
            subject = email_details.get('subject', 'No Subject')
            body = email_details.get('body', 'No body')

            # Execute the email sending via agent skill
            result = self.agent.run("gmail_sender_skill", to=to, subject=subject, body=body)

            logger.info(f"Email sent successfully: {result}")

            # Log the action
            self.audit_logger.log_mcp_call(
                service="gmail_sender",
                endpoint="send_email",
                data={"to": to, "subject": subject},
                success=True,
                response=result,
                session_id=datetime.now().isoformat()
            )

            return result
        except Exception as e:
            logger.error(f"Email sending failed: {e}")

            # Log the error
            self.audit_logger.log_error(
                error_type="email_sending_failed",
                error_message=str(e),
                context={"approver_data": approval_data},
                severity="high"
            )

            return f"Error: {str(e)}"

    def execute_odoo_actions(self, approval_data: Dict[str, Any]):
        """Execute real Odoo actions (invoice, customer, etc.)"""
        logger.info("Executing real Odoo action...")

        try:
            action = approval_data.get('action', '')
            details = approval_data.get('details', {})

            if action == 'create_invoice':
                # Execute real invoice creation via MCP
                result = self.call_mcp_endpoint("odoo_mcp", "create_invoice", details)
            elif action == 'create_customer':
                # Execute real customer creation via MCP
                result = self.call_mcp_endpoint("odoo_mcp", "create_customer", details)
            else:
                logger.warning(f"Unknown Odoo action: {action}")
                result = {"error": f"Unknown action: {action}"}

            logger.info(f"Odoo action completed: {result}")

            # Log the action
            self.audit_logger.log_mcp_call(
                service="odoo_mcp",
                endpoint=action,
                data=details,
                success=True,
                response=result,
                session_id=datetime.now().isoformat()
            )

            return result
        except Exception as e:
            logger.error(f"Odoo action failed: {e}")

            # Log the error
            self.audit_logger.log_error(
                error_type="odoo_action_failed",
                error_message=str(e),
                context={"approval_data": approval_data},
                severity="high"
            )

            return f"Error: {str(e)}"

    def execute_social_posting(self, approval_data: Dict[str, Any]):
        """Execute real social media posting"""
        logger.info("Executing real social media posting...")

        try:
            details = approval_data.get('details', {})
            platform = details.get('platform', 'facebook')
            content = details.get('content', '')

            # Execute the social media posting via agent skill
            result = self.agent.run("social_poster_skill", platform=platform, content=content)

            logger.info(f"Social post created successfully: {result}")

            # Log the action
            self.audit_logger.log_mcp_call(
                service="social_poster",
                endpoint="post",
                data={"platform": platform, "content": content},
                success=True,
                response=result,
                session_id=datetime.now().isoformat()
            )

            return result
        except Exception as e:
            logger.error(f"Social posting failed: {e}")

            # Log the error
            self.audit_logger.log_error(
                error_type="social_posting_failed",
                error_message=str(e),
                context={"approval_data": approval_data},
                severity="high"
            )

            return f"Error: {str(e)}"

    def execute_whatsapp_sending(self, approval_data: Dict[str, Any]):
        """Execute real WhatsApp sending"""
        logger.info("Executing real WhatsApp sending...")

        try:
            details = approval_data.get('details', {})
            phone_number = details.get('phone_number', '')
            message = details.get('message', '')

            # Execute the WhatsApp sending via agent skill
            result = self.agent.run("whatsapp_sender_skill", phone_number=phone_number, message=message)

            logger.info(f"WhatsApp message sent successfully: {result}")

            # Log the action
            self.audit_logger.log_mcp_call(
                service="whatsapp_sender",
                endpoint="send_message",
                data={"phone_number": phone_number, "message": message},
                success=True,
                response=result,
                session_id=datetime.now().isoformat()
            )

            return result
        except Exception as e:
            logger.error(f"WhatsApp sending failed: {e}")

            # Log the error
            self.audit_logger.log_error(
                error_type="whatsapp_sending_failed",
                error_message=str(e),
                context={"approval_data": approval_data},
                severity="high"
            )

            return f"Error: {str(e)}"

    def execute_approval(self, approval_file: Path):
        """Execute a single approval request"""
        logger.info(f"Executing approval: {approval_file.name}")

        try:
            # Read the approval file
            content = approval_file.read_text()

            # Parse the approval data
            # This is a simplified approach - in a real system, we'd have structured data
            lines = content.split('\n')
            action_type = None
            details = {}
            details_started = False

            for line in lines:
                if '## Original Content' in line:
                    break  # Stop parsing at original content
                if 'Action:' in line:
                    action_type = line.split('Action:')[1].strip()
                elif line.startswith('- ') and ':' in line:
                    # Parse details like "- action: send_email"
                    if details_started or 'action' in line.lower():
                        parts = line[2:].split(':', 1)  # Remove "- " prefix
                        if len(parts) == 2:
                            key, value = parts
                            details[key.strip().lower()] = value.strip()
                elif '## Request Details' in line:
                    details_started = True

            # Determine execution type based on content
            if 'email' in content.lower() or 'gmail' in content.lower():
                result = self.execute_email_sending({"details": details})
            elif 'odoo' in content.lower() or 'invoice' in content.lower() or 'customer' in content.lower():
                result = self.execute_odoo_actions({"action": action_type or "unknown", "details": details})
            elif any(platform in content.lower() for platform in ['facebook', 'instagram', 'x', 'twitter', 'social']):
                result = self.execute_social_posting({"details": details})
            elif 'whatsapp' in content.lower():
                result = self.execute_whatsapp_sending({"details": details})
            else:
                # For unknown types, log as error
                logger.warning(f"Unknown approval type for {approval_file.name}")
                result = f"Error: Unknown approval type"

            # Archive the processed approval
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_filename = f"executed_{timestamp}_{approval_file.name}"
            archived_file = self.archived_dir / archived_filename
            approval_file.rename(archived_file)

            logger.info(f"Approval executed and archived: {archived_file.name}")
            return result

        except Exception as e:
            logger.error(f"Error executing approval {approval_file.name}: {e}")

            # Move to rejected on error
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rejected_filename = f"error_{timestamp}_{approval_file.name}"
            rejected_file = self.rejected_dir / rejected_filename
            approval_file.rename(rejected_file)

            return f"Error executing approval: {str(e)}"

    def check_approvals(self):
        """Check for approved requests to execute"""
        approval_files = list(self.approved_dir.glob("*.md"))
        # Filter out archived files
        approval_files = [f for f in approval_files if 'archived' not in str(f)]

        return approval_files

    def run(self):
        """Main loop to check for and execute approvals"""
        logger.info("Approval Executor started")

        while True:
            try:
                # Check for approved requests
                approval_files = self.check_approvals()

                if approval_files:
                    logger.info(f"Found {len(approval_files)} approved requests to execute")
                    for approval_file in approval_files:
                        self.execute_approval(approval_file)

                # Wait before checking again
                time.sleep(10)  # Check every 10 seconds

            except KeyboardInterrupt:
                logger.info("Approval Executor stopped by user")
                break
            except Exception as e:
                logger.error(f"Approval Executor error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait longer if there's an error

def main():
    executor = ApprovalExecutor()
    logger.info("Starting Approval Executor...")
    executor.run()

if __name__ == "__main__":
    main()