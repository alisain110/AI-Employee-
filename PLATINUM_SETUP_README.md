# Platinum Tier Local Setup

This document explains the Platinum Tier Local Orchestrator and related components for the hybrid cloud+local AI Employee Vault.

## Architecture Overview

The platinum tier follows a "cloud-draft + local-execute" pattern:
- **Cloud**: Triage, drafting, read operations, draft approval requests
- **Local**: Execution of sensitive actions, final posting, sending, payments

## Components

### 1. Platinum Local Orchestrator (`platinum_local_orchestrator.py`)
- Handles sensitive operations: WhatsApp session, real send/post, payments/banking, final Odoo invoice post
- Reviews cloud approval requests from `/Pending_Approval/cloud/`
- Executes final actions via local MCP servers when approved
- Implements claim-by-move rule to prevent double-processing
- Maintains dashboard and system status

### 2. Approval Executor (`approval_executor.py`)
- Watches for files moved to `/Approved/` directory
- Executes final actions based on approval type:
  - Real email sending
  - Social media posting
  - Odoo invoice/customer creation
  - WhatsApp messaging
- Logs all executed actions for audit trail

### 3. Dashboard Merger (`dashboard_merger.py`)
- Safely merges updates from `/Updates/` directory into `Dashboard.md`
- Appends content without overwriting existing dashboard structure
- Archives processed updates to prevent reprocessing
- Handles cloud-to-local dashboard updates

### 4. Local MCP Servers
- Real execution endpoints for sensitive operations
- Connected to actual external services (email, social media, Odoo)

## Key Responsibilities (Local Only)

### Sensitive Operations
- ✅ WhatsApp session management and messaging
- ✅ Real email sending (not just drafts)
- ✅ Social media posting to actual platforms
- ✅ Banking and payment operations
- ✅ Final Odoo invoice posting
- ✅ Customer creation in production systems

### Approval Workflow
1. Cloud creates approval request in `/Pending_Approval/cloud/`
2. Local orchestrator reviews request
3. Human moves to `/Approved/` or `/Rejected/`
4. Approval executor processes `/Approved/` requests
5. Final actions executed via local MCP

### Claim-by-Move Rule
- Local orchestrator ignores files in `/In_Progress/local/`
- Prevents double-processing when cloud tries to claim already-claimed tasks

## Setup Instructions

1. **Configure Environment**
   ```bash
   # Ensure .env contains local credentials for:
   # - WhatsApp session files
   # - Real email credentials
   # - Social media API keys
   # - Odoo production credentials
   # - Banking APIs
   ```

2. **Start Local Services**
   ```bash
   python start_platinum_services.py
   ```

3. **Configure Git Sync** (if not already done)
   ```bash
   # Setup git sync with cloud
   # Configure cloud_push.sh and local_pull_merge.sh crontabs
   ```

## Safety Features

1. **Separation of Duties**: Cloud for drafting, local for execution
2. **Approval Workflow**: Human review for sensitive operations
3. **Audit Logging**: All actions logged with audit_logger
4. **Claim-by-Move**: Prevents double-processing
5. **Archive Processing**: Prevents reprocessing of completed tasks

## Directory Structure

```
Vault/
├── Needs_Action/           # Tasks requiring processing
├── In_Progress/
│   └── local/             # Local-claimed tasks
├── Pending_Approval/
│   └── cloud/             # Cloud-generated approval requests
├── Approved/
│   ├── archived/          # Processed approvals
│   └── (active approvals)
├── Rejected/              # Rejected approval requests
├── Updates/               # Cloud updates for dashboard
│   └── archive/           # Processed updates
├── Signals/               # Cloud signals
│   └── archive/           # Processed signals
├── Done/                  # Completed tasks
└── Dashboard.md           # Merged dashboard
```

## Health Monitoring

All local services maintain their own logs in the `Logs/` directory:
- `platinum_local_orchestrator.log`
- `approval_executor.log`
- `dashboard_merger.log`