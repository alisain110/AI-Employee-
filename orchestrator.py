import os
import time
import logging
import requests
from pathlib import Path
import subprocess
import json
from datetime import datetime
from core.agent import AIAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('Logs/orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIOrchestrator:
    """Orchestrates the AI Employee operations"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.done = self.vault_path / 'Done'
        self.inbox = self.vault_path / 'Inbox'
        self.plans = self.vault_path / 'Plans'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.rejected = self.vault_path / 'Rejected'

        # Create directories if they don't exist
        for dir_path in [self.needs_action, self.done, self.inbox, self.plans,
                         self.pending_approval, self.approved, self.rejected,
                         self.vault_path / 'Logs', self.vault_path / 'Briefings']:
            dir_path.mkdir(exist_ok=True)

        # Load MCP endpoints configuration
        self.mcp_endpoints = self.load_mcp_endpoints()

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

            response = requests.post(full_url, json=data, headers=headers)
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

    def check_needs_action(self):
        """Check for files that need action"""
        needs_action_files = list(self.needs_action.glob('*.md'))
        return needs_action_files

    def process_file(self, file_path: Path):
        """Process a file using Claude Code"""
        logger.info(f"Processing file: {file_path.name}")

        try:
            # Read the file content
            content = file_path.read_text()

            # Update dashboard before processing
            self.update_dashboard(f"Processing {file_path.name}")

            # Example: Process the file with Claude Code logic
            # In a real implementation, this would call Claude Code
            result = self.simulate_claude_processing(content, file_path)

            # Move file to Done folder
            done_file = self.done / file_path.name
            file_path.rename(done_file)

            logger.info(f"Successfully processed and moved {file_path.name} to Done")
            self.update_dashboard(f"Completed processing {file_path.name}")

            return result
        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return None

    def handle_social_media_task(self, content: str, file_path: Path):
        """Handle social media related tasks using MCP endpoints when available, otherwise agent skills"""
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
        agent = AIAgent()

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

    def simulate_claude_processing(self, content: str, file_path: Path):
        """Simulate what Claude Code would do with the file"""
        # This is a simplified simulation
        # In a real implementation, this would call Claude Code API

        # Check for social media tasks first
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

    def update_dashboard(self, message: str):
        """Update the dashboard with current status"""
        dashboard_path = self.vault_path / 'Dashboard.md'
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
                for i in range(1, 4):  # Add up to 3 previous activities
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
        dashboard_path.write_text(updated_content)

    def update_stats_in_dashboard(self):
        """Update the quick stats in the dashboard"""
        dashboard_path = self.vault_path / 'Dashboard.md'
        current_content = dashboard_path.read_text()

        # Count files in each directory
        inbox_count = len(list(self.inbox.glob('*')))
        needs_action_count = len(list(self.needs_action.glob('*')))
        done_count = len(list(self.done.glob('*')))
        pending_approval_count = len(list(self.pending_approval.glob('*')))

        lines = current_content.split('\n')
        new_lines = []

        for line in lines:
            if line.startswith('- Files in Inbox:'):
                new_lines.append(f'- Files in Inbox: {inbox_count}')
            elif line.startswith('- Files in Needs_Action:'):
                new_lines.append(f'- Files in Needs_Action: {needs_action_count}')
            elif line.startswith('- Files in Done:'):
                new_lines.append(f'- Files in Done: {done_count}')
            elif line.startswith('- Pending Approvals:'):
                new_lines.append(f'- Pending Approvals: {pending_approval_count}')
            else:
                new_lines.append(line)

        updated_content = '\n'.join(new_lines)
        dashboard_path.write_text(updated_content)

    def run(self):
        """Main loop to check for and process files"""
        logger.info("AI Employee Orchestrator started")

        while True:
            try:
                # Check for files that need action
                needs_action_files = self.check_needs_action()

                if needs_action_files:
                    logger.info(f"Found {len(needs_action_files)} files to process")
                    for file_path in needs_action_files:
                        self.process_file(file_path)

                # Update dashboard stats
                self.update_stats_in_dashboard()

                # Wait before checking again
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("Orchestrator stopped by user")
                break
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                time.sleep(60)  # Wait longer if there's an error

def main():
    vault_path = Path.cwd()
    orchestrator = AIOrchestrator(str(vault_path))

    logger.info("Starting AI Employee Orchestrator...")
    orchestrator.run()

if __name__ == "__main__":
    main()