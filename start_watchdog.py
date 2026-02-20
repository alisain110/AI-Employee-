"""
Start script for Platinum Watchdog
Detects environment and starts watchdog accordingly
"""

import subprocess
import sys
import os
from pathlib import Path
import time
import logging
import argparse

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "watchdog_startup.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_environment():
    """Try to determine if this is cloud or local environment"""
    # Check for common cloud indicators
    cloud_indicators = [
        "CLOUD_ENV",  # Environment variable
        "CLOUD_INSTANCE",  # Cloud instance metadata
    ]

    # Check for local-specific services that might indicate local
    local_indicators = [
        "WHATSAPP_SESSION",  # Local-specific
        "LOCAL_MCP",  # Local-specific
    ]

    # Check environment variables
    for indicator in cloud_indicators:
        if os.getenv(indicator):
            return "cloud"

    for indicator in local_indicators:
        if os.getenv(indicator):
            return "local"

    # Default detection - could also check for specific local files
    if Path("local_config.json").exists() or Path("whatsapp_session").exists():
        return "local"
    else:
        # Default to local if no strong indicators
        return "local"  # Change to "cloud" if your cloud has specific indicators

def main():
    parser = argparse.ArgumentParser(description='Start Platinum Watchdog')
    parser.add_argument('--env', choices=['cloud', 'local'],
                       help='Force environment detection (optional)')
    parser.add_argument('--auto-detect', action='store_true',
                       help='Automatically detect environment')

    args = parser.parse_args()

    if args.env:
        environment = args.env
        logger.info(f"Using forced environment: {environment}")
    elif args.auto_detect:
        environment = check_environment()
        logger.info(f"Auto-detected environment: {environment}")
    else:
        # Ask user for environment
        print("Platinum Watchdog Startup")
        print("Select environment:")
        print("1. Cloud")
        print("2. Local")
        choice = input("Enter choice (1 or 2, or press Enter for auto-detect): ").strip()

        if choice == "1":
            environment = "cloud"
        elif choice == "2":
            environment = "local"
        else:
            environment = check_environment()
            print(f"Auto-detected environment: {environment}")

    logger.info(f"Starting Platinum Watchdog in {environment} mode")

    # Start the watchdog with the detected environment
    watchdog_script = "platinum_watchdog_win.py" if os.name == 'nt' else "platinum_watchdog.py"

    if not Path(watchdog_script).exists():
        logger.error(f"Watchdog script {watchdog_script} not found!")
        return

    try:
        cmd = [sys.executable, watchdog_script, f"--env={environment}"]
        logger.info(f"Starting watchdog with command: {' '.join(cmd)}")

        # Start the watchdog process
        process = subprocess.Popen(cmd)

        logger.info(f"Platinum Watchdog started with PID: {process.pid}")
        logger.info("Watchdog is now monitoring services...")
        logger.info(f"Environment: {environment}")
        logger.info("Check Logs/watchdog.log for detailed monitoring information")

        # Keep the script running to monitor the watchdog
        try:
            process.wait()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, terminating watchdog...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            logger.info("Watchdog terminated")

    except Exception as e:
        logger.error(f"Error starting watchdog: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()