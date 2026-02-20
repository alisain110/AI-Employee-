"""
Start script for Cloud Orchestrator Lite and related services
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
        logging.FileHandler(logs_dir / "cloud_startup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_service(script_name, port=None):
    """Start a service in a subprocess"""
    try:
        cmd = [sys.executable, script_name]
        if port:
            # For FastAPI services, we'll use uvicorn
            cmd = [sys.executable, "-c", f"import uvicorn; uvicorn.run('{script_name.replace('.py', '')}:app', host='0.0.0.0', port={port}, log_level='info')"]

        logger.info(f"Starting {script_name}...")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
    except Exception as e:
        logger.error(f"Failed to start {script_name}: {e}")
        return None

def main():
    """Start all cloud services"""
    logger.info("Starting Cloud Orchestrator Lite services...")

    processes = []

    # Start cloud orchestrator
    logger.info("Starting Cloud Orchestrator Lite...")
    orchestrator_process = start_service("cloud_orchestrator_lite.py")
    if orchestrator_process:
        processes.append(("Cloud Orchestrator", orchestrator_process))

    # Start cloud watchers
    logger.info("Starting Cloud Watchers...")
    # For watchers, we'll start them in the background
    watchers_process = start_service("cloud_watchers.py", None)
    if watchers_process:
        processes.append(("Cloud Watchers", watchers_process))

    # Start MCP servers
    logger.info("Starting Cloud MCP Servers...")

    # Gmail Draft MCP Server
    gmail_mcp_process = start_service("gmail_draft_mcp.py")  # This would be run with uvicorn
    if gmail_mcp_process:
        processes.append(("Gmail Draft MCP", gmail_mcp_process))

    # Odoo Draft MCP Server
    odoo_mcp_process = start_service("odoo_draft_mcp.py")  # This would be run with uvicorn
    if odoo_mcp_process:
        processes.append(("Odoo Draft MCP", odoo_mcp_process))

    # Start Health Check Server
    health_process = start_service("cloud_health.py")  # This would be run with uvicorn
    if health_process:
        processes.append(("Health Check", health_process))

    logger.info(f"Started {len(processes)} services successfully!")

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
                        restarted = start_service("cloud_orchestrator_lite.py")
                    elif "watchers" in name.lower():
                        restarted = start_service("cloud_watchers.py")
                    elif "gmail" in name.lower():
                        restarted = start_service("gmail_draft_mcp.py")
                    elif "odoo" in name.lower():
                        restarted = start_service("odoo_draft_mcp.py")
                    elif "health" in name.lower():
                        restarted = start_service("cloud_health.py")

                    if restarted:
                        # Update the process in the list
                        processes = [(n, p) for n, p in processes if n != name]
                        processes.append((name, restarted))
                        logger.info(f"Successfully restarted {name}")
                    else:
                        logger.error(f"Failed to restart {name}")

    except KeyboardInterrupt:
        logger.info("Stopping Cloud Orchestrator Lite services...")
        for name, process in processes:
            logger.info(f"Terminating {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if not responding
        logger.info("All services stopped.")

if __name__ == "__main__":
    main()