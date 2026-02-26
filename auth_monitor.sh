#!/bin/bash
# Authentication Monitor Script for AI Employee Vault
# Checks if watchers are properly authenticated and running

PROJECT_DIR="/home/ubuntu/ai_employee_vault"
LOG_FILE="$PROJECT_DIR/logs/auth_monitor.log"

echo "$(date): Checking authentication status..." >> $LOG_FILE

# Check for Gmail authentication issues
if pm2 logs gmail-watcher --lines 10 2>/dev/null | grep -q -i "credentials file not found\|token\|auth"; then
    echo "$(date): WARNING - Gmail watcher may have authentication issues" >> $LOG_FILE
    echo "$(date): Gmail log snippet:" >> $LOG_FILE
    pm2 logs gmail-watcher --lines 5 2>/dev/null >> $LOG_FILE
fi

# Check for WhatsApp authentication issues
if pm2 logs whatsapp-watcher --lines 10 2>/dev/null | grep -q -i "qr code\|login\|session\|captcha"; then
    echo "$(date): WARNING - WhatsApp watcher may have authentication issues" >> $LOG_FILE
    echo "$(date): WhatsApp log snippet:" >> $LOG_FILE
    pm2 logs whatsapp-watcher --lines 5 2>/dev/null >> $LOG_FILE
fi

# Check for LinkedIn authentication issues
if pm2 logs linkedin-watcher --lines 10 2>/dev/null | grep -q -i "log in\|session\|login\|captcha"; then
    echo "$(date): WARNING - LinkedIn watcher may have authentication issues" >> $LOG_FILE
    echo "$(date): LinkedIn log snippet:" >> $LOG_FILE
    pm2 logs linkedin-watcher --lines 5 2>/dev/null >> $LOG_FILE
fi

# Check if browser processes are running for WhatsApp and LinkedIn
WHATSAPP_CHROME=$(pgrep -f "whatsapp_session" | wc -l)
LINKEDIN_CHROME=$(pgrep -f "linkedin_session" | wc -l)

if [ "$WHATSAPP_CHROME" -eq 0 ]; then
    echo "$(date): WARNING - No Chrome process found for WhatsApp watcher" >> $LOG_FILE
fi

if [ "$LINKEDIN_CHROME" -eq 0 ]; then
    echo "$(date): WARNING - No Chrome process found for LinkedIn watcher" >> $LOG_FILE
fi

echo "$(date): Authentication check complete" >> $LOG_FILE