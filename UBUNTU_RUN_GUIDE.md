# AI Employee Vault - Ubuntu 24/7 Operation Guide

## Complete Setup Commands

### 1. System Prerequisites
```bash
# Update system and install prerequisites
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Install Chrome Browser
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/google-chrome-browser.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-browser.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

### 2. Project Setup
```bash
# Clone the repository
cd /home/ubuntu
git clone https://github.com/your-username/ai_employee_vault.git
cd ai_employee_vault

# Create virtual environment and install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install PM2
npm install -g pm2
mkdir -p logs pids
```

### 3. PM2 Configuration
```bash
# Setup PM2 to start on boot
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Install pm2-logrotate
pm2 install pm2-logrotate

# Start all services
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Check status
pm2 status
```

### 4. Authentication Setup
```bash
# For Gmail watcher
# 1. Setup Google Cloud project and download credentials.json
# 2. Place credentials.json in project root
# 3. Run once to authenticate: python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('gmail_watcher_skill', action='start')"

# For WhatsApp watcher
# 1. Run once to authenticate: python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('whatsapp_watcher_skill', action='start')"
# 2. Scan the QR code that appears in the Chrome window

# For LinkedIn watcher
# 1. Run once to authenticate: python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('linkedin_watcher_skill', action='start')"
# 2. Login to LinkedIn in the Chrome window that appears
```

### 5. Health Monitoring Setup
```bash
# Add health checks to crontab
crontab -l 2>/dev/null | grep -v "health_check.sh\|auth_monitor.sh" | crontab -
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/ubuntu/ai_employee_vault/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * /home/ubuntu/ai_employee_vault/auth_monitor.sh") | crontab -
```

## Running the System

### Start Services
```bash
# Start all services
pm2 start ecosystem.config.js

# Or start individual services
pm2 start ai-orchestrator
pm2 start gmail-watcher
pm2 start whatsapp-watcher
pm2 start linkedin-watcher
```

### Monitor Services
```bash
# Check status of all services
pm2 status

# View logs of all services
pm2 logs

# View logs of specific service
pm2 logs ai-orchestrator
pm2 logs gmail-watcher
pm2 logs whatsapp-watcher
pm2 logs linkedin-watcher

# Monitor resource usage
pm2 monit

# Get detailed info about a service
pm2 show ai-orchestrator
```

### System Commands
```bash
# Restart all services
pm2 restart all

# Reload all services gracefully
pm2 reload all

# Stop all services
pm2 stop all

# Update the application
cd /home/ubuntu/ai_employee_vault
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart all

# View system health
pm2 jlist  # JSON list of all processes
pm2 info ai-orchestrator  # Detailed info for specific process
```

## Service Descriptions

1. **ai-orchestrator**: Monitors file system directories (Inbox, Needs_Action, etc.) and processes tasks
2. **gmail-watcher**: Monitors Gmail for new emails and processes them through Claude reasoning
3. **whatsapp-watcher**: Monitors WhatsApp Web for new messages and processes them through Claude reasoning
4. **linkedin-watcher**: Monitors LinkedIn for notifications and messages and processes them through Claude reasoning

## 24/7 Operation Features

- **Auto-restart**: All services automatically restart if they crash
- **System boot**: Services start automatically when the system reboots
- **Health monitoring**: Regular checks for service status, disk space, memory usage, and authentication issues
- **Error handling**: Comprehensive error handling and logging
- **Resource management**: Proper memory and CPU usage monitoring
- **Log rotation**: Automatic log rotation to prevent disk space issues

## Troubleshooting

### If a service crashes:
```bash
pm2 restart <service-name>
pm2 logs <service-name> --lines 50
```

### If authentication fails:
```bash
# For browser-based services (WhatsApp/LinkedIn)
pm2 stop <service-name>
# Clear session if needed: rm -rf <service>_session/
pm2 start <service-name>
# Then manually authenticate if needed
```

### View system resources:
```bash
# System monitoring
htop
df -h
free -h

# PM2 monitoring
pm2 monit
```

## Verification Commands

```bash
# Check if all 4 services are running
pm2 jlist | grep -c '"pm2_env":\{.*"status":"online"'

# Check for recent errors
pm2 logs --lines 20 | grep -i error

# Check disk usage
df -h | grep -E 'Filesystem|/dev/'

# Check memory usage
free -h

# Check if Chrome processes are running
ps aux | grep chrome
```

The system is fully configured for 24/7 operation with all necessary components:
- Process management with PM2
- Auto-restart on failures
- System boot startup
- Health monitoring
- Authentication management
- Resource monitoring
- Error handling and logging