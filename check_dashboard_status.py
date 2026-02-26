"""
Quick dashboard status checker for AI Employee Vault
"""
import json
from datetime import datetime
from pathlib import Path

def check_dashboard_status():
    print("AI EMPLOYEE VAULT - CURRENT DASHBOARD STATUS")
    print("=" * 50)

    # Check main dashboard file
    dashboard_file = Path("Dashboard.md")
    if dashboard_file.exists():
        print(f"[OK] Main Dashboard: {dashboard_file}")
        content = dashboard_file.read_text()
        lines = content.split('\n')

        for line in lines:
            if line.startswith('- **Date:**'):
                print(f"  Date: {line.split(':', 1)[1].strip()}")
            elif line.startswith('- **Last Processed:**'):
                print(f"  Last Processed: {line.split(':', 1)[1].strip()}")
            elif line.startswith('- **AI Employee Status:**'):
                print(f"  Status: {line.split(':', 1)[1].strip()}")

    print()

    # Count files in key directories
    key_dirs = ["Inbox", "Needs_Action", "Done", "Approved", "Pending_Approval", "Plans"]
    print("DIRECTORY STATUS:")
    for dir_name in key_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            files = list(dir_path.glob('*'))
            print(f"  {dir_name}: {len(files)} files")
        else:
            print(f"  {dir_name}: *NOT FOUND*")

    print()

    # Check if sample files from our demo are there
    print("SAMPLE DATA FROM DEMO:")
    demo_files = [
        "Inbox/new_client_inquiry.md",
        "Inbox/quarterly_review_task.md",
        "Plans/PLAN_new_client_inquiry.md",
        "Plans/PLAN_quarterly_review_task.md",
        "Needs_Action/new_client_inquiry.md",
        "Needs_Action/quarterly_review_task.md"
    ]

    for file_path in demo_files:
        exists = Path(file_path).exists()
        status = "EXISTS" if exists else "MISSING"
        print(f"  {file_path}: {status}")

    print()
    print("SYSTEM HEALTH INDICATORS:")

    # Check the current timestamp
    current_time = datetime.now()
    print(f"  Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Show the dashboard stats that exist
    if dashboard_file.exists():
        content = dashboard_file.read_text()
        lines = content.split('\n')
        print("  Dashboard Quick Stats:")
        for line in lines:
            if any(stat in line for stat in ["Files in Inbox:", "Files in Needs_Action:",
                                           "Files in Approved:", "Files in Done:",
                                           "Pending Approvals:"]):
                print(f"    {line.strip()}")

if __name__ == "__main__":
    check_dashboard_status()