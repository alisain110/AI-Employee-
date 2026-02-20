"""
Approval Monitor - Background task to process approval requests
"""
import time
import threading
from pathlib import Path
from utilities.human_approval import check_for_approvals, approval_monitor

def run_approval_monitor():
    """
    Run the approval monitor as a background task
    """
    print("Starting Approval Monitor...")
    print("This will run in the background to process approval requests")

    # Run the monitor function (which contains an infinite loop)
    approval_monitor()

def run_approval_monitor_daemon():
    """
    Run the approval monitor as a daemon thread
    """
    monitor_thread = threading.Thread(target=run_approval_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

if __name__ == "__main__":
    print("AI Employee Approval Monitor")
    print("="*40)
    print("Starting approval monitoring system...")
    print("Press Ctrl+C to stop")

    try:
        # Run the approval monitor
        approval_monitor()
    except KeyboardInterrupt:
        print("\nStopping approval monitor...")
        print("Approval monitor stopped.")