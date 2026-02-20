# Platinum Tier Cloud Setup

This document explains the Cloud Orchestrator Lite and related components for the Platinum Tier AI Employee Vault.

## Architecture Overview

The cloud setup follows a "draft and approve" pattern:
- **Cloud**: Triage, drafting, read operations, approval requests
- **Local**: Execution of sensitive actions, final posting, sending

## Components

### 1. Cloud Orchestrator Lite (`cloud_orchestrator_lite.py`)
- Lightweight orchestrator for cloud operations only
- Handles email triage, social post drafts, Odoo read/draft operations
- Never performs final actions (no real payments, no final posts)
- Uses Ralph Wiggum loop for complex multi-step tasks
- Moves files to `/In_Progress/cloud/` when claimed

### 2. Cloud Watchers (`cloud_watchers.py`)
- Gmail watcher: Monitors emails and creates tasks (no sending)
- Social watcher: Monitors social media mentions (no posting)
- Only runs on cloud for monitoring purposes

### 3. Draft MCP Servers
- `gmail_draft_mcp.py`: Creates email drafts and approval requests (no sending)
- `odoo_draft_mcp.py`: Creates Odoo draft actions and approval requests (no execution)

### 4. Health Endpoint (`cloud_health.py`)
- `/health` endpoint reporting system status
- Tracks last heartbeat and service health

## Key Differences from Local Orchestrator

### Cloud-Only Operations
- ✅ Email triage and draft creation
- ✅ Social media post drafting
- ✅ Odoo read operations and analysis
- ✅ Approval request generation
- ❌ No WhatsApp sending
- ❌ No real payments
- ❌ No final LinkedIn/Facebook/Instagram posts
- ❌ No sensitive financial operations

### Claim-by-Move Rule
- Cloud agent moves files from `/Needs_Action/` → `/In_Progress/cloud/`
- Local agent ignores files already in `/In_Progress/*/`
- Prevents double-processing of tasks

### Approval Workflow
1. Cloud creates draft or analyzes request
2. If sensitive action needed → create `/Pending_Approval/cloud/` file
3. Git sync moves file to local system
4. Local user reviews and approves
5. Local system executes final action

## Environment Variables (for .env.local on cloud)

```bash
# API Keys for cloud services
ANTHROPIC_API_KEY=your_claude_api_key

# Gmail draft operations
GMAIL_DRAFT_API_KEY=your_gmail_draft_api_key

# Odoo draft operations
ODOO_DRAFT_API_KEY=your_odoo_draft_api_key

# Gmail credentials (for reading only)
GMAIL_ADDRESS=your_gmail_address
GMAIL_APP_PASSWORD=your_app_password

# Social media credentials (for reading only)
FACEBOOK_PAGE_TOKEN=your_facebook_token
TWITTER_BEARER_TOKEN=your_twitter_token
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
```

## Git Sync Rules

### Excluded Files (in .gitignore)
- `.env`, `*.session`, `/WhatsApp_Sessions/`, `/Banking_Creds/`
- `/node_modules/`, `/.claude/cache/`
- Only sync markdown, logs, plans, approvals

### Cloud-Specific Directories
- `/Updates/` or `/Signals/` - Cloud writes updates here (not directly to Dashboard.md)
- `/In_Progress/cloud/` - Cloud-claimed tasks
- `/Pending_Approval/cloud/` - Cloud-generated approval requests

## Setup Instructions

1. **Configure Environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your cloud-specific credentials
   ```

2. **Start Cloud Services**
   ```bash
   python start_cloud_services.py
   ```

3. **Setup Git Sync** (run on both cloud and local)
   ```bash
   # On first setup only
   git init
   git remote add origin your_git_repo_url
   git add .
   git commit -m "Initial cloud setup"
   git push -u origin main
   ```

4. **Setup Crontab for Syncing**
   - On cloud: `cloud_push.sh` every 3 minutes
   - On local: `local_pull_merge.sh` every 5 minutes

## Health Check

Services can be checked at:
- Health endpoint: `http://your-cloud-vm:8006/health`
- Status endpoint: `http://your-cloud-vm:8006/status`

## Safety Features

1. **No Direct Action Execution**: Cloud never executes final actions
2. **Approval Workflow**: Sensitive operations require local approval
3. **Claim-by-Move**: Prevents double-processing
4. **Git Synchronization**: Secure sync with proper file exclusions
5. **Health Monitoring**: Continuous system status monitoring