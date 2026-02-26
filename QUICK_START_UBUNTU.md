# AI Employee Vault - Quick Start on Ubuntu

## Essential 24/7 Deployment Commands

### Initial Setup (Run Once):
```bash
# System updates and prerequisites
sudo apt update && sudo apt install -y python3 python3-pip git curl wget nodejs google-chrome-stable

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

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# PM2 setup
npm install -g pm2
pm2 startup
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Create directories and start services
mkdir -p logs pids Plans Inbox Needs_Action Done Pending_Approval Approved Rejected Briefings Logs
mkdir -p whatsapp_session linkedin_session
pm2 start ecosystem.config.js
pm2 save

# Setup monitoring
crontab -l 2>/dev/null | grep -v "health_check.sh" | crontab -
(crontab -l 2>/dev/null; echo "*/10 * * * * /home/ubuntu/ai_employee_vault/health_check.sh") | crontab -
```

### Daily Management Commands:
```bash
# Check system status
pm2 status

# View logs
pm2 logs

# Restart all services
pm2 restart all

# Monitor resources
pm2 monit

# Update system
cd /home/ubuntu/ai_employee_vault
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart all
```

### Service Status Check:
```bash
# Should show 4 services running
pm2 status

# Quick health check
pm2 jlist | grep -c '"status":"online"'
```

The system will now run 24/7 with automatic restart on crashes and system reboots!