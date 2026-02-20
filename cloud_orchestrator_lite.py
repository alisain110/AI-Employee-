"""
Cloud Orchestrator Lite for Platinum Tier AI Employee Vault
Lightweight cloud version that handles triage, drafting, and approval requests only
No sensitive actions (no real payment, no final posts, no message sending)
"""
import os
import time
import logging
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from anthropic import Anthropic
import requests

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "cloud_orchestrator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskConfig(BaseModel):
    """Configuration for task processing"""
    mode: str = "normal"  # "normal" or "ralph"
    max_iterations: int = 15
    max_duration_minutes: int = 30  # Shorter time cap for cloud

class CloudOrchestratorLite:
    """Lightweight orchestrator for cloud operations - triage and drafting only"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.inbox = self.vault_path / 'Inbox'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval' / 'cloud'  # Cloud-specific folder
        self.in_progress = self.vault_path / 'In_Progress' / 'cloud'
        self.updates = self.vault_path / 'Updates'

        # Create directories if they don't exist
        for dir_path in [self.needs_action, self.done, self.inbox, self.plans,
                         self.pending_approval, self.in_progress, self.updates,
                         self.vault_path / 'Logs', self.vault_path / 'Briefings']:
            dir_path.mkdir(exist_ok=True)

        # Initialize AI components
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def check_needs_action(self):
        """Check for files that need action (excluding already claimed files)"""
        # Get all files in needs_action
        needs_action_files = list(self.needs_action.glob('*.md'))

        # Filter out files that are already in progress
        in_progress_files = set(f.name for f in self.in_progress.glob('*.md'))
        available_files = [f for f in needs_action_files if f.name not in in_progress_files]

        return available_files

    def claim_task(self, file_path: Path) -> Path:
        """Claim a task by moving it to In_Progress/cloud/"""
        in_progress_file = self.in_progress / file_path.name
        file_path.rename(in_progress_file)
        logger.info(f"Claimed task: {file_path.name}")
        return in_progress_file

    def run_ralph_loop(self, file_path: Path, content: str, config: TaskConfig):
        """Run Ralph Wiggum mode loop for complex multi-step tasks"""
        logger.info(f"Starting Ralph loop for task: {file_path.name}")
        start_time = datetime.now()

        iteration = 0
        current_content = content

        while iteration < config.max_iterations:
            iteration += 1
            current_time = datetime.now()

            # Safety check - time cap
            if (current_time - start_time).total_seconds() > (config.max_duration_minutes * 60):
                logger.warning(f"Time cap reached for Ralph loop: {config.max_duration_minutes} minutes")
                return f"Task terminated due to time cap after {iteration} iterations"

            logger.info(f"Ralph loop iteration {iteration}")

            # Prepare context for Claude (no huge history)
            context = f"""Cloud Ralph Wiggum Mode - Iteration {iteration}
Current Task: {file_path.name}
Task Content:
{current_content}

This is a cloud-only orchestrator. You may only:
- Generate drafts
- Create planning documents
- Create approval requests in /Pending_Approval/cloud/
- Perform read operations via MCP servers
- NEVER execute final actions that affect external systems

Current iteration: {iteration}
"""

            # Send to Claude for thought and decision
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000,
                    temperature=0.7,
                    system="You are in Ralph Wiggum mode on a cloud orchestrator. You can only draft, plan, read, or request approval. Never perform final actions that affect external systems.",
                    messages=[
                        {"role": "user", "content": context}
                    ]
                )

                claude_response = response.content[0].text

                # Look for action indicators in response
                if "DONE" in claude_response.upper():
                    logger.info(f"Ralph loop completed successfully after {iteration} iterations")
                    return f"Ralph loop completed after {iteration} iterations"
                elif "APPROVAL" in claude_response.upper() or "NEEDS HUMAN" in claude_response.upper():
                    # Create approval request
                    self.create_approval_request(file_path, f"Iteration {iteration}: {claude_response}")
                    logger.info(f"Created approval request at iteration {iteration}")
                    return f"Ralph loop paused for approval at iteration {iteration}"
                else:
                    # Update content for next iteration
                    current_content += f"\n\nIteration {iteration} result: {claude_response}"

                # Small delay between iterations
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error in Claude Ralph iteration: {e}")
                return f"Error occurred in iteration {iteration}: {str(e)}"

        logger.warning(f"Max iterations reached for Ralph loop: {config.max_iterations}")
        return f"Ralph loop reached max iterations ({config.max_iterations})"

    def create_approval_request(self, original_file: Path, reason: str):
        """Create an approval request in the cloud-specific folder"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        approval_filename = f"cloud_approval_{timestamp}_{original_file.stem}.md"
        approval_file = self.pending_approval / approval_filename

        approval_content = f"""---
type: cloud_approval_request
action: pending_review
original_file: {original_file.name}
created: {datetime.now().isoformat()}
status: pending
source: cloud_orchestrator
---

# Cloud Approval Request

## Original Task
File: {original_file.name}

## Request Details
- Created by: Cloud Orchestrator Lite
- Time: {datetime.now().isoformat()}
- Reason: {reason}

## Original Content
{original_file.read_text()[:1000]}  # First 1000 chars

## Cloud Action
This requires human approval on the local system before final execution.
"""
        approval_file.write_text(approval_content)
        logger.info(f"Created cloud approval request: {approval_file.name}")

    def process_email_task(self, file_path: Path, content: str):
        """Process email-related tasks - draft replies only"""
        logger.info(f"Processing email task: {file_path.name}")

        # Check if this needs approval
        content_lower = content.lower()

        # Look for sensitive keywords that require approval
        sensitive_keywords = [
            'payment', 'invoice', 'pay', 'purchase', 'order', 'buy',
            'contract', 'agreement', 'legal', 'billing', 'financial'
        ]

        is_sensitive = any(keyword in content_lower for keyword in sensitive_keywords)

        if is_sensitive:
            # Create approval request for sensitive content
            self.create_approval_request(file_path, "Email contains sensitive financial/legal content requiring approval")
            return "Email approval requested"
        else:
            # Generate a draft reply only
            try:
                system_prompt = """You are drafting email replies on a cloud system.
Only create the content of the reply.
Do NOT send the email (that happens locally).
Focus on professional, appropriate responses.
Do NOT include any actual sending functionality."""

                user_prompt = f"""Draft a professional reply to this email:

{content}

Draft reply:"""

                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.5,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                draft_reply = response.content[0].text

                # Save as plan
                plan_file = self.plans / f"EMAIL_DRAFT_{file_path.stem}.md"
                plan_content = f"""---
type: email_draft
created: {datetime.now().isoformat()}
status: draft_completed
original_file: {file_path.name}
---

# Email Draft for {file_path.name}

## Draft Reply
{draft_reply}

## Next Steps
This email draft requires local approval before sending.
"""
                plan_file.write_text(plan_content)
                logger.info(f"Created email draft: {plan_file.name}")

                # Move to done
                done_file = self.done / file_path.name
                file_path.rename(done_file)

                return f"Email draft created: {plan_file.name}"

            except Exception as e:
                logger.error(f"Error processing email: {e}")
                return f"Error processing email: {str(e)}"

    def process_social_task(self, file_path: Path, content: str):
        """Process social media tasks - draft posts only"""
        logger.info(f"Processing social media task: {file_path.name}")

        # Never post directly from cloud - only draft
        try:
            system_prompt = """You are drafting social media posts on a cloud system.
Only create the content of the post.
Do NOT post directly to social media (that happens locally).
Focus on appropriate, professional content.
Do NOT include any actual posting functionality."""

            user_prompt = f"""Draft a social media post based on this request:

{content}

Draft post:"""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            draft_post = response.content[0].text

            # Save as plan
            plan_file = self.plans / f"SOCIAL_DRAFT_{file_path.stem}.md"
            plan_content = f"""---
type: social_media_draft
created: {datetime.now().isoformat()}
status: draft_completed
original_file: {file_path.name}
---

# Social Media Draft for {file_path.name}

## Draft Content
{draft_post}

## Next Steps
This social media draft requires local approval before posting.
"""
            plan_file.write_text(plan_content)
            logger.info(f"Created social media draft: {plan_file.name}")

            # Move to done
            done_file = self.done / file_path.name
            file_path.rename(done_file)

            return f"Social media draft created: {plan_file.name}"

        except Exception as e:
            logger.error(f"Error processing social task: {e}")
            return f"Error processing social task: {str(e)}"

    def process_odoo_task(self, file_path: Path, content: str):
        """Process Odoo-related tasks - draft actions only"""
        logger.info(f"Processing Odoo task: {file_path.name}")

        # Look for sensitive operations that require approval
        content_lower = content.lower()

        # Create approval request for any action that would modify data
        if any(keyword in content_lower for keyword in ['create', 'update', 'delete', 'invoice', 'customer', 'payment']):
            self.create_approval_request(file_path, "Odoo action requires local approval before execution")
            return "Odoo approval requested"
        else:
            # For read-only operations, process directly
            try:
                system_prompt = """You are analyzing Odoo operations on a cloud system.
This is a read-only environment for generating reports and planning.
Do NOT execute any actual changes to the Odoo system.
Only generate reports or planning documents."""

                user_prompt = f"""Analyze this Odoo request and generate a report/planning document:

{content}

Report:"""

                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.5,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                analysis = response.content[0].text

                # Save as plan
                plan_file = self.plans / f"ODOO_ANALYSIS_{file_path.stem}.md"
                plan_content = f"""---
type: odoo_analysis
created: {datetime.now().isoformat()}
status: analysis_completed
original_file: {file_path.name}
---

# Odoo Analysis for {file_path.name}

## Analysis
{analysis}

## Next Steps
This is a read-only analysis. Any actions require local approval.
"""
                plan_file.write_text(plan_content)
                logger.info(f"Created Odoo analysis: {plan_file.name}")

                # Move to done
                done_file = self.done / file_path.name
                file_path.rename(done_file)

                return f"Odoo analysis completed: {plan_file.name}"

            except Exception as e:
                logger.error(f"Error processing Odoo task: {e}")
                return f"Error processing Odoo task: {str(e)}"

    def process_file(self, file_path: Path):
        """Process a file based on its content and type"""
        logger.info(f"Processing file: {file_path.name}")

        try:
            # Read the file content
            content = file_path.read_text()

            # Claim the task (move to In_Progress)
            claimed_file = self.claim_task(file_path)
            content = claimed_file.read_text()

            # Determine task type and process accordingly
            content_lower = content.lower()

            if 'email' in content_lower or 'gmail' in content_lower:
                result = self.process_email_task(claimed_file, content)
            elif any(platform in content_lower for platform in ['facebook', 'instagram', 'x', 'twitter', 'social']):
                result = self.process_social_task(claimed_file, content)
            elif 'odoo' in content_lower or 'invoice' in content_lower or 'customer' in content_lower:
                result = self.process_odoo_task(claimed_file, content)
            else:
                # Default processing - create approval request for unknown types
                self.create_approval_request(claimed_file, f"Unknown task type: {content[:200]}...")
                result = "Approval requested for unknown task type"

            logger.info(f"Successfully processed {claimed_file.name}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run(self):
        """Main loop to check for and process files"""
        logger.info("Cloud Orchestrator Lite started")

        while True:
            try:
                # Check for files that need action
                needs_action_files = self.check_needs_action()

                if needs_action_files:
                    logger.info(f"Found {len(needs_action_files)} files to process")
                    for file_path in needs_action_files:
                        self.process_file(file_path)

                # Wait before checking again
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("Cloud Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Cloud Orchestrator error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait longer if there's an error

def main():
    vault_path = Path.cwd()
    orchestrator = CloudOrchestratorLite(str(vault_path))

    logger.info("Starting Cloud Orchestrator Lite...")
    orchestrator.run()

if __name__ == "__main__":
    main()