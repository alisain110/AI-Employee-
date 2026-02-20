# Platinum Tier Minimum Demo Script

## Goal
Test the complete flow: Email arrives → Cloud drafts reply → writes approval file → git sync → Local sees it → human approves → Local sends real reply → log + move to Done.

## Prerequisites

Before starting the demo, ensure:
- Cloud orchestrator is running (`cloud_orchestrator.py`)
- Local orchestrator is running (`platinum_local_orchestrator.py`)
- Approval executor is running (`approval_executor.py`)
- Git sync is configured between cloud and local
- Gmail API credentials are properly configured in `.env`
- Dashboard merger is running

## Test Procedure

### Step 1: Send test email to yourself
1. Send an email from another email account to your monitored email address
2. Subject: "Demo Test: Please Reply"
3. Body: "This is a test email for the Platinum Tier demo. Please send me a reply."

### Step 2: Wait for cloud watcher → draft created
1. Monitor cloud orchestrator logs: `tail -f Logs/cloud_orchestrator.log`
2. Wait for messages showing:
   - "New email detected"
   - "Draft reply created"
   - "Approval request generated"
3. Verify approval file is created in: `Pending_Approval/cloud/`
   - Check with: `ls -la Pending_Approval/cloud/`
   - File should be named like: `email_reply_YYYYMMDD_HHMMSS.json`

### Step 3: Git pull on local → see Pending_Approval/cloud/
1. On local machine, run: `git pull origin main`
2. Verify the approval file appeared: `ls -la Pending_Approval/cloud/`
3. Check file contents: `cat Pending_Approval/cloud/email_reply_*.json`

### Step 4: Move to Approved/
1. Manually move the approval file to Approved directory:
   ```bash
   mv Pending_Approval/cloud/email_reply_*.json Approved/
   ```
2. This triggers the approval executor to process the request

### Step 5: Local executes send
1. Monitor approval executor logs: `tail -f Logs/approval_executor.log`
2. Wait for:
   - "Processing approved request"
   - "Email sent successfully"
3. Check your email to confirm the reply was sent

### Step 6: Check Dashboard update + /Done/
1. Verify dashboard was updated: `cat Dashboard.md`
2. Look for the new entry in "Recent Activity"
3. Check that the approval file was moved to Done: `ls -la Done/`
4. Verify logs show complete process in `Logs/platinum_local_orchestrator.log`

## Expected Results

- An email reply is sent back to the original sender
- Dashboard.md shows the completed action
- The approval file moves from Approved/ to Done/
- All actions are logged in the respective log files

## Troubleshooting Tips

### Common Issues

#### 1. Cloud watcher not detecting email
- **Check logs**: `cat Logs/cloud_orchestrator.log | grep -i error`
- **Verify credentials**: `cat .env | grep GMAIL`
- **Check Gmail API access**: Ensure OAuth is properly configured
- **Restart cloud orchestrator**: `python cloud_orchestrator.py`

#### 2. Git sync not working
- **Check git status**: `git status`
- **Check remote**: `git remote -v`
- **Manual sync**: `git pull origin main && git push origin main`
- **Check git logs**: Look for sync errors in related logs

#### 3. Approval file not appearing locally
- **Verify git sync**: `git log --oneline -5`
- **Check directories**: Ensure `Pending_Approval/cloud/` exists
- **Check file permissions**: `ls -la Pending_Approval/`

#### 4. Local orchestrator not processing
- **Check if running**: `ps aux | grep orchestrator`
- **Check logs**: `cat Logs/platinum_local_orchestrator.log`
- **Check approval executor**: `cat Logs/approval_executor.log`
- **Verify file movement**: Ensure files are moved to `Approved/` directory

#### 5. Email not sending
- **Check logs**: `cat Logs/approval_executor.log | grep -i error`
- **Verify Gmail credentials**: Check `.env` file
- **Test API connection**: Verify OAuth tokens are valid
- **Check rate limits**: Gmail may have rate limiting

### Log Files to Monitor

#### Cloud Side:
- `Logs/cloud_orchestrator.log` - Main cloud operations
- `Logs/email_watcher.log` - Email detection activities

#### Local Side:
- `Logs/platinum_local_orchestrator.log` - Local orchestration
- `Logs/approval_executor.log` - Approval processing
- `Logs/dashboard_merger.log` - Dashboard updates
- `Logs/gmail_actions.log` - Email sending logs

### Status Commands

#### Check all services:
```bash
# Check if orchestrators are running
ps aux | grep -E "(orchestrator|approval|dashboard)"

# Check all log files for recent activity
tail -n 10 Logs/*.log

# Check git status
git status
git log --oneline -3
```

#### Check directories:
```bash
# Check all relevant directories
ls -la Inbox/
ls -la Pending_Approval/cloud/
ls -la Approved/
ls -la Done/
ls -la Updates/
```

### Quick Reset for Demo

If you need to reset for another demo run:
```bash
# Move any pending files to safe location
mkdir -p reset_backup_$(date +%Y%m%d_%H%M%S)
mv Pending_Approval/cloud/* reset_backup_*/ 2>/dev/null || true
mv Approved/* reset_backup_*/ 2>/dev/null || true

# Clear recent dashboard entries (keep structure)
cp Dashboard.md Dashboard_backup_$(date +%Y%m%d_%H%M%S).md
# Keep only the first part of dashboard, remove recent activity
sed -i '/## Recent Activity/,$d' Dashboard.md
echo "## Recent Activity" >> Dashboard.md

# Force git sync
git add . && git commit -m "Demo reset" && git push origin main
```

### Debug Mode
For more detailed troubleshooting:
1. Set `DEBUG=true` in your `.env` file
2. Use `--debug` flag when starting services if available
3. Check timestamps in logs to verify sequence of operations
4. Monitor every 5 seconds: `watch -n 5 'ls -la Pending_Approval/cloud/ && ls -la Approved/ && ls -la Done/'`

### Success Indicators
- ✅ Email detected on cloud side
- ✅ Draft created and approval file generated
- ✅ Git sync brings file to local
- ✅ Approval file moved to Approved/
- ✅ Email reply sent successfully
- ✅ Dashboard updated with activity
- ✅ Approval file moved to Done/
- ✅ All actions logged appropriately