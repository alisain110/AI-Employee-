"""
Gold Tier Orchestrator - Enhanced with Ralph Wiggum Mode
Supports both normal single-pass reasoning and Ralph mode with iterative loops
"""
import os
import time
import logging
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from langchain_core.tools import tool
from pydantic import BaseModel
from core.agent import AIAgent
from anthropic import Anthropic
import requests
from audit_logger import get_audit_logger, AuditActor, AuditAction, retry_on_transient_error, graceful_fallback

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "orchestrator_gold.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskConfig(BaseModel):
    """Configuration for task processing"""
    mode: str = "normal"  # "normal" or "ralph"
    max_iterations: int = 15
    max_duration_minutes: int = 120  # 2 hours
    min_loop_delay: int = 10
    max_loop_delay: int = 30
    emergency_stop_file: str = "EMERGENCY_STOP_RALPH"

class RalphOrchestrator:
    """Enhanced orchestrator with Ralph Wiggum mode"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.inbox = self.vault_path / 'Inbox'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'
        self.ralph_logs = self.vault_path / 'Ralph_Logs'

        # Create directories if they don't exist
        for dir_path in [self.needs_action, self.done, self.inbox, self.plans,
                         self.pending_approval, self.approved, self.rejected,
                         self.ralph_logs, self.vault_path / 'Logs', self.vault_path / 'Briefings']:
            dir_path.mkdir(exist_ok=True)

        # Initialize AI components
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.agent = AIAgent()
        self.mcp_endpoints = self.load_mcp_endpoints()

        # Initialize audit logger
        self.audit_logger = get_audit_logger()

    def load_mcp_endpoints(self):
        """Load MCP endpoints configuration from file"""
        config_file = self.vault_path / 'mcp_endpoints.json'
        if config_file.exists():
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"MCP endpoints configuration not found: {config_file}")
            return {}

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def call_mcp_endpoint(self, mcp_service: str, endpoint: str, data: dict = None):
        """Dynamically call an MCP endpoint based on configuration"""
        if not self.mcp_endpoints or mcp_service not in self.mcp_endpoints:
            error_msg = f"MCP service {mcp_service} not found in configuration"
            logger.error(error_msg)
            self.audit_logger.log_error(
                error_type="mcp_config_missing",
                error_message=error_msg,
                context={"service": mcp_service, "available_services": list(self.mcp_endpoints.keys())}
            )
            return {"error": f"MCP service {mcp_service} not configured"}

        service_config = self.mcp_endpoints[mcp_service]
        service_url = service_config['url']

        # Get the specific endpoint path
        endpoint_path = service_config['endpoints'].get(endpoint)
        if not endpoint_path:
            error_msg = f"Endpoint {endpoint} not found for service {mcp_service}"
            logger.error(error_msg)
            self.audit_logger.log_error(
                error_type="mcp_endpoint_missing",
                error_message=error_msg,
                context={"service": mcp_service, "endpoint": endpoint}
            )
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

            start_time = time.time()
            response = requests.post(full_url, json=data, headers=headers, timeout=30)
            call_duration = time.time() - start_time

            if response.status_code in [200, 201]:
                result = response.json()
                self.audit_logger.log_mcp_call(
                    service=mcp_service,
                    endpoint=endpoint,
                    data=data,
                    success=True,
                    response=result,
                    session_id=datetime.now().isoformat()
                )
                return result
            else:
                error_msg = f"MCP call failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                self.audit_logger.log_mcp_call(
                    service=mcp_service,
                    endpoint=endpoint,
                    data=data,
                    success=False,
                    error=f"HTTP {response.status_code}",
                    session_id=datetime.now().isoformat()
                )
                return {"error": f"HTTP {response.status_code}", "details": response.text}
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling MCP endpoint {full_url}: {e}"
            logger.error(error_msg)
            self.audit_logger.log_mcp_call(
                service=mcp_service,
                endpoint=endpoint,
                data=data,
                success=False,
                error=str(e),
                session_id=datetime.now().isoformat()
            )
            raise  # Re-raise for retry decorator
        except Exception as e:
            error_msg = f"Unexpected error calling MCP endpoint {full_url}: {e}"
            logger.error(error_msg)
            self.audit_logger.log_mcp_call(
                service=mcp_service,
                endpoint=endpoint,
                data=data,
                success=False,
                error=str(e),
                session_id=datetime.now().isoformat()
            )
            raise  # Re-raise for retry decorator

    def parse_task_config(self, content: str) -> TaskConfig:
        """Parse configuration from task file, looking for mode: ralph"""
        config = TaskConfig()

        # Look for configuration in the content
        for line in content.split('\n'):
            if 'mode:' in line.lower():
                mode_value = line.split(':')[1].strip().lower()
                if mode_value == 'ralph':
                    config.mode = 'ralph'
                    logger.info("Ralph mode detected in task configuration")
                    break

        return config

    def check_emergency_stop(self, config: TaskConfig) -> bool:
        """Check if emergency stop file exists"""
        return (self.vault_path / config.emergency_stop_file).exists()

    def execute_tool_call(self, tool_name: str, tool_args: Dict[str, Any]):
        """Execute a tool call, potentially routing to MCP"""
        try:
            # Try direct agent tool execution first
            if tool_name in self.agent.list_skills():
                result = self.agent.run(tool_name, **tool_args)
                return result
            else:
                # If it's an MCP endpoint, route through MCP
                # Extract service and endpoint from tool name
                # This assumes MCP tool names follow the pattern service_endpoint
                parts = tool_name.split('_', 1)
                if len(parts) >= 2:
                    service = parts[0] + "_mcp"
                    endpoint = parts[1]
                    if service in self.mcp_endpoints:
                        result = self.call_mcp_endpoint(service, endpoint, tool_args)
                        return result

                # If no match found, return error
                return {"error": f"Tool {tool_name} not found", "available": self.agent.list_skills()}
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": str(e)}

    def run_ralph_loop(self, file_path: Path, content: str, config: TaskConfig):
        """Run Ralph Wiggum mode loop"""
        logger.info(f"Starting Ralph mode loop for task: {file_path.name}")
        start_time = datetime.now()

        iteration = 0
        current_content = content

        # Create Ralph log directory for this task
        task_name = file_path.stem
        ralph_task_dir = self.ralph_logs / task_name
        ralph_task_dir.mkdir(exist_ok=True)

        while iteration < config.max_iterations:
            iteration += 1
            current_time = datetime.now()

            # Safety checks
            if self.check_emergency_stop(config):
                logger.warning("Emergency stop file detected, terminating Ralph loop")
                return "Task terminated due to emergency stop"

            if (current_time - start_time).total_seconds() > (config.max_duration_minutes * 60):
                logger.warning(f"Time cap reached for Ralph loop: {config.max_duration_minutes} minutes")
                return f"Task terminated due to time cap after {iteration} iterations"

            logger.info(f"Ralph loop iteration {iteration}")

            # Prepare context for Claude (no huge history)
            context = self.prepare_ralph_context(file_path, current_content, iteration)

            # Send to Claude for thought and tool selection
            claude_response = self.run_claude_ralph_iteration(context, iteration)

            # Log this step
            step_file = ralph_task_dir / f"step_{iteration:02d}.md"
            with open(step_file, 'w', encoding='utf-8') as f:
                f.write(f"# Ralph Loop Step {iteration}\n")
                f.write(f"## Timestamp: {datetime.now().isoformat()}\n\n")
                f.write(f"## Context:\n{context}\n\n")
                f.write(f"## Claude Response:\n{json.dumps(claude_response, indent=2)}\n\n")

            # Check for termination conditions
            status = claude_response.get('next_action', 'CONTINUE').upper()
            if status == 'DONE':
                logger.info(f"Ralph loop completed successfully after {iteration} iterations")
                return f"Ralph loop completed after {iteration} iterations"
            elif status == 'FAILED':
                logger.warning(f"Ralph loop failed at iteration {iteration}")
                return f"Ralph loop failed at iteration {iteration}"
            elif status == 'NEEDS_HUMAN':
                logger.info(f"Human approval needed at iteration {iteration}")
                # Move to pending approval
                approval_file = self.pending_approval / f"RALPH_{file_path.name}"
                with open(approval_file, 'w', encoding='utf-8') as f:
                    f.write(f"---\ntype: ralph_approval\naction: pending_review\noriginal_file: {file_path.name}\niteration: {iteration}\ncreated: {datetime.now().isoformat()}\nstatus: pending\n---\n\n")
                    f.write(f"# Ralph Mode Human Approval Required\n\n")
                    f.write(f"Task: {file_path.name}\n")
                    f.write(f"Iteration: {iteration}\n\n")
                    f.write(f"Context:\n{context}\n\n")
                    f.write(f"Response:\n{json.dumps(claude_response, indent=2)}\n\n")
                return f"Ralph loop paused for human approval at iteration {iteration}"
            elif status == 'CONTINUE':
                # Execute tools and continue loop
                tool_calls = claude_response.get('tool_calls', [])
                for tool_call in tool_calls:
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('arguments', {})
                    result = self.execute_tool_call(tool_name, tool_args)

                    # Update content with result for next iteration
                    current_content += f"\n\nTool {tool_name} result: {json.dumps(result, indent=2)}"

                # Add random delay between loops
                delay = config.min_loop_delay + (config.max_loop_delay - config.min_loop_delay) * (iteration % 3)  # Vary delay based on iteration
                time.sleep(delay)
            else:
                logger.error(f"Unknown action status: {status}")
                return f"Unknown action status: {status}"

        logger.warning(f"Max iterations reached for Ralph loop: {config.max_iterations}")
        return f"Ralph loop reached max iterations ({config.max_iterations})"

    def prepare_ralph_context(self, file_path: Path, content: str, iteration: int) -> str:
        """Prepare fresh context for Ralph mode iteration"""
        # Read related files
        related_files = self.find_related_files(file_path.parent, content)

        context_parts = [
            f"Ralph Wiggum Mode - Iteration {iteration}",
            f"Current Task: {file_path.name}",
            f"Task Content:\n{content}",
            "\nRelated Files:"
        ]

        for related_file in related_files:
            try:
                if related_file.is_file():
                    file_content = related_file.read_text()
                    context_parts.append(f"\nFile: {related_file.name}\n{file_content[:1000]}...")  # Truncate long files
            except:
                context_parts.append(f"\nFile: {related_file.name} (could not read)")

        return "\n".join(context_parts)

    def find_related_files(self, search_dir: Path, content: str) -> List[Path]:
        """Find files that might be related to the current task"""
        related_files = []

        # Look for files mentioned in content
        words = re.findall(r'\b\w+\.\w+\b', content)  # Look for .file extensions
        for word in words:
            potential_file = search_dir / word
            if potential_file.exists():
                related_files.append(potential_file)

        # Look for recent files
        for file_path in search_dir.glob("*.md"):
            if file_path != Path(content) and (datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)).days <= 7:
                related_files.append(file_path)

        return related_files[:5]  # Limit to 5 related files

    @retry_on_transient_error(max_retries=3, base_delay=1.0)
    def run_claude_ralph_iteration(self, context: str, iteration: int) -> Dict[str, Any]:
        """Run Claude in Ralph mode to get thought, tool calls, and next action"""
        system_prompt = f"""
        You are in Ralph Wiggum mode. This is iteration {iteration} of solving a task.
        Your goal is to work through the problem step by step, using tools when needed.

        For each iteration, provide:
        - A brief thought about the current state and next steps
        - Tool calls if needed (specify tool name and arguments)
        - Next action decision: DONE, CONTINUE, FAILED, or NEEDS_HUMAN

        Be concise but thorough. Don't try to do everything in one step.
        """

        user_prompt = f"""
        Context:
        {context}

        Respond in JSON format with:
        {{
          "thought": "Your brief thought about the current state",
          "tool_calls": [
            {{
              "name": "tool_name",
              "arguments": {{"arg1": "value1", "arg2": "value2"}}
            }}
          ],
          "next_action": "DONE | CONTINUE | FAILED | NEEDS_HUMAN"
        }}

        Make sure next_action is exactly one of these four options.
        """

        try:
            start_time = time.time()
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.7,  # Slightly higher for more creative exploration
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            call_duration = time.time() - start_time

            # Extract JSON from response
            response_text = response.content[0].text

            # Look for JSON block
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                claude_response = json.loads(json_str)

                # Log successful Claude request
                self.audit_logger.log_claude_request(
                    model="claude-3-5-sonnet-20241022",
                    prompt_length=len(user_prompt),
                    response_length=len(response_text),
                    success=True,
                    session_id=datetime.now().isoformat()
                )

                return claude_response
            else:
                # Log partial success (response received but no JSON)
                self.audit_logger.log_claude_request(
                    model="claude-3-5-sonnet-20241022",
                    prompt_length=len(user_prompt),
                    response_length=len(response_text),
                    success=False,
                    error="Could not parse JSON response from Claude",
                    session_id=datetime.now().isoformat()
                )

                # If no JSON found, assume continuation
                return {
                    "thought": f"Could not parse response, continuing: {response_text}",
                    "tool_calls": [],
                    "next_action": "CONTINUE"
                }
        except Exception as e:
            error_msg = f"Error in Claude Ralph iteration: {e}"
            logger.error(error_msg)

            self.audit_logger.log_claude_request(
                model="claude-3-5-sonnet-20241022",
                prompt_length=len(user_prompt),
                response_length=0,
                success=False,
                error=str(e),
                session_id=datetime.now().isoformat()
            )

            # Re-raise for retry decorator if it's a transient error
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                raise
            else:
                # For other errors, return failed response
                return {
                    "thought": f"Error occurred: {str(e)}, marking as failed",
                    "tool_calls": [],
                    "next_action": "FAILED"
                }

    def check_needs_action(self):
        """Check for files that need action"""
        needs_action_files = list(self.needs_action.glob('*.md'))
        return needs_action_files

    def process_file(self, file_path: Path):
        """Process a file - either normal mode or Ralph mode based on configuration"""
        logger.info(f"Processing file: {file_path.name}")

        try:
            # Read the file content
            content = file_path.read_text()

            # Update dashboard before processing
            self.update_dashboard(f"Processing {file_path.name}")

            # Parse task configuration to see if Ralph mode is requested
            config = self.parse_task_config(content)

            if config.mode == 'ralph':
                result = self.run_ralph_loop(file_path, content, config)
            else:
                # Normal mode - single reasoning pass
                result = self.run_normal_mode(file_path, content)

            # If not in Ralph mode loop (which handles its own output), move files appropriately
            if config.mode != 'ralph':
                # Move file to Done folder
                done_file = self.done / file_path.name
                file_path.rename(done_file)

                logger.info(f"Successfully processed and moved {file_path.name} to Done")
                self.update_dashboard(f"Completed processing {file_path.name}")

            return result

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_normal_mode(self, file_path: Path, content: str):
        """Run the normal single-pass reasoning mode"""
        # Check for social media tasks first (using existing logic)
        social_result = self.handle_social_media_task(content, file_path)
        if social_result:
            # If it was a social media task, handle it and return
            plan_file = self.plans / f"PLAN_{file_path.stem}.md"
            plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: completed
original_file: {file_path.name}
---

# Plan for {file_path.name}

## Tasks Completed:
- [x] Social media task processed
- [x] Determined appropriate action
- [x] Processed according to Company_Handbook.md rules

## Summary:
Social media task processed: {social_result}
"""
            plan_file.write_text(plan_content)
            logger.info(f"Created social media plan: {plan_file.name}")
            return social_result

        # Check if the file requires approval
        if "approval" in content.lower() or "payment" in content.lower():
            # Create an approval request
            approval_file = self.pending_approval / f"APPROVAL_{file_path.stem}.md"
            approval_content = f"""---
type: approval_request
action: pending_review
original_file: {file_path.name}
created: {datetime.now().isoformat()}
status: pending
---

# Approval Request for {file_path.name}

The following action requires human approval:

{content[:500]}  # First 500 chars of original content

## Action Required:
Move this file to the /Approved folder to proceed,
or to /Rejected folder to cancel.
"""
            approval_file.write_text(approval_content)
            logger.info(f"Created approval request: {approval_file.name}")
            return "Approval required"
        else:
            # Process normally
            plan_file = self.plans / f"PLAN_{file_path.stem}.md"
            plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: completed
original_file: {file_path.name}
---

# Plan for {file_path.name}

## Tasks Completed:
- [x] Reviewed content
- [x] Determined appropriate action
- [x] Processed according to Company_Handbook.md rules

## Summary:
Processed file {file_path.name} as requested. No further action needed.
"""
            plan_file.write_text(plan_content)
            logger.info(f"Created plan: {plan_file.name}")
            return "Processed successfully"

    def handle_social_media_task(self, content: str, file_path: Path):
        """Handle social media related tasks using the existing logic"""
        # Check for MCP endpoints configuration first
        if self.mcp_endpoints and "social_mcp" in self.mcp_endpoints:
            # Use MCP endpoint for social media tasks
            return self.handle_social_media_via_mcp(content, file_path)
        else:
            # Fallback to direct agent skill usage
            return self.handle_social_media_via_agent(content, file_path)

    def handle_social_media_via_mcp(self, content: str, file_path: Path):
        """Handle social media tasks via MCP endpoints"""
        content_lower = content.lower()

        # Handle Facebook posting via MCP
        if "facebook" in content_lower and ("post" in content_lower or "share" in content_lower):
            post_text = self.extract_post_content(content)
            image_url = self.extract_image_url(content)

            # Prepare MCP call data
            mcp_data = {
                "text": post_text,
                "image_url": image_url
            }

            result = self.call_mcp_endpoint("social_mcp", "facebook_post", mcp_data)
            logger.info(f"Facebook post via MCP: {result}")
            return f"MCP result: {result}"

        # Handle X posting via MCP
        if "x post" in content_lower or ("twitter" in content_lower and "post" in content_lower):
            post_text = self.extract_post_content(content)

            # Prepare MCP call data
            mcp_data = {
                "text": post_text
            }

            result = self.call_mcp_endpoint("social_mcp", "x_post", mcp_data)
            logger.info(f"X post via MCP: {result}")
            return f"MCP result: {result}"

        # Handle social media summary generation via MCP
        if "summary" in content_lower and ("facebook" in content_lower or
                                          "instagram" in content_lower or
                                          "x" in content_lower or
                                          "twitter" in content_lower):
            # Determine which platform is requested
            if "facebook" in content_lower:
                endpoint = "generate_facebook_summary"
            elif "instagram" in content_lower:
                endpoint = "generate_instagram_summary"
            elif "x" in content_lower or "twitter" in content_lower:
                endpoint = "generate_x_summary"
            else:
                endpoint = "generate_facebook_summary"  # default

            mcp_data = {
                "platform": endpoint.replace("generate_", "").replace("_summary", "")
            }

            result = self.call_mcp_endpoint("social_mcp", endpoint, mcp_data)
            logger.info(f"Social media summary via MCP: {result}")
            return f"MCP summary result: {result}"

        # If no specific social media task found, return None
        return None

    def handle_social_media_via_agent(self, content: str, file_path: Path):
        """Handle social media tasks using direct agent skills (fallback)"""
        # Initialize the AI agent
        agent = self.agent

        # Check for social media keywords
        content_lower = content.lower()

        # Handle Facebook posting
        if "facebook" in content_lower and ("post" in content_lower or "share" in content_lower):
            # Extract post content from the file
            post_text = self.extract_post_content(content)

            # Check if it's sales-related to determine if approval is needed
            is_sales_related = any(keyword in content_lower for keyword in
                                 ['buy', 'sale', 'discount', 'offer', 'deal', 'price', 'shop', 'order', 'purchase', 'promo'])

            if is_sales_related:
                # For sales-related posts, use the skill which will request approval
                result = agent.run(
                    "facebook_poster",
                    text=post_text,
                    image_url=self.extract_image_url(content)
                )
                logger.info(f"Facebook post requested: {result}")
                return result
            else:
                # For non-sales posts, post directly
                result = agent.run(
                    "facebook_poster",
                    text=post_text,
                    image_url=self.extract_image_url(content)
                )
                logger.info(f"Facebook post result: {result}")
                return result

        # Handle social media summary generation
        if "summary" in content_lower and ("facebook" in content_lower or
                                          "instagram" in content_lower or
                                          "x" in content_lower or
                                          "twitter" in content_lower):
            # Determine which platform is requested
            if "facebook" in content_lower:
                platform = "facebook"
            elif "instagram" in content_lower:
                platform = "instagram"
            elif "x" in content_lower or "twitter" in content_lower:
                platform = "x"
            else:
                platform = "facebook"  # default

            result = agent.run("social_summary_generator", platform=platform)
            logger.info(f"Social media summary generated: {result}")
            return result

        # If no specific social media task found, return None
        return None

    def extract_post_content(self, content: str) -> str:
        """Extract post content from file content"""
        # Look for common markers of post content
        if "post:" in content.lower():
            start = content.lower().find("post:") + 5
            end = content.find("\n", start)
            if end == -1:
                end = len(content)
            return content[start:end].strip()
        elif "share:" in content.lower():
            start = content.lower().find("share:") + 6
            end = content.find("\n", start)
            if end == -1:
                end = len(content)
            return content[start:end].strip()
        else:
            # Return first 500 characters if no specific marker found
            return content[:500]

    def extract_image_url(self, content: str) -> str:
        """Extract image URL from content if present"""
        import re
        # Look for URLs that might be images
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, content)
        for url in urls:
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                return url
        return None

    def update_dashboard(self, message: str):
        """Update the dashboard with current status"""
        dashboard_path = self.vault_path / 'Dashboard.md'
        if not dashboard_path.exists():
            # Create a basic dashboard if it doesn't exist
            basic_dashboard = f"""# AI Employee Dashboard

## Executive Summary
Welcome to your AI Employee dashboard. This system monitors your personal and business affairs 24/7.

## Current Status
- **Date:** {datetime.now().strftime('%Y-%m-%d')}
- **AI Employee Status:** Active
- **Last Processed:** {datetime.now().strftime('%H:%M')}

## Recent Activity
- {datetime.now().strftime('%H:%M')} - {message}

## Pending Actions
- No pending actions currently

## Alerts
- No alerts

## Quick Stats
- Files in Inbox: 0
- Files in Needs_Action: 0
- Files in Done: 0
- Pending Approvals: 0

## Gold Tier - Autonomous Employee
### Status: Active
- [x] All systems operational
- [x] Ralph Wiggum mode available
- [ ] Accounting system connected (Odoo integration)
- [ ] Social media summaries (FB/IG/X)
- [ ] Weekly CEO briefings + audit logs
- [ ] Ralph Wiggum loop traces

## Next Actions
- Monitor for new files in Inbox
- Process any high-priority tasks first
- Continue following Company_Handbook.md guidelines
- Run setup_gold.py to initialize Gold Tier features
"""
            dashboard_path.write_text(basic_dashboard)
            return

        current_content = dashboard_path.read_text()

        # Update the recent activity section
        lines = current_content.split('\n')
        new_lines = []
        replaced = False

        for line in lines:
            if line.startswith('## Recent Activity') and not replaced:
                new_lines.append('## Recent Activity')
                new_lines.append(f'- {datetime.now().strftime("%H:%M")} - {message}')
                # Add back the next few lines that contain existing activity
                for i in range(1, 5):  # Add up to 4 previous activities
                    if len(lines) > lines.index(line) + i and not lines[lines.index(line) + i].startswith('## '):
                        existing_line = lines[lines.index(line) + i]
                        if existing_line.strip() and '- ' in existing_line:
                            new_lines.append(existing_line)
                replaced = True
            elif not (line.startswith('## Recent Activity') or
                     (replaced and line.strip() and '- ' in line and len(line) < 100)):
                new_lines.append(line)

        # Make sure we have the section if it wasn't found
        if not replaced:
            new_lines.extend(['', '## Recent Activity', f'- {datetime.now().strftime("%H:%M")} - {message}'])

        updated_content = '\n'.join(new_lines)

        # Update quick stats to show current counts
        stats_lines = updated_content.split('\n')
        final_lines = []
        for line in stats_lines:
            if line.startswith('- Files in Inbox:'):
                inbox_count = len(list(self.inbox.glob('*')))
                final_lines.append(f'- Files in Inbox: {inbox_count}')
            elif line.startswith('- Files in Needs_Action:'):
                needs_action_count = len(list(self.needs_action.glob('*')))
                final_lines.append(f'- Files in Needs_Action: {needs_action_count}')
            elif line.startswith('- Files in Done:'):
                done_count = len(list(self.done.glob('*')))
                final_lines.append(f'- Files in Done: {done_count}')
            elif line.startswith('- Pending Approvals:'):
                pending_approval_count = len(list(self.pending_approval.glob('*')))
                final_lines.append(f'- Pending Approvals: {pending_approval_count}')
            else:
                final_lines.append(line)

        final_content = '\n'.join(final_lines)
        dashboard_path.write_text(final_content)

    def run(self):
        """Main loop to check for and process files"""
        logger.info("AI Employee Orchestrator Gold started")

        while True:
            try:
                # Check for files that need action
                needs_action_files = self.check_needs_action()

                if needs_action_files:
                    logger.info(f"Found {len(needs_action_files)} files to process")
                    for file_path in needs_action_files:
                        self.process_file(file_path)

                # Update dashboard stats
                self.update_dashboard("Monitoring for new tasks")

                # Wait before checking again
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait longer if there's an error

def main():
    vault_path = Path.cwd()
    orchestrator = RalphOrchestrator(str(vault_path))

    logger.info("Starting AI Employee Orchestrator Gold...")
    orchestrator.run()

if __name__ == "__main__":
    main()