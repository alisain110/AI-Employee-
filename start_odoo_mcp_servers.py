"""
Start script for Odoo MCP servers
Starts both odoo_draft_mcp and odoo_execute_mcp servers
"""

import subprocess
import sys
import os
from pathlib import Path
import time
import logging
import signal
import psutil

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "odoo_mcp_startup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_server(script_name, port):
    """Start a server in a subprocess"""
    try:
        cmd = [sys.executable, "-c", f"""
import uvicorn
import importlib.util

# Load the module
spec = importlib.util.spec_from_file_location("{script_name[:-3]}", "{script_name}")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

uvicorn.run(
    module.app,
    host="0.0.0.0",
    port={port},
    log_level="info",
    reload=False
)
"""]

        logger.info(f"Starting {script_name} on port {port}...")

        # Using a different method that's more compatible with Windows
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            f"{script_name[:-3]}:app",
            "--host", "0.0.0.0",
            "--port", str(port),
            "--reload", "False"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        return process
    except Exception as e:
        logger.error(f"Failed to start {script_name}: {e}")
        return None

def check_port_in_use(port):
    """Check if a port is already in use"""
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.info['connections'] or []:
                if conn.laddr.port == port:
                    return True, proc.info['pid'], proc.info['name']
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False, None, None

def main():
    """Start both Odoo MCP servers"""
    logger.info("Starting Odoo MCP Servers...")

    # Check if ports are available
    draft_port = 8001
    execute_port = 8002

    port_check, pid, proc_name = check_port_in_use(draft_port)
    if port_check:
        logger.warning(f"Port {draft_port} is already in use by {proc_name} (PID: {pid})")
        response = input(f"Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    port_check, pid, proc_name = check_port_in_use(execute_port)
    if port_check:
        logger.warning(f"Port {execute_port} is already in use by {proc_name} (PID: {pid})")
        response = input(f"Do you want to continue anyway? (y/n): ")
        if response.lower() != 'y':
            return

    processes = []

    # Start Odoo Draft MCP (cloud operations)
    logger.info("Starting Odoo Draft MCP Server...")
    draft_process = start_server("odoo_draft_mcp.py", draft_port)
    if draft_process:
        processes.append(("Odoo Draft MCP", draft_process))

    time.sleep(2)  # Give the first server a moment to start

    # Start Odoo Execute MCP (local operations)
    logger.info("Starting Odoo Execute MCP Server...")
    execute_process = start_server("odoo_execute_mcp.py", execute_port)
    if execute_process:
        processes.append(("Odoo Execute MCP", execute_process))

    if len(processes) == 2:
        logger.info(f"Started {len(processes)} Odoo MCP servers successfully!")
        logger.info("Odoo Draft MCP running on port 8001 (cloud operations)")
        logger.info("Odoo Execute MCP running on port 8002 (local operations)")
        logger.info("Press Ctrl+C to stop the servers")
    else:
        logger.error("Failed to start one or more servers")
        return

    # Keep the main process alive
    try:
        while True:
            time.sleep(10)  # Check every 10 seconds

            # Check if any processes have died
            for name, process in processes[:]:  # Make a copy to iterate safely
                if process.poll() is not None:
                    logger.warning(f"{name} process has died with return code {process.returncode}")

    except KeyboardInterrupt:
        logger.info("Stopping Odoo MCP Servers...")
        for name, process in processes:
            logger.info(f"Terminating {name}...")
            try:
                process.terminate()
                process.wait(timeout=5)  # Wait up to 5 seconds for graceful shutdown
            except subprocess.TimeoutExpired:
                process.kill()  # Force kill if not responding
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")

        logger.info("All Odoo MCP servers stopped.")

if __name__ == "__main__":
    main()