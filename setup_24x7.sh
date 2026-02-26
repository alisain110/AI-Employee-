#!/bin/bash
# Ubuntu 24/7 Setup Script for AI Employee Vault
# This script prepares the system for 24/7 operation

set -e  # Exit on any error

echo "Setting up AI Employee Vault for 24/7 operation on Ubuntu..."

# Create required directories
echo "Creating required directories..."
mkdir -p logs pids Plans Inbox Needs_Action Done Pending_Approval Approved Rejected Briefings Logs
mkdir -p whatsapp_session linkedin_session

# Set proper permissions
echo "Setting proper permissions..."
chmod +x *.sh *.py
chmod 600 .env.example 2>/dev/null || echo ".env file not present, that's OK"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Install PM2
echo "Installing PM2 process manager..."
npm install -g pm2

# Setup PM2 to start on boot
echo "Setting up PM2 startup..."
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Create log rotation configuration for PM2
echo "Setting up log rotation..."
pm2 install pm2-logrotate

# Setup and start the services
echo "Starting AI Employee services..."
pm2 start ecosystem.config.js

# Save the PM2 configuration
echo "Saving PM2 configuration..."
pm2 save

# Setup health check cron job (every 10 minutes)
echo "Setting up health monitoring..."
crontab -l 2>/dev/null | grep -v "health_check.sh\|auth_monitor.sh" | crontab -
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/ubuntu/ai_employee_vault/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * /home/ubuntu/ai_employee_vault/auth_monitor.sh") | crontab -

echo "AI Employee Vault is now configured for 24/7 operation!"
echo "Services status:"
pm2 status

echo ""
echo "To monitor the system, use:"
echo "  pm2 status          # View service status"
echo "  pm2 logs            # View all logs"
echo "  pm2 logs <app>      # View specific app logs"
echo "  pm2 monit           # Monitor resources"
echo ""
echo "System will automatically restart on boot and recover from crashes."