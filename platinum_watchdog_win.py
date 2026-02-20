"""
Platinum Tier Watchdog (Windows Compatible Version)
Monitors orchestrators, watchers, and MCP servers
Restarts services if they die, sends health pings, alerts on excessive restarts
"""

import os
import time
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
import sys
import argparse
import threading

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "watchdog.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PlatinumWatchdog:
    def __init__(self, is_cloud=True):
        self.is_cloud = is_cloud
        self.restart_counts = {}  # Track restarts per service
        self.restart_times = {}   # Track restart timestamps
        self.max_restarts = 3     # Max restarts allowed
        self.time_window = 600    # Time window in seconds (10 minutes)

        # Define services to monitor based on environment
        base_services = [
            "platinum_local_orchestrator.py",
            "approval_executor.py",
            "dashboard_merger.py"
        ]

        # Add cloud-specific services
        if self.is_cloud:
            base_services.extend([
                "cloud_orchestrator.py",
                "email_watcher.py"
            ])

        # Add MCP services (these run on both cloud and local if needed)
        base_services.extend([
            "odoo_draft_mcp.py",      # Draft operations (typically cloud)
            "odoo_execute_mcp.py"     # Execute operations (typically local)
        ])

        self.services = base_services

        # Add heartbeat file path
        self.heartbeat_file = Path("heartbeat.md")

        # Alert log
        self.alert_log = logs_dir / "alerts.md"

        logger.info(f"Platinum Watchdog initialized (is_cloud={self.is_cloud})")
        logger.info(f"Monitoring services: {self.services}")

    def is_process_running(self, process_name):
        """Check if a process is running using tasklist on Windows"""
        try:
            # Extract just the filename without path
            if '\\' in process_name:
                process_exe = process_name.split('\\')[-1]
            else:
                process_exe = process_name

            # On Windows, use tasklist to check running processes
            result = subprocess.run(['tasklist'], capture_output=True, text=True, shell=True)

            # Check if the process name appears in the tasklist output
            # We need to find the Python processes and see if they're running our specific script
            lines = result.stdout.split('\n')

            for line in lines:
                if 'python' in line.lower() and process_name in line:
                    return True
                elif process_exe.replace('.py', '.exe') in line.lower():
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking if {process_name} is running: {e}")
            return False

    def start_service(self, service_name):
        """Start a service using subprocess in a separate thread"""
        try:
            logger.info(f"Starting {service_name}...")

            # Create logs directory for this service if it doesn't exist
            service_logs_dir = Path("Service_Logs")
            service_logs_dir.mkdir(exist_ok=True)

            # Create a separate thread to run the subprocess
            def run_service():
                try:
                    # Use the current Python interpreter to run the service
                    log_file = service_logs_dir / f"{service_name.replace('.py', '')}.log"

                    with open(log_file, 'a') as log:
                        process = subprocess.Popen(
                            [sys.executable, service_name],
                            stdout=log,
                            stderr=log,
                            text=True
                        )
                        # Keep the process running in this thread
                        process.wait()

                except Exception as e:
                    logger.error(f"Error running {service_name}: {e}")

            # Start the service in a new thread
            service_thread = threading.Thread(target=run_service, daemon=True)
            service_thread.start()

            # Give it a moment to start
            time.sleep(3)

            # Check if it's now running
            return self.is_process_running(service_name)

        except Exception as e:
            logger.error(f"Error starting {service_name}: {e}")
            return False

    def increment_restart_count(self, service_name):
        """Increment restart count and check for excessive restarts"""
        now = datetime.now()

        if service_name not in self.restart_counts:
            self.restart_counts[service_name] = []
            self.restart_times[service_name] = []

        # Add current restart time
        self.restart_times[service_name].append(now)

        # Filter times within the time window
        window_start = now - timedelta(seconds=self.time_window)
        recent_restarts = [
            t for t in self.restart_times[service_name]
            if t >= window_start
        ]
        self.restart_times[service_name] = recent_restarts

        restart_count = len(recent_restarts)

        logger.info(f"Service {service_name} restart count: {restart_count} in last {self.time_window}s")

        # Check if too many restarts
        if restart_count >= self.max_restarts:
            self.log_alert(service_name, f"Excessive restarts: {restart_count} in {self.time_window}s")
            return True  # Too many restarts

        return False  # Normal restart count

    def log_alert(self, service_name, message):
        """Log an alert to the alerts file"""
        try:
            alert_entry = f"""
## Alert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Service**: {service_name}
- **Issue**: {message}
- **Severity**: HIGH
"""
            with open(self.alert_log, 'a') as f:
                f.write(alert_entry + "\n")

            logger.warning(f"ALERT LOGGED: {message}")
        except Exception as e:
            logger.error(f"Error logging alert: {e}")

    def send_health_ping(self):
        """Send health ping to local (if cloud) or update heartbeat file"""
        try:
            if self.is_cloud:
                # For cloud, we could implement a simple HTTP ping to local
                # For now, just update the heartbeat file
                self.update_heartbeat()
                logger.info("Health ping sent (cloud mode)")
            else:
                # For local, just update heartbeat
                self.update_heartbeat()
                logger.info("Local heartbeat updated")

        except Exception as e:
            logger.error(f"Error sending health ping: {e}")

    def update_heartbeat(self):
        """Update heartbeat file with current timestamp"""
        try:
            heartbeat_data = {
                "timestamp": datetime.now().isoformat(),
                "service": "platinum_watchdog",
                "is_cloud": self.is_cloud,
                "status": "healthy",
                "services_monitored": self.services
            }

            with open(self.heartbeat_file, 'w') as f:
                f.write(f"# System Heartbeat\n\n")
                f.write(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Environment**: {'Cloud' if self.is_cloud else 'Local'}\n")
                f.write(f"**Status**: Healthy\n")
                f.write(f"**Services Monitored**: {len(self.services)}\n")
                f.write(f"**Details**: {json.dumps(heartbeat_data, indent=2)}\n")

        except Exception as e:
            logger.error(f"Error updating heartbeat: {e}")

    def check_and_restart_services(self):
        """Check all services and restart dead ones"""
        for service in self.services:
            # Only check services that exist
            if not Path(service).exists():
                continue

            if not self.is_process_running(service):
                logger.warning(f"Service {service} is not running, attempting restart...")

                # Check restart count
                excessive_restarts = self.increment_restart_count(service)
                if excessive_restarts:
                    logger.error(f"Too many restarts for {service}, skipping restart")
                    continue

                # Attempt restart
                if self.start_service(service):
                    logger.info(f"Successfully restarted {service}")
                else:
                    logger.error(f"Failed to restart {service}")
            else:
                # Service is running, update our tracking but don't reset if it was recently restarted
                if service in self.restart_times:
                    # Keep only recent restart times (within window)
                    now = datetime.now()
                    window_start = now - timedelta(seconds=self.time_window)
                    recent_restarts = [
                        t for t in self.restart_times[service]
                        if t >= window_start
                    ]
                    self.restart_times[service] = recent_restarts

    def run(self):
        """Main watchdog loop"""
        logger.info("Platinum Watchdog started")
        logger.info(f"Running in {'cloud' if self.is_cloud else 'local'} mode")

        # Initial heartbeat
        self.update_heartbeat()

        while True:
            try:
                # Check all services
                self.check_and_restart_services()

                # Send health ping
                self.send_health_ping()

                # Wait before next check
                time.sleep(30)  # Check every 30 seconds

            except KeyboardInterrupt:
                logger.info("Platinum Watchdog stopped by user")
                break
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait longer if there's an error


def main():
    # Determine if this is cloud or local based on command line argument
    parser = argparse.ArgumentParser(description='Platinum Watchdog')
    parser.add_argument('--env', choices=['cloud', 'local'], required=True,
                       help='Environment type: cloud or local')
    args = parser.parse_args()

    is_cloud = args.env == 'cloud'

    watchdog = PlatinumWatchdog(is_cloud=is_cloud)
    watchdog.run()


if __name__ == "__main__":
    main()