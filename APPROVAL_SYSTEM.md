# Human Approval System

This document describes the human approval system for sensitive AI actions.

## Overview

The approval system provides a secure way to require human approval before executing sensitive actions like sending emails, posting to LinkedIn, or making other external API calls.

## Approval Decorator

The `@requires_human_approval` decorator is applied to sensitive functions to require human approval before execution.

## Two Operating Modes

### 1. Console Mode (Default)
- Prompts user interactively for approval
- Asks "YES/NO" for each sensitive action
- Good for development and direct interaction

### 2. Production Mode
- Uses file-based approval system
- Creates approval requests in `Pending_Approval/` folder
- Waits for files to be moved to `Approved/` or `Rejected/` folder
- Includes timeout handling

## How to Set Mode

Set environment variable:
```bash
APPROVAL_MODE=console    # For interactive approval
APPROVAL_MODE=production # For file-based approval
```

## Sensitive Actions That Require Approval

- `linkedin_auto_post` - LinkedIn posts
- `send_email_skill` - Sending emails
- `execute_action_skill` - Generic actions
- Any future sensitive operations

## Folder Structure

```
Pending_Approval/    # Approval requests waiting for decision
├── APPROVAL_*.md
Approved/            # Approved requests
├── APPROVAL_*.md
Rejected/            # Rejected requests
├── APPROVAL_*.md
approvals/           # Additional approval-related files
notifications/       # Approval notifications (in extended system)
```

## How Approval Works

### In Console Mode:
1. Function is called
2. User is prompted: "Do you approve this action? (YES/NO)"
3. If YES: function executes
4. If NO: function is cancelled

### In Production Mode:
1. Function is called
2. Approval request file is created in `Pending_Approval/`
3. System waits for file to be moved to `Approved/` or `Rejected/`
4. If Approved: function executes
5. If Rejected: function is cancelled
6. If timeout: function is cancelled

## Background Approval Monitoring

For scheduled background tasks, you can run the approval monitor:

```python
from approval_monitor import approval_monitor
import threading

# Run approval monitor in background thread
monitor_thread = threading.Thread(target=approval_monitor, daemon=True)
monitor_thread.start()
```

The monitor periodically checks for pending approvals and can process them automatically if configured.

## Example Usage

### Setting Console Mode:
```python
import os
os.environ['APPROVAL_MODE'] = 'console'

from skills.linkedin_auto_post import linkedin_auto_post
# Will prompt user interactively
result = linkedin_auto_post(post_topic="AI trends", context="Share insights")
```

### Setting Production Mode:
```python
import os
os.environ['APPROVAL_MODE'] = 'production'

from skills.send_email_skill import send_email_skill
# Will create approval request file, wait for approval
result = send_email_skill(to="user@example.com", subject="Test", body="Body")
```

## Timeout Configuration

The production mode has a default timeout of 1 hour. You can modify this in the `human_approval.py` file by changing the `max_wait_time` variable.

## Integration with Existing Systems

The approval system integrates seamlessly with:
- The MCP server client skills
- LinkedIn auto-post functionality
- Any other sensitive operations
- The existing folder-based workflow
- Claude reasoning loops

## Security Benefits

- Prevents unauthorized external actions
- Provides audit trail of all sensitive operations
- Maintains human oversight on important decisions
- Supports both interactive and unattended operation modes
- Includes proper error handling and timeout management