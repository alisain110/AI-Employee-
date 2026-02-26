#!/bin/bash
PROJECT_DIR="/home/ubuntu/ai_employee_vault"
LOG_FILE="$PROJECT_DIR/logs/health_check.log"

echo "$(date): Checking AI Employee Vault health..." >> $LOG_FILE

# Check PM2 status
PM2_STATUS=$(pm2 jlist | grep -c '"status":"online"')
if [ "$PM2_STATUS" -eq 4 ]; then
    echo "$(date): All 4 services are running" >> $LOG_FILE
else
    echo "$(date): WARNING - Only $PM2_STATUS of 4 services are running" >> $LOG_FILE
    pm2 status >> $LOG_FILE
fi

# Check for recent errors in logs
ERRORS_FOUND=$(pm2 logs --lines 20 2>/dev/null | grep -c -i -E "(error|exception|traceback|failed)")
if [ "$ERRORS_FOUND" -gt 0 ]; then
    echo "$(date): WARNING - $ERRORS_FOUND errors found in recent logs" >> $LOG_FILE
    pm2 logs --lines 20 2>/dev/null | grep -i -E "(error|exception|traceback|failed)" >> $LOG_FILE
fi

# Check authentication status
AUTH_ERRORS=$(pm2 logs --lines 20 2>/dev/null | grep -c -i -E "(login|auth|session|qr|captcha|credentials)")
if [ "$AUTH_ERRORS" -gt 0 ]; then
    echo "$(date): WARNING - $AUTH_ERRORS authentication-related issues found in recent logs" >> $LOG_FILE
    pm2 logs --lines 20 2>/dev/null | grep -i -E "(login|auth|session|qr|captcha|credentials)" >> $LOG_FILE
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): WARNING - Disk usage is ${DISK_USAGE}%" >> $LOG_FILE
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEMORY_USAGE" -gt 85 ]; then
    echo "$(date): WARNING - Memory usage is ${MEMORY_USAGE}%" >> $LOG_FILE
fi

echo "$(date): Health check complete" >> $LOG_FILE