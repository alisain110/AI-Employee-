"""
Main System Entry Point for AI Employee Vault
Orchestrates all components and provides unified interface
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
import threading
import logging
import argparse

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "main_system.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AISystemManager:
    def __init__(self):
        self.running = False
        self.services = {}
        self.dashboard_file = Path("Dashboard.md")
        self.system_status_file = Path("system_status.json")

    def initialize_dashboard(self):
        """Initialize or update the dashboard with system status"""
        if not self.dashboard_file.exists():
            initial_content = f"""# AI Employee Vault Dashboard

## Executive Summary
Welcome to your AI Employee dashboard. This system monitors your personal and business affairs 24/7.

## System Status
- **Date:** {datetime.now().strftime('%Y-%m-%d')}
- **AI Employee Status:** Active
- **Last Processed:** {datetime.now().strftime('%H:%M:%S')}
- **System Uptime:** 0 hours

## Current Services
- Platinum Orchestrator: Not Running
- Approval Executor: Not Running
- Dashboard Merger: Not Running
- MCP Servers: Not Running
- Watchdog: Not Running
- Ralph Mode: Not Running

## Recent Activity
- {datetime.now().strftime('%H:%M:%S')} - System initialized

## System Health
- Overall Status: Initializing
- Active Services: 0/8
- Memory Usage: Unknown%
- CPU Usage: Unknown%

## Quick Stats
- Files in Inbox: 0
- Files in Needs_Action: 0
- Files in Approved: 0
- Files in Done: 0
- Pending Approvals: 0

## Next Actions
- Monitor for new files in Inbox
- Process any high-priority tasks first
- Continue following Company_Handbook.md guidelines
"""
            self.dashboard_file.write_text(initial_content)
        else:
            # Update existing dashboard with current time
            content = self.dashboard_file.read_text()
            lines = content.split('\n')
            updated_lines = []
            for line in lines:
                if line.startswith('- **Date:**'):
                    updated_lines.append(f"- **Date:** {datetime.now().strftime('%Y-%m-%d')}")
                elif line.startswith('- **Last Processed:**'):
                    updated_lines.append(f"- **Last Processed:** {datetime.now().strftime('%H:%M:%S')}")
                elif line.startswith('- **System Uptime:**'):
                    updated_lines.append(f"- **System Uptime:** Calculating...")
                else:
                    updated_lines.append(line)

            self.dashboard_file.write_text('\n'.join(updated_lines))

    def start_service(self, service_name: str, module_name: str):
        """Start a service in a separate thread"""
        try:
            # Import the module and get its main function
            module = __import__(module_name, fromlist=[module_name])

            # Look for common start function names
            start_func = None
            for func_name in ['main', 'run', 'start', f'start_{module_name}']:
                if hasattr(module, func_name):
                    start_func = getattr(module, func_name)
                    break

            if start_func is None:
                logger.error(f"No start function found in {module_name}")
                return False

            # Create thread and start the service
            def run_service():
                try:
                    # For some services, we may need to pass arguments
                    try:
                        start_func()
                    except TypeError:
                        # If it doesn't accept arguments, run without them
                        try:
                            # Try with default args if it expects them
                            start_func()
                        except:
                            logger.error(f"Could not start {module_name}")

                except Exception as e:
                    logger.error(f"Service {module_name} crashed: {e}")
                    import traceback
                    traceback.print_exc()

            thread = threading.Thread(target=run_service, daemon=True)
            thread.start()
            self.services[service_name] = thread

            logger.info(f"Started service: {service_name}")
            return True

        except ImportError as e:
            logger.error(f"Could not import {module_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error starting service {service_name}: {e}")
            return False

    def start_all_services(self):
        """Start all system services"""
        logger.info("Starting all AI Employee Vault services...")

        # Define services to start
        services_to_start = [
            ("Dashboard Merger", "dashboard_merger"),
            ("Approval Executor", "approval_executor"),
            ("Platinum Orchestrator", "platinum_local_orchestrator"),
            ("Cloud Watchers", "cloud_watchers"),
            ("Watchdog", "platinum_watchdog_win"),  # Use Windows version
        ]

        started_count = 0
        for service_name, module_name in services_to_start:
            logger.info(f"Starting {service_name}...")
            if self.start_service(service_name, module_name):
                started_count += 1
                time.sleep(2)  # Give each service a moment to start
            else:
                logger.warning(f"Failed to start {service_name}")

        logger.info(f"Started {started_count}/{len(services_to_start)} services")

    def update_dashboard_status(self, status_message: str = ""):
        """Update dashboard with current system status"""
        if self.dashboard_file.exists():
            content = self.dashboard_file.read_text()

            # Update status sections
            lines = content.split('\n')
            updated_lines = []
            in_services_section = False

            for line in lines:
                if line.startswith('## Current Services'):
                    in_services_section = True
                    updated_lines.append(line)
                    continue
                elif line.startswith('## ') and in_services_section:
                    in_services_section = False
                    updated_lines.append(f"- {status_message}" if status_message else "")
                    updated_lines.append(line)
                    continue
                elif in_services_section:
                    # Skip existing service lines in this section
                    continue
                else:
                    updated_lines.append(line)

            # If we're still in the services section, add the status
            if in_services_section:
                updated_lines.append(f"- {status_message}" if status_message else "")

            self.dashboard_file.write_text('\n'.join(updated_lines))

    def monitor_system(self):
        """Monitor system health and update dashboard"""
        while self.running:
            try:
                # Update dashboard with current status
                active_services = sum(1 for t in self.services.values() if t.is_alive())
                total_services = len(self.services)

                status_msg = f"Active Services: {active_services}/{total_services}"

                # Add health indicator
                if active_services == total_services and total_services > 0:
                    status_msg += " - Excellent"
                elif active_services >= total_services * 0.7:  # 70%+
                    status_msg += " - Good"
                elif active_services >= total_services * 0.4:  # 40%+
                    status_msg += " - Fair"
                else:
                    status_msg += " - Poor"

                self.update_dashboard_status(status_msg)

                # Update system information
                self.update_system_info()

                # Wait before next update
                time.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(60)

    def update_system_info(self):
        """Update system information in dashboard"""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            if self.dashboard_file.exists():
                content = self.dashboard_file.read_text()

                lines = content.split('\n')
                updated_lines = []

                for line in lines:
                    if line.startswith('- Memory Usage:'):
                        updated_lines.append(f"- Memory Usage: {memory_percent}%")
                    elif line.startswith('- CPU Usage:'):
                        updated_lines.append(f"- CPU Usage: {cpu_percent}%")
                    elif line.startswith('- Active Services:'):
                        active_services = sum(1 for t in self.services.values() if t.is_alive())
                        total_services = len(self.services)
                        updated_lines.append(f"- Active Services: {active_services}/{total_services}")
                    elif line.startswith('- Files in Inbox:'):
                        inbox_count = len(list(Path("Inbox").glob("*"))) if Path("Inbox").exists() else 0
                        updated_lines.append(f"- Files in Inbox: {inbox_count}")
                    elif line.startswith('- Files in Needs_Action:'):
                        needs_action_count = len(list(Path("Needs_Action").glob("*"))) if Path("Needs_Action").exists() else 0
                        updated_lines.append(f"- Files in Needs_Action: {needs_action_count}")
                    elif line.startswith('- Files in Approved:'):
                        approved_count = len(list(Path("Approved").glob("*"))) if Path("Approved").exists() else 0
                        updated_lines.append(f"- Files in Approved: {approved_count}")
                    elif line.startswith('- Files in Done:'):
                        done_count = len(list(Path("Done").glob("*"))) if Path("Done").exists() else 0
                        updated_lines.append(f"- Files in Done: {done_count}")
                    else:
                        updated_lines.append(line)

                self.dashboard_file.write_text('\n'.join(updated_lines))

        except ImportError:
            # psutil not installed, skip system info update
            pass
        except Exception as e:
            logger.error(f"Error updating system info: {e}")

    def run(self, start_services: bool = True):
        """Run the main system"""
        logger.info("Starting AI Employee Vault System Manager...")

        # Initialize dashboard
        self.initialize_dashboard()

        # Start services if requested
        if start_services:
            self.start_all_services()

        # Set running flag
        self.running = True

        # Update dashboard to show system is active
        self.update_dashboard_status("System Active - All Services Starting...")

        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        monitor_thread.start()

        logger.info("AI Employee Vault System Manager is running")
        logger.info("Press Ctrl+C to stop the system")

        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal...")
            self.shutdown()

    def shutdown(self):
        """Shutdown the system gracefully"""
        logger.info("Shutting down AI Employee Vault System...")

        self.running = False

        # Wait for threads to finish (with timeout)
        for name, thread in self.services.items():
            if thread.is_alive():
                logger.info(f"Waiting for {name} to stop...")
                # Note: We can't forcibly stop threads, but we can wait for them
                # Services should handle KeyboardInterrupt properly
                thread.join(timeout=5)  # Wait up to 5 seconds

                if thread.is_alive():
                    logger.warning(f"{name} did not stop gracefully")

        logger.info("AI Employee Vault System has been shut down")

def main():
    parser = argparse.ArgumentParser(description='AI Employee Vault Main System')
    parser.add_argument('--no-services', action='store_true',
                       help='Start system without background services')
    parser.add_argument('--test', action='store_true',
                       help='Run system tests instead of starting services')

    args = parser.parse_args()

    if args.test:
        logger.info("Running comprehensive system tests...")
        try:
            import run_comprehensive_tests
            test_runner = run_comprehensive_tests.ComprehensiveTestRunner()
            results = test_runner.run_all_tests()

            print("\nTest Results Summary:")
            print(f"Total Tests: {results['total_tests']}")
            print(f"Passed: {results['passed_tests']}")
            print(f"Failed: {results['failed_tests']}")
            if results['total_tests'] > 0:
                print(f"Success Rate: {(results['passed_tests']/results['total_tests']*100):.1f}%")
        except ImportError:
            logger.error("Could not import test runner")
        return

    # Initialize system manager
    manager = AISystemManager()

    # Start the system
    manager.run(start_services=not args.no_services)

if __name__ == "__main__":
    main()