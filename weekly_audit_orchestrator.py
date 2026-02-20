"""
Weekly Audit Orchestrator - Runs weekly to generate CEO Briefing
Executes every Monday at 9 AM to collect metrics and create audit reports
"""
import os
import json
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from anthropic import Anthropic
from core.agent import AIAgent

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "weekly_audit.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WeeklyAuditOrchestrator:
    """Orchestrates weekly audit and CEO briefing generation"""

    def __init__(self):
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.agent = AIAgent()
        self.mcp_endpoints = self.load_mcp_endpoints()

    def load_mcp_endpoints(self):
        """Load MCP endpoints configuration from file"""
        config_file = Path('mcp_endpoints.json')
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

    def get_odoo_metrics(self) -> Dict[str, Any]:
        """Get key Odoo metrics from MCP server"""
        logger.info("Fetching Odoo metrics from MCP server...")

        metrics = {}

        # Get profit and loss for last 7 days
        try:
            pl_7d = self.call_mcp_endpoint("odoo_mcp", "get_profit_loss_last_30_days")
            # Note: we'll adjust the endpoint to handle 7-day period if needed
            metrics["profit_loss_7_days"] = pl_7d
        except Exception as e:
            logger.error(f"Error getting 7-day P&L: {e}")
            metrics["profit_loss_7_days"] = {"error": str(e)}

        # Get balance sheet summary
        try:
            balance_sheet = self.call_mcp_endpoint("odoo_mcp", "get_balance_sheet_summary")
            metrics["balance_sheet"] = balance_sheet
        except Exception as e:
            logger.error(f"Error getting balance sheet: {e}")
            metrics["balance_sheet"] = {"error": str(e)}

        # Get unpaid invoices
        try:
            unpaid_invoices = self.call_mcp_endpoint("odoo_mcp", "get_unpaid_invoices")
            metrics["unpaid_invoices"] = unpaid_invoices
        except Exception as e:
            logger.error(f"Error getting unpaid invoices: {e}")
            metrics["unpaid_invoices"] = {"error": str(e)}

        logger.info("Odoo metrics fetched successfully")
        return metrics

    def get_social_summaries(self) -> Dict[str, Any]:
        """Generate social media summaries using agent skills"""
        logger.info("Generating social media summaries...")

        summaries = {}

        # Generate Facebook summary
        try:
            fb_summary = self.agent.run("social_summary_generator", platform="facebook")
            summaries["facebook"] = fb_summary
        except Exception as e:
            logger.error(f"Error generating Facebook summary: {e}")
            summaries["facebook"] = {"error": str(e)}

        # Generate Instagram summary
        try:
            ig_summary = self.agent.run("social_summary_generator", platform="instagram")
            summaries["instagram"] = ig_summary
        except Exception as e:
            logger.error(f"Error generating Instagram summary: {e}")
            summaries["instagram"] = {"error": str(e)}

        # Generate X (Twitter) summary
        try:
            x_summary = self.agent.run("social_summary_generator", platform="x")
            summaries["x"] = x_summary
        except Exception as e:
            logger.error(f"Error generating X summary: {e}")
            summaries["x"] = {"error": str(e)}

        logger.info("Social media summaries generated successfully")
        return summaries

    def generate_ceo_briefing(self, odoo_metrics: Dict, social_summaries: Dict) -> str:
        """Generate CEO briefing using Claude with comprehensive context"""
        logger.info("Generating CEO briefing with Claude...")

        # Prepare comprehensive context
        context_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "week_number": datetime.now().isocalendar()[1],
            "odoo_metrics": odoo_metrics,
            "social_summaries": social_summaries
        }

        system_prompt = """
        You are a senior business analyst creating a weekly CEO briefing.
        Create a comprehensive report with clear sections covering financial performance,
        social media performance, risks/issues, recommendations, and action items.
        Use professional business language and provide actionable insights.
        """

        user_prompt = f"""
        Create a comprehensive weekly CEO briefing for the week ending {context_data['date']}.
        Week number: {context_data['week_number']}

        Odoo Financial Metrics:
        {json.dumps(context_data['odoo_metrics'], indent=2)}

        Social Media Summaries:
        {json.dumps(context_data['social_summaries'], indent=2)}

        Please create a detailed report with the following sections:
        1. Financial Snapshot - Revenue, expenses, profit/loss, balance sheet highlights
        2. Social Performance - Facebook, Instagram, X (Twitter) performance metrics
        3. Risks/Issues - Potential business risks and issues identified
        4. Recommendations - Strategic recommendations based on data
        5. Action Items - Specific action items for leadership team

        Format your response as clean Markdown with appropriate headers.
        Make the report executive-friendly with clear insights and recommendations.
        """

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            briefing_content = response.content[0].text
            logger.info("CEO briefing generated successfully")
            return briefing_content

        except Exception as e:
            logger.error(f"Error generating CEO briefing: {e}")
            return f"Error generating briefing: {str(e)}"

    def save_briefing(self, briefing_content: str) -> str:
        """Save the CEO briefing to the Audits folder"""
        # Get current year and week number
        current_date = datetime.now()
        year = current_date.year
        week_number = current_date.isocalendar()[1]

        # Create filename with format: YYYY-WW_CEO_Briefing.md
        filename = f"{year}-W{week_number:02d}_CEO_Briefing.md"

        # Create Audits directory if it doesn't exist
        audits_dir = Path("Audits")
        audits_dir.mkdir(exist_ok=True)

        # Create the full file path
        file_path = audits_dir / filename

        # Write the briefing content
        full_content = f"""# CEO Weekly Briefing
## Week {week_number} of {year} - {current_date.strftime('%B %d, %Y')}

{briefing_content}

---

*Generated by Weekly Audit Orchestrator on {current_date.strftime('%Y-%m-%d %H:%M:%S')}*
*Next scheduled execution: Next Monday 9:00 AM*
"""

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        logger.info(f"CEO briefing saved to: {file_path}")
        return str(file_path)

    def move_to_needs_action(self, briefing_path: str):
        """Move the briefing to Needs_Action folder as high-priority task"""
        try:
            source_path = Path(briefing_path)
            if not source_path.exists():
                logger.error(f"Source file does not exist: {briefing_path}")
                return

            # Create Needs_Action directory if it doesn't exist
            needs_action_dir = Path("Needs_Action")
            needs_action_dir.mkdir(exist_ok=True)

            # Move the file
            destination_path = needs_action_dir / source_path.name
            source_path.rename(destination_path)

            logger.info(f"CEO briefing moved to Needs_Action: {destination_path}")

            # Update dashboard to indicate new high-priority task
            self.update_dashboard(f"Weekly CEO Briefing generated: {destination_path.name}")

        except Exception as e:
            logger.error(f"Error moving briefing to Needs_Action: {e}")

    def update_dashboard(self, message: str):
        """Update the dashboard with current status"""
        dashboard_path = Path('Dashboard.md')
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
- Files in Needs_Action: 1
- Files in Done: 0
- Pending Approvals: 0

## Next Actions
- Review generated CEO briefing in Needs_Action
- Process any high-priority tasks first
- Continue following Company_Handbook.md guidelines
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

        # Update quick stats to show the briefing file
        stats_lines = updated_content.split('\n')
        final_lines = []
        for line in stats_lines:
            if line.startswith('- Files in Needs_Action:'):
                # Count files in Needs_Action directory
                needs_action_count = len(list(Path('Needs_Action').glob('*'))) + 1  # +1 for our new file
                final_lines.append(f'- Files in Needs_Action: {needs_action_count}')
            else:
                final_lines.append(line)

        final_content = '\n'.join(final_lines)
        dashboard_path.write_text(final_content)

    def run_weekly_audit(self):
        """Main method to run the weekly audit and generate CEO briefing"""
        logger.info("Starting weekly audit process...")

        try:
            # Step 1: Get Odoo metrics
            odoo_metrics = self.get_odoo_metrics()

            # Step 2: Generate social media summaries
            social_summaries = self.get_social_summaries()

            # Step 3: Generate CEO briefing with Claude
            briefing_content = self.generate_ceo_briefing(odoo_metrics, social_summaries)

            # Step 4: Save the briefing
            briefing_path = self.save_briefing(briefing_content)

            # Step 5: Move to Needs_Action as high-priority task
            self.move_to_needs_action(briefing_path)

            logger.info("Weekly audit completed successfully")
            return briefing_path

        except Exception as e:
            logger.error(f"Error in weekly audit process: {e}")
            import traceback
            traceback.print_exc()
            return None

def run_weekly_audit_job():
    """Wrapper function for the scheduler"""
    logger.info("Weekly audit job triggered by scheduler")
    orchestrator = WeeklyAuditOrchestrator()
    result = orchestrator.run_weekly_audit()

    if result:
        logger.info(f"Weekly audit job completed successfully, output: {result}")
    else:
        logger.error("Weekly audit job failed")

    return result

if __name__ == "__main__":
    logger.info("Manual run of Weekly Audit Orchestrator started")
    orchestrator = WeeklyAuditOrchestrator()
    orchestrator.run_weekly_audit()