# AI Employee Vault - Ubuntu 24/7 Deployment Commands

## Complete Step-by-Step Setup

### 1. System Prerequisites Installation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python, Git, and Node.js
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install Node.js LTS
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Install Chrome Browser for Selenium
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

# Install additional system dependencies
sudo apt install -y build-essential
```

### 2. Project Setup
```bash
# Create project directory and clone repository
cd /home/ubuntu
git clone https://github.com/your-username/ai_employee_vault.git
cd ai_employee_vault

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify dependencies installed
pip list | grep -E "(anthropic|fastapi|selenium|google|langchain)"
```

### 3. Environment Configuration
```bash
# Create .env file with your API keys
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_anthropic_api_key_here
SOCIAL_MCP_API_KEY=your_social_mcp_api_key_here
EOF

# Set secure permissions for .env file
chmod 600 .env
```

### 4. PM2 Process Manager Setup
```bash
# Install PM2 globally
npm install -g pm2

# Create necessary directories
mkdir -p logs pids Plans Inbox Needs_Action Done Pending_Approval Approved Rejected Briefings Logs
mkdir -p gmail_session whatsapp_session linkedin_session

# Setup PM2 to start on system boot
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Install PM2 log rotation
pm2 install pm2-logrotate
```

### 5. Service Startup
```bash
# Start all services using PM2
pm2 start ecosystem.config.js

# Save PM2 configuration to persist across reboots
pm2 save

# Verify all services are running
pm2 status
```

### 6. Authentication Setup (One-time per service)
```bash
# For Gmail watcher - setup OAuth credentials:
# 1. Create Google Cloud project and enable Gmail API
# 2. Download credentials.json and place in project root
# 3. Run once to authenticate:
# python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('gmail_watcher_skill', action='start')"

# For WhatsApp watcher - manual QR scan:
# 1. Run once to start:
# python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('whatsapp_watcher_skill', action='start')"
# 2. Scan QR code that appears in Chrome window

# For LinkedIn watcher - manual login:
# 1. Run once to start:
# python -c "from core.agent import AIAgent; agent = AIAgent(); agent.run('linkedin_watcher_skill', action='start')"
# 2. Login to LinkedIn in Chrome window that appears
```

### 7. Health Monitoring Setup
```bash
# Add health monitoring to crontab
crontab -l 2>/dev/null | grep -v "health_check.sh\|auth_monitor.sh" | crontab -
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/ubuntu/ai_employee_vault/health_check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * /home/ubuntu/ai_employee_vault/auth_monitor.sh") | crontab -

# Verify cron jobs are added
crontab -l
```

## Daily Operation Commands

### Check System Status
```bash
# View all service statuses
pm2 status

# View logs for all services
pm2 logs

# View logs for specific service
pm2 logs ai-orchestrator --lines 50
pm2 logs gmail-watcher --lines 50
pm2 logs whatsapp-watcher --lines 50
pm2 logs linkedin-watcher --lines 50

# Monitor system resources
pm2 monit

# Get detailed info about a specific service
pm2 show ai-orchestrator
```

### Service Management
```bash
# Restart all services
pm2 restart all

# Reload all services gracefully
pm2 reload all

# Stop all services
pm2 stop all

# Start all services again
pm2 start all

# Restart a specific service
pm2 restart ai-orchestrator
pm2 restart gmail-watcher
pm2 restart whatsapp-watcher
pm2 restart linkedin-watcher
```

### Update the System
```bash
# Update application code
cd /home/ubuntu/ai_employee_vault
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart all

# Update system packages
sudo apt update && sudo apt upgrade -y
```

### System Monitoring
```bash
# Check overall system health
pm2 jlist | grep -c '"pm2_env":\{.*"status":"online"'

# Check for errors in logs
pm2 logs --lines 100 | grep -i error

# Check system resources
htop
df -h
free -h

# Check running Chrome processes (for WhatsApp/LinkedIn watchers)
ps aux | grep chrome
```

## Service Descriptions

1. **ai-orchestrator**: Monitors file system (Inbox, Needs_Action, etc.) and processes tasks
2. **gmail-watcher**: Monitors Gmail for new emails and processes through Claude reasoning
3. **whatsapp-watcher**: Monitors WhatsApp Web for new messages and processes through Claude reasoning
4. **linkedin-watcher**: Monitors LinkedIn for notifications/messages and processes through Claude reasoning

## Troubleshooting Commands

### If a service crashes:
```bash
# Check which service crashed
pm2 status

# View logs to identify issue
pm2 logs <service-name> --lines 100

# Restart the crashed service
pm2 restart <service-name>
```

### If authentication issues occur:
```bash
# Stop the affected service
pm2 stop gmail-watcher  # or whatsapp-watcher or linkedin-watcher

# Clear session if needed (for browser-based services)
rm -rf whatsapp_session/
rm -rf linkedin_session/

# Start the service again and re-authenticate if needed
pm2 start <service-name>

# For Gmail, check credentials
ls -la credentials.json token.json  # Should exist for Gmail
```

### View system statistics:
```bash
# Count files in each directory
find Inbox/ -type f | wc -l
find Needs_Action/ -type f | wc -l
find Done/ -type f | wc -l
find Plans/ -name "*.md" | wc -l
```

## Verification Commands

Run these to confirm 24/7 operation is working:

```bash
# 1. Check if all 4 services are running
echo "Running services: $(pm2 jlist | grep -c '"pm2_env":\{.*"status":"online"') of 4"

# 2. Check for recent errors
echo "Recent errors: $(pm2 logs --lines 50 | grep -c -i error)"

# 3. Check disk usage
df -h | grep -E 'Filesystem|/$'

# 4. Check memory usage
free -h

# 5. Check if Chrome processes are running (for WhatsApp/LinkedIn)
echo "Chrome processes: $(ps aux | grep -c chrome)"

# 6. Check cron jobs
crontab -l | grep -E "(health|auth)"
```

## Expected Output for Healthy System:
- All 4 services showing as "online" in PM2 status
- No recent errors in logs
- Adequate disk space (>20% free)
- Memory usage under 85%
- Chrome processes running for browser-based watchers
- Cron jobs scheduled for health monitoring

The system is now ready for 24/7 operation with automatic restart on crashes, system boot startup, and comprehensive health monitoring!