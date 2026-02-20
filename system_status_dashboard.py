"""
AI Employee Vault System Status Dashboard
Provides comprehensive view of all system components and their health
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import logging
from typing import Dict, List, Optional

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "system_status.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemStatusDashboard:
    def __init__(self):
        self.base_path = Path(".")
        self.status_file = Path("system_status.json")

        # Services to monitor
        self.services = [
            "platinum_local_orchestrator.py",
            "approval_executor.py",
            "dashboard_merger.py",
            "cloud_orchestrator_lite.py",
            "email_watcher.py",
            "odoo_draft_mcp.py",
            "odoo_execute_mcp.py",
            "social_mcp_server.py",
            "gmail_draft_mcp.py",
            "platinum_watchdog.py",
            "ralph_loop.py",
            "weekly_audit_orchestrator.py"
        ]

        # Directories to check
        self.key_directories = [
            "Inbox",
            "Needs_Action",
            "Approved",
            "Done",
            "Pending_Approval",
            "Pending_Approval/cloud",
            "Approved",
            "Logs",
            "Audits",
            "Accounting",
            "Social_Summaries",
            "Briefings"
        ]

        # Log files to monitor
        self.log_files = [
            "Logs/platinum_local_orchestrator.log",
            "Logs/approval_executor.log",
            "Logs/dashboard_merger.log",
            "Logs/watchdog.log",
            "Logs/audit.log",
            "Logs/cloud_orchestrator.log",
            "Logs/alerts.md"
        ]

    def check_process_running(self, process_name: str) -> bool:
        """Check if a specific process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Check if the process name appears in the command line
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline']).lower()
                        if process_name.lower() in cmdline and 'python' in cmdline:
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return False
        except Exception as e:
            logger.error(f"Error checking process {process_name}: {e}")
            return False

    def get_directory_contents(self) -> Dict[str, int]:
        """Get count of files in key directories"""
        contents = {}
        for dir_name in self.key_directories:
            dir_path = Path(dir_name)
            if dir_path.exists():
                try:
                    contents[dir_name] = len([f for f in dir_path.iterdir() if f.is_file()])
                except:
                    contents[dir_name] = 0
            else:
                contents[dir_name] = -1  # Directory doesn't exist
        return contents

    def get_system_resources(self) -> Dict:
        """Get system resource usage"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(str(self.base_path)).percent,
            "timestamp": datetime.now().isoformat()
        }

    def get_recent_log_entries(self, log_file: str, lines: int = 5) -> List[str]:
        """Get recent entries from a log file"""
        try:
            if Path(log_file).exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines_list = f.readlines()
                    return lines_list[-lines:] if len(lines_list) >= lines else lines_list
            return ["Log file not found"]
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
            return [f"Error reading log: {e}"]

    def get_service_status(self) -> Dict[str, bool]:
        """Get status of all services"""
        status = {}
        for service in self.services:
            status[service] = self.check_process_running(service)
        return status

    def get_dashboard_summary(self) -> Dict:
        """Generate complete dashboard summary"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_resources": self.get_system_resources(),
            "directory_contents": self.get_directory_contents(),
            "service_status": self.get_service_status(),
            "log_health": self.check_log_health(),
            "overall_health": self.calculate_overall_health()
        }

    def check_log_health(self) -> Dict[str, str]:
        """Check health of log files"""
        health = {}
        for log_file in self.log_files:
            if Path(log_file).exists():
                try:
                    size = Path(log_file).stat().st_size
                    recent_entries = self.get_recent_log_entries(log_file, 1)

                    # Check for error patterns
                    error_patterns = ["error", "exception", "traceback", "failed"]
                    has_errors = any(pattern in str(recent_entries).lower() for pattern in error_patterns)

                    health[log_file] = "WARNING" if has_errors else "OK"
                except:
                    health[log_file] = "ERROR"
            else:
                health[log_file] = "MISSING"
        return health

    def calculate_overall_health(self) -> str:
        """Calculate overall system health"""
        service_status = self.get_service_status()
        active_services = sum(1 for status in service_status.values() if status)
        total_services = len(service_status)

        # Check directory health
        dir_contents = self.get_directory_contents()
        critical_dirs_exist = all(
            dir_contents.get(dir_name, -1) >= 0
            for dir_name in ["Inbox", "Logs", "Approved", "Done"]
        )

        # Check log health
        log_health = self.check_log_health()
        critical_logs_ok = all(
            status == "OK"
            for log_file, status in log_health.items()
            if "alerts" not in log_file
        )

        # Calculate health score
        service_health = (active_services / total_services) * 100 if total_services > 0 else 0
        critical_checks = [critical_dirs_exist, critical_logs_ok]
        critical_health = sum(critical_checks) / len(critical_checks) * 100 if critical_checks else 0

        overall_score = (service_health + critical_health) / 2

        if overall_score >= 90 and service_health >= 80:
            return "EXCELLENT"
        elif overall_score >= 70:
            return "GOOD"
        elif overall_score >= 50:
            return "FAIR"
        else:
            return "POOR"

    def generate_report(self) -> str:
        """Generate a formatted report"""
        summary = self.get_dashboard_summary()

        report = []
        report.append("# AI Employee Vault System Status Report")
        report.append(f"**Generated at:** {summary['timestamp']}")
        report.append(f"**Overall Health:** {summary['overall_health']}")
        report.append("")

        # System Resources
        resources = summary["system_resources"]
        report.append("## System Resources")
        report.append(f"- CPU Usage: {resources['cpu_percent']}%")
        report.append(f"- Memory Usage: {resources['memory_percent']}%")
        report.append(f"- Disk Usage: {resources['disk_percent']}%")
        report.append("")

        # Directory Status
        report.append("## Directory Status")
        for dir_name, count in summary["directory_contents"].items():
            if count >= 0:
                report.append(f"- {dir_name}: {count} files")
            else:
                report.append(f"- {dir_name}: *MISSING*")
        report.append("")

        # Service Status
        report.append("## Service Status")
        active_services = 0
        total_services = len(summary["service_status"])
        for service, running in summary["service_status"].items():
            status = "✅ RUNNING" if running else "❌ STOPPED"
            if running:
                active_services += 1
            report.append(f"- {service}: {status}")
        report.append(f"**Active Services:** {active_services}/{total_services}")
        report.append("")

        # Log Health
        report.append("## Log Health")
        for log_file, health in summary["log_health"].items():
            emoji = "✅" if health == "OK" else "⚠️" if health == "WARNING" else "❌"
            report.append(f"- {log_file}: {emoji} {health}")
        report.append("")

        return "\n".join(report)

    def save_status(self):
        """Save current status to file"""
        summary = self.get_dashboard_summary()
        with open(self.status_file, 'w') as f:
            json.dump(summary, f, indent=2)

    def run_dashboard(self, continuous: bool = False, interval: int = 30):
        """Run the dashboard"""
        logger.info("Starting System Status Dashboard...")

        while True:
            try:
                report = self.generate_report()
                print("\n" + "="*60)
                print("AI EMPLOYEE VAULT SYSTEM STATUS")
                print("="*60)
                print(report)
                print("="*60)

                # Save to file
                self.save_status()

                # Write to dashboard file as well
                with open("Dashboard.md", "r+", encoding="utf-8") as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write(report + "\n\n" + content)

                if not continuous:
                    break

                print(f"Refreshing in {interval} seconds... (Ctrl+C to stop)")
                time.sleep(interval)

            except KeyboardInterrupt:
                logger.info("Dashboard stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in dashboard: {e}")
                if not continuous:
                    break
                time.sleep(interval)

def main():
    import argparse

    parser = argparse.ArgumentParser(description='AI Employee Vault System Status Dashboard')
    parser.add_argument('--continuous', '-c', action='store_true',
                       help='Run continuously with updates')
    parser.add_argument('--interval', '-i', type=int, default=30,
                       help='Update interval in seconds (default: 30)')

    args = parser.parse_args()

    dashboard = SystemStatusDashboard()
    dashboard.run_dashboard(continuous=args.continuous, interval=args.interval)

if __name__ == "__main__":
    main()