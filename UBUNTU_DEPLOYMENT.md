# AI Employee Vault - Ubuntu 24/7 Deployment Guide

This document provides step-by-step instructions to deploy the AI Employee Vault project on a Linux cloud VM (Ubuntu) for 24/7 operation.

## 1. System Prerequisites

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Python and Essential Tools
```bash
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

### Install Node.js and npm (required for PM2)
```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

### Install Chrome Browser (for Selenium)
```bash
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-browser.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-browser.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable
```

### Install ChromeDriver
```bash
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

## 2. Project Setup

### Clone the Repository
```bash
cd /home/ubuntu
git clone https://github.com/your-username/ai_employee_vault.git
cd ai_employee_vault
```

### Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Install PM2 (Process Manager)
```bash
npm install -g pm2
```

### Create Required Directories
```bash
mkdir -p logs pids
```

## 3. Environment Configuration

### Copy and Edit Environment File
```bash
cp .env.example .env
nano .env  # Update with your actual API keys and credentials
```

### Set up Required Credentials

For Gmail watcher, you'll need to:
1. Create Google Cloud project and enable Gmail API
2. Download `credentials.json` and place it in the project root
3. Run the authentication flow once to generate `token.json`
4. The Gmail API uses OAuth2 tokens that auto-refresh, ensuring long-term operation

For WhatsApp and LinkedIn watchers, you'll need to:
1. Run the authentication process manually once to set up persistent browser sessions
2. The sessions will be stored in `./whatsapp_session` and `./linkedin_session` directories
3. These browser-based sessions persist between runs using Chrome user data directories
4. Note: Browser-based sessions may occasionally require re-authentication due to service updates

## 4. Configure PM2

### Install PM2 Startup Script
```bash
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu
```

### Start All Services with PM2
```bash
pm2 start ecosystem.config.js
```

### Save PM2 Configuration
```bash
pm2 save
```

### Check Status
```bash
pm2 status
pm2 logs  # View all logs
pm2 logs ai-orchestrator  # View specific service logs
```

## 5. Deployment Commands

### Complete Deployment Script
```bash
# Install system dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git curl wget
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Clone and setup project
cd /home/ubuntu
git clone https://github.com/your-username/ai_employee_vault.git
cd ai_employee_vault

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install PM2
npm install -g pm2
mkdir -p logs pids

# Setup PM2
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Start services
pm2 start ecosystem.config.js
pm2 save
```

## 6. Health Check Instructions

### Basic Health Checks
```bash
# Check if all services are running
pm2 status

# Check logs for errors
pm2 logs --lines 50 | grep -i error

# Check specific service logs
pm2 logs ai-orchestrator --lines 50
pm2 logs gmail-watcher --lines 50
pm2 logs whatsapp-watcher --lines 50
pm2 logs linkedin-watcher --lines 50
```

### System Resource Monitoring
```bash
# Check system resources
htop

# Check disk usage
df -h

# Check memory usage
free -h

# Check disk usage of project
du -sh /home/ubuntu/ai_employee_vault
```

### Service-Specific Checks

#### Check if orchestrator is processing files
```bash
tail -f /home/ubuntu/ai_employee_vault/logs/orchestrator_combined.log
```

#### Check if watchers are running
```bash
ps aux | grep python | grep -E "(orchestrator|watcher)"
```

#### Check for any crashed processes
```bash
pm2 jlist | grep -E '"pm2_env":\{.*"status":"errored"'
```

### Automated Health Check Script
Create a health check script at `/home/ubuntu/health_check.sh`:
```bash
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

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): WARNING - Disk usage is ${DISK_USAGE}%" >> $LOG_FILE
fi

echo "$(date): Health check complete" >> $LOG_FILE
```

Make it executable and add to crontab:
```bash
chmod +x /home/ubuntu/health_check.sh

# Add to crontab to run every 10 minutes
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/ubuntu/health_check.sh") | crontab -
```

## 7. Maintenance Commands

### Restart Services
```bash
# Restart all services
pm2 restart all

# Restart specific service
pm2 restart ai-orchestrator

# Reload all (graceful restart)
pm2 reload all
```

### Update Application
```bash
cd /home/ubuntu/ai_employee_vault
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart all
```

### Monitor Resource Usage
```bash
# Monitor in real-time
pm2 monit

# Check memory usage per process
pm2 top
```

### Log Management
```bash
# Rotate logs
pm2 logrotate -u

# Clear logs
pm2 flush
```

## 8. Troubleshooting

### If a service crashes:
1. Check the logs: `pm2 logs <service-name>`
2. Restart the service: `pm2 restart <service-name>`
3. Check system resources: `htop`

### If watchers stop responding:
1. Check if Chrome processes are running: `ps aux | grep chrome`
2. Kill any zombie Chrome processes: `pkill -f chrome`
3. Restart the watcher: `pm2 restart <watcher-name>`

### If orchestrator stops processing files:
1. Check if files are accumulating in `Needs_Action` directory
2. Check orchestrator logs for errors
3. Verify file permissions in project directories

### Common Issues and Solutions:
- **Chrome crashes**: Increase VM memory or reduce number of browser-based watchers
- **API rate limits**: Implement proper delays in watcher code
- **Memory leaks**: Monitor with `pm2 monit` and set up alerts
- **Authentication issues**: Re-authenticate services manually when needed

## 8. System Architecture: Orchestrator and Watchers Interaction

### Component Overview:

#### Orchestrator:
- Monitors file system directories (`Inbox`, `Needs_Action`, `Approved`, etc.)
- Processes tasks based on file content and system rules
- Coordinates with other system components
- Manages task lifecycle from creation to completion

#### Watchers:
- **Gmail Watcher**: Monitors Gmail for new emails using Google API
- **WhatsApp Watcher**: Monitors WhatsApp Web for new messages using browser automation
- **LinkedIn Watcher**: Monitors LinkedIn for notifications and messages using browser automation

### How Orchestrator and Watchers Work Together:

1. **Watchers detect activity** (new emails/messages/notifications)
2. **Watchers process activity** through Claude reasoning loop
3. **Watchers generate plans/decisions** and save to `plans/` directory
4. **Orchestrator may monitor** the results of watcher actions
5. **Orchestrator can coordinate** with watchers for complex workflows

### Claude Reasoning Loop Integration:
All watchers use the `claude_reasoning_loop` skill to:
- Analyze incoming messages/notifications
- Generate appropriate responses or action plans
- Create structured plans in Markdown format
- Route tasks through approval processes when needed

## 9. Authentication and Session Management

### Authentication Mechanisms

#### Gmail Watcher Authentication:
- Uses Google OAuth2 with automatic token refresh
- Requires initial setup with `credentials.json` file
- Tokens are automatically refreshed when they expire
- Long-term operation is supported without manual intervention

#### WhatsApp Watcher Authentication:
- Uses persistent browser sessions via Chrome user data directory
- Requires initial manual authentication by scanning QR code
- Session is stored in `./whatsapp_session` directory
- May require occasional re-authentication (every few weeks/months depending on WhatsApp Web policies)

#### LinkedIn Watcher Authentication:
- Uses persistent browser sessions via Chrome user data directory
- Requires initial manual authentication by logging in
- Session is stored in `./linkedin_session` directory
- May require occasional re-authentication (every few weeks/months depending on LinkedIn policies)

### Authentication Maintenance:
For browser-based watchers (WhatsApp/LinkedIn), implement the following maintenance procedures:

1. **Monitor authentication status**:
```bash
# Check for common authentication errors in logs
pm2 logs | grep -i -E "login|auth|session|qr|captcha"
```

2. **Refresh authentication when needed**:
```bash
# Stop the affected service
pm2 stop whatsapp-watcher  # or linkedin-watcher

# Clear and reset session (optional)
rm -rf whatsapp_session/  # or linkedin_session/

# Start the service and manually authenticate again
pm2 start whatsapp-watcher
```

3. **Set up alerts for authentication failures**:
Add to your monitoring script to alert when authentication-related errors occur.

## 10. Security Considerations

### Firewall Configuration
```bash
# Only allow necessary ports
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
```

### File Permissions
```bash
# Set appropriate permissions
chmod 600 .env  # Restrict access to environment file
chmod 755 start.sh
```

### Regular Security Updates
```bash
# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```