#!/bin/bash

# Local Pull and Merge Script for AI Employee Vault
# Runs on local machine - pulls from cloud, processes updates, then pushes

VAULT_DIR="$HOME/AI_Employee_Vault"
LOG_FILE="$VAULT_DIR/Logs/local_sync.log"
UPDATES_DIR="$VAULT_DIR/Updates"
DASHBOARD_FILE="$VAULT_DIR/Dashboard.md"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log_message "Starting local pull and merge sync"

# Check if we're in the right directory
if [ ! -d "$VAULT_DIR/.git" ]; then
    log_message "ERROR: Not in a git repository or .git not found"
    exit 1
fi

cd "$VAULT_DIR"

# Pull latest changes from remote
if git pull origin main; then
    log_message "Successfully pulled from remote"
else
    log_message "ERROR: Failed to pull from remote"
    exit 1
fi

# Process any update files from cloud
if [ -d "$UPDATES_DIR" ] && [ -n "$(ls -A $UPDATES_DIR/*.md 2>/dev/null)" ]; then
    log_message "Processing update files from cloud"

    # Process each update file
    for update_file in "$UPDATES_DIR"/*.md; do
        if [ -f "$update_file" ]; then
            log_message "Processing update file: $update_file"

            # Get the filename without path
            filename=$(basename "$update_file")

            # Append the update to Dashboard.md with a timestamp and source
            {
                echo ""
                echo "## Update from cloud: ${filename} (added $(date))"
                echo ""
                cat "$update_file"
                echo ""
                echo "---"
                echo ""
            } >> "$DASHBOARD_FILE"

            # Add the processed update to git (so it gets removed in next step)
            git add "$update_file"
        fi
    done

    # Commit the dashboard changes and remove processed update files
    git add "$DASHBOARD_FILE"
    if git commit -m "Merge cloud updates to dashboard and cleanup: $(date)"; then
        log_message "Dashboard merged and update files committed"
    fi
else
    log_message "No update files to process"
fi

# Push any local changes back to remote
if [ -n "$(git status --porcelain)" ]; then
    if git push origin main; then
        log_message "Local changes pushed successfully"
    else
        log_message "ERROR: Failed to push local changes"
        exit 1
    fi
else
    log_message "No local changes to push"
fi

log_message "Local pull and merge sync completed"