#!/bin/bash

# Cloud Push Script for AI Employee Vault
# Runs on cloud VM - pushes changes to git every 3-5 minutes
# Only pushes changes, no merges or pulls from cloud side

VAULT_DIR="$HOME/AI_Employee_Vault"
LOG_FILE="$VAULT_DIR/Logs/cloud_sync.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Log start of sync
log_message "Starting cloud push sync"

# Check if we're in the right directory
if [ ! -d "$VAULT_DIR/.git" ]; then
    log_message "ERROR: Not in a git repository or .git not found"
    exit 1
fi

cd "$VAULT_DIR"

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    log_message "No changes to commit"
    exit 0
fi

# Add all tracked files and new files (but not untracked credentials or sessions)
git add -A

# Check again if there are staged changes
if [ -z "$(git diff --cached --name-only)" ]; then
    log_message "No changes staged after git add"
    exit 0
fi

# Commit changes
COMMIT_MSG="Cloud auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
if git commit -m "$COMMIT_MSG"; then
    log_message "Changes committed successfully"

    # Push to remote
    if git push origin main; then
        log_message "Changes pushed successfully"
    else
        log_message "ERROR: Failed to push changes"
        exit 1
    fi
else
    log_message "No changes to commit (all changes might be in ignored files)"
fi

log_message "Cloud push sync completed"