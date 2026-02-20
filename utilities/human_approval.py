"""
Human Approval System
Provides a decorator for requiring human approval before executing sensitive actions.
"""
import os
import functools
from pathlib import Path
from datetime import datetime
import uuid
import time
from typing import Optional

# Create approval directories if they don't exist
for folder in ['approvals', 'Pending_Approval', 'Approved', 'Rejected']:
    Path(folder).mkdir(exist_ok=True)

def requires_human_approval(func):
    """
    Decorator that requires human approval before executing the decorated function.
    Can work in console mode (interactive) or production mode (file-based approval).
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Determine if we're in console mode or production mode
        mode = os.getenv('APPROVAL_MODE', 'console').lower()  # 'console' or 'production'

        # Get function name for the approval request
        func_name = func.__name__

        # Define what functions require approval
        sensitive_functions = [
            'linkedin_auto_post',
            'send_email_skill',
            'execute_action_skill',
            'delete_file',  # Example of future sensitive operations
            'modify_config',
            'access_credentials'
        ]

        if func_name in sensitive_functions:
            if mode == 'console':
                # Console mode: ask for approval interactively
                print(f"\n--- HUMAN APPROVAL REQUIRED ---")
                print(f"Function: {func_name}")
                print(f"Arguments: args={args}, kwargs={kwargs}")
                print("-" * 40)

                while True:
                    response = input("Do you approve this action? (YES/NO): ").strip().upper()
                    if response in ['YES', 'Y']:
                        print("Approval granted. Proceeding with execution...")
                        return func(*args, **kwargs)
                    elif response in ['NO', 'N']:
                        print("Action cancelled by user.")
                        return {"status": "cancelled", "message": f"Action {func_name} cancelled by user"}
                    else:
                        print("Please respond with YES or NO.")
            else:
                # Production mode: use file-based approval system
                return _file_based_approval(func, func_name, args, kwargs)
        else:
            # Function doesn't require approval, execute normally
            return func(*args, **kwargs)

    return wrapper


def _file_based_approval(func, func_name: str, args: tuple, kwargs: dict):
    """
    Handle approval in production mode using file-based system.
    """
    # Create a unique token for this approval request
    approval_token = str(uuid.uuid4())

    # Create approval request file in Pending_Approval folder
    pending_dir = Path("Pending_Approval")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    approval_file = pending_dir / f"APPROVAL_{func_name}_{approval_token[:8]}_{timestamp}.md"

    # Create approval request content
    approval_content = f"""---
type: approval_request
action: {func_name}
status: pending
token: {approval_token}
created: {datetime.now().isoformat()}
---

# Approval Request for Action: {func_name}

## Action Details
- **Action**: {func_name}
- **Arguments**: {args}
- **Keyword Arguments**: {kwargs}

## Function Information
This action requires human approval before execution.

## Action Required
Review the above action and approve or reject it.

To approve: Move this file to the Approved folder
To reject: Move this file to the Rejected folder

The system will wait for your decision...
"""

    # Write the approval request
    with open(approval_file, 'w', encoding='utf-8') as f:
        f.write(approval_content)

    print(f"Approval request created: {approval_file.name}")
    print("Waiting for human approval...")

    # Wait for approval by checking the file's location
    approved_dir = Path("Approved")
    rejected_dir = Path("Rejected")

    max_wait_time = 3600  # Wait up to 1 hour
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        # Check if the file was moved to Approved or Rejected folder
        if approval_file.exists():
            # Still in pending, wait more
            time.sleep(5)
            continue
        else:
            # File was moved, check where it went
            # Look for the file in approved or rejected folders by token
            approved_file = None
            rejected_file = None

            for af in approved_dir.glob(f"APPROVAL_{func_name}_{approval_token[:8]}*"):
                approved_file = af
                break

            for rf in rejected_dir.glob(f"APPROVAL_{func_name}_{approval_token[:8]}*"):
                rejected_file = rf
                break

            if approved_file:
                print(f"Action approved. Executing {func_name}...")
                # Execute the original function
                result = func(*args, **kwargs)
                # Clean up by deleting the approved file after use
                try:
                    approved_file.unlink()
                except:
                    pass
                return result
            elif rejected_file:
                print(f"Action rejected. Skipping {func_name}...")
                try:
                    rejected_file.unlink()
                except:
                    pass
                return {"status": "rejected", "message": f"Action {func_name} was rejected"}
            else:
                # File was moved but couldn't find it in either folder
                # This shouldn't happen under normal circumstances
                time.sleep(5)
                continue

    # If we're here, we timed out waiting for approval
    print(f"Timeout waiting for approval of {func_name}. Action cancelled.")
    try:
        approval_file.unlink()  # Clean up pending file
    except:
        pass
    return {"status": "timeout", "message": f"Approval timeout for {func_name}"}


def send_approval_email(approval_token: str, action_details: str, recipient: str):
    """
    Send an email notification for approval (would use MCP server in real implementation).
    """
    # In a real implementation, this would call the MCP server to send an email
    # For now, we'll just create a notification file as a placeholder
    notifications_dir = Path("notifications")
    notifications_dir.mkdir(exist_ok=True)

    email_file = notifications_dir / f"approval_notification_{approval_token[:8]}.txt"
    with open(email_file, 'w', encoding='utf-8') as f:
        f.write(f"""APPROVAL NEEDED

Action: {action_details}
Token: {approval_token}

Please review and approve this action by moving the corresponding file
from Pending_Approval to either Approved or Rejected folder.
""")


def check_for_approvals():
    """
    Background function to check for approvals in the approval system.
    This can be run periodically to process approval requests.
    """
    pending_dir = Path("Pending_Approval")
    approved_dir = Path("Approved")
    rejected_dir = Path("Rejected")

    # Process any pending approvals
    pending_files = list(pending_dir.glob("APPROVAL_*.md"))

    for pending_file in pending_files:
        # In a real system, you might have a timeout check here
        # For now, we just check if there are pending files
        print(f"Pending approval request: {pending_file.name}")

    return len(pending_files)


# Example of how this might be used in a background task
def approval_monitor():
    """
    Background monitoring function for approval system.
    This could be run in a separate thread or scheduled task.
    """
    print("Approval monitor started...")

    while True:
        pending_count = check_for_approvals()
        if pending_count > 0:
            print(f"Found {pending_count} pending approval requests")

        # Wait before checking again (e.g., every 30 seconds)
        time.sleep(30)