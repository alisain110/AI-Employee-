"""
Dashboard Merger for Platinum Tier AI Employee Vault
Merges updates from /Updates/ directory into Dashboard.md safely without overwriting
"""
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import re

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "dashboard_merger.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DashboardMerger:
    """Safely merges updates from cloud into Dashboard.md"""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.dashboard_path = self.vault_path / "Dashboard.md"
        self.updates_dir = self.vault_path / "Updates"
        self.signals_dir = self.vault_path / "Signals"

        # Create directories if they don't exist
        self.updates_dir.mkdir(exist_ok=True)
        self.signals_dir.mkdir(exist_ok=True)

    def merge_updates_to_dashboard(self):
        """Merge all updates from Updates/ into Dashboard.md"""
        logger.info("Starting dashboard merge process")

        # Get all update files
        update_files = list(self.updates_dir.glob("*.md"))

        if not update_files:
            logger.info("No update files found to merge")
            return

        # Read current dashboard
        if self.dashboard_path.exists():
            current_dashboard = self.dashboard_path.read_text()
        else:
            # Create a basic dashboard if it doesn't exist
            current_dashboard = self._create_basic_dashboard()
            self.dashboard_path.write_text(current_dashboard)

        # Process each update file
        for update_file in update_files:
            logger.info(f"Processing update file: {update_file.name}")

            try:
                update_content = update_file.read_text()

                # Merge the update content
                updated_dashboard = self._merge_single_update(current_dashboard, update_content, update_file.name)

                # Write back to dashboard
                self.dashboard_path.write_text(updated_dashboard)

                # Archive the processed update (move to prevent reprocessing)
                archive_dir = self.vault_path / "Updates" / "archive"
                archive_dir.mkdir(exist_ok=True)
                archive_file = archive_dir / f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{update_file.name}"
                update_file.rename(archive_file)

                logger.info(f"Successfully merged update: {update_file.name}")

                # Update the current dashboard for the next iteration
                current_dashboard = updated_dashboard

            except Exception as e:
                logger.error(f"Error processing update file {update_file.name}: {e}")
                # Move to error directory instead of archive
                error_dir = self.vault_path / "Updates" / "error"
                error_dir.mkdir(exist_ok=True)
                error_file = error_dir / f"error_{update_file.name}"
                update_file.rename(error_file)

    def _create_basic_dashboard(self):
        """Create a basic dashboard if none exists"""
        basic_dashboard = f"""# AI Employee Dashboard

## Executive Summary
Welcome to your AI Employee dashboard. This system monitors your personal and business affairs 24/7.

## Current Status
- **Date:** {datetime.now().strftime('%Y-%m-%d')}
- **AI Employee Status:** Active
- **Last Processed:** {datetime.now().strftime('%H:%M')}

## Recent Activity
- {datetime.now().strftime('%H:%M')} - Dashboard initialized

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
- [x] Accounting system connected (Odoo integration)
- [x] Social media summaries (FB/IG/X)
- [x] Weekly CEO briefings + audit logs
- [x] Ralph Wiggum loop traces
- [x] API keys configured (.env)
- [x] External services tested
- [x] Comprehensive audit logging
- [x] Error recovery patterns
- [x] MCP endpoint integration
- [x] Dashboard monitoring
- [x] File-based workflows
- [x] Automated scheduling

## Next Actions
- Monitor for new files in Inbox
- Process any high-priority tasks first
- Continue following Company_Handbook.md guidelines
- Run setup_gold.py to initialize Gold Tier features
"""
        return basic_dashboard

    def _merge_single_update(self, current_dashboard: str, update_content: str, update_filename: str):
        """Merge a single update into the dashboard"""
        lines = current_dashboard.split('\n')
        new_lines = []

        # Add the update content to Recent Activity section
        update_timestamp = datetime.now().strftime('%H:%M')
        update_entry = f"- {update_timestamp} - Update from {update_filename}: {update_content[:100]}..."

        for line in lines:
            if line.startswith('## Recent Activity'):
                new_lines.append(line)
                new_lines.append(update_entry)

                # Add back previous activity lines (limit to recent ones to avoid infinite growth)
                # Find and add next few lines that are part of the activity section
                continue

            elif line.startswith('## ') and line != '## Recent Activity':
                # We're at the start of the next section, add recent activity if not added yet
                if update_entry not in new_lines:
                    # Add the update entry before the next section
                    new_lines.insert(len(new_lines)-1 if new_lines else 0, update_entry) if new_lines else new_lines.append(update_entry)
                new_lines.append(line)
            else:
                new_lines.append(line)

        # If we couldn't find the Recent Activity section, add it at the beginning
        if not any('Recent Activity' in line for line in new_lines):
            # Insert after the Current Status section
            status_section_idx = -1
            for i, line in enumerate(new_lines):
                if line.startswith('## Current Status'):
                    status_section_idx = i
                    break

            if status_section_idx != -1:
                new_lines.insert(status_section_idx + 1, '## Recent Activity')
                new_lines.insert(status_section_idx + 2, update_entry)
            else:
                # If we can't find Current Status, add it at the beginning
                new_lines = ['## Recent Activity', update_entry, ''] + new_lines

        return '\n'.join(new_lines)

    def merge_signals_to_dashboard(self):
        """Merge signals from Signals/ directory if needed"""
        logger.info("Processing signals...")

        signal_files = list(self.signals_dir.glob("*.md"))

        for signal_file in signal_files:
            logger.info(f"Processing signal: {signal_file.name}")

            try:
                signal_content = signal_file.read_text()

                # For signals, we might want to add them to a different section
                # For now, treat them similar to updates
                if self.dashboard_path.exists():
                    current_dashboard = self.dashboard_path.read_text()
                else:
                    current_dashboard = self._create_basic_dashboard()

                # Add signal to dashboard
                updated_dashboard = self._merge_signal(current_dashboard, signal_content, signal_file.name)
                self.dashboard_path.write_text(updated_dashboard)

                # Archive the signal
                archive_dir = self.vault_path / "Signals" / "archive"
                archive_dir.mkdir(exist_ok=True)
                archive_file = archive_dir / f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{signal_file.name}"
                signal_file.rename(archive_file)

                logger.info(f"Successfully processed signal: {signal_file.name}")

            except Exception as e:
                logger.error(f"Error processing signal {signal_file.name}: {e}")
                # Move to error directory
                error_dir = self.vault_path / "Signals" / "error"
                error_dir.mkdir(exist_ok=True)
                error_file = error_dir / f"error_{signal_file.name}"
                signal_file.rename(error_file)

    def _merge_signal(self, current_dashboard: str, signal_content: str, signal_filename: str):
        """Merge a signal into the dashboard"""
        # For now, just add to recent activity like updates
        # In a more sophisticated system, signals might go to their own section
        return self._merge_single_update(current_dashboard, signal_content, signal_filename)

    def run(self):
        """Main method to run the merger"""
        logger.info("Dashboard Merger started")

        while True:
            try:
                # Merge updates
                self.merge_updates_to_dashboard()

                # Merge signals
                self.merge_signals_to_dashboard()

                # Wait before checking again
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("Dashboard Merger stopped by user")
                break
            except Exception as e:
                logger.error(f"Dashboard Merger error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait longer if there's an error

def main():
    merger = DashboardMerger()
    logger.info("Starting Dashboard Merger...")
    merger.run()

if __name__ == "__main__":
    main()