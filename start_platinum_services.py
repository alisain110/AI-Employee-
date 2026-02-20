"""
Start script for Platinum Tier Local Services
Starts local orchestrator, approval executor, and dashboard merger
"""
import subprocess
import sys
import os
from pathlib import Path
import time
import logging

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "platinum_startup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_service(script_name):
    """Start a service in a subprocess"""
    try:
        cmd = [sys.executable, script_name]
        logger.info(f"Starting {script_name}...")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return process
    except Exception as e:
        logger.error(f"Failed to start {script_name}: {e}")
        return None

def main():
    """Start all platinum local services"""
    logger.info("Starting Platinum Tier Local Services...")

    processes = []

    # Start platinum local orchestrator
    logger.info("Starting Platinum Local Orchestrator...")
    orchestrator_process = start_service("platinum_local_orchestrator.py")
    if orchestrator_process:
        processes.append(("Platinum Orchestrator", orchestrator_process))

    # Start approval executor
    logger.info("Starting Approval Executor...")
    approval_process = start_service("approval_executor.py")
    if approval_process:
        processes.append(("Approval Executor", approval_process))

    # Start dashboard merger
    logger.info("Starting Dashboard Merger...")
    merger_process = start_service("dashboard_merger.py")
    if merger_process:
        processes.append(("Dashboard Merger", merger_process))

    logger.info(f"Started {len(processes)} platinum services successfully!")

    # Keep the main process alive
    try:
        while True:
            time.sleep(10)  # Check every 10 seconds

            # Check if any processes have died
            for name, process in processes[:]:  # Make a copy to iterate safely
                if process.poll() is not None:
                    logger.warning(f"{name} process has died with return code {process.returncode}")
                    # Try to restart the process
                    logger.info(f"Attempting to restart {name}...")
                    if "orchestrator" in name.lower():
                        restarted = start_service("platinum_local_orchestrator.py")
                    elif "approval" in name.lower():
                        restarted = start_service("approval_executor.py")
                    elif "merger" in name.lower():
                        restarted = start_service("dashboard_merger.py")

                    if restarted:
                        # Update the process in the list
                        processes = [(n, p) for n, p in processes if n != name]
                        processes.append((name, restarted))
                        logger.info(f"Successfully restarted {name}")
                    else:
                        logger.error(f"Failed to restart {name}")

    except KeyboardInterrupt:
        logger.info("Stopping Platinum Tier Local Services...")
        for name, process in processes:
            logger.info(f"Terminating {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if not responding
        logger.info("All platinum services stopped.")

if __name__ == "__main__":
    main()