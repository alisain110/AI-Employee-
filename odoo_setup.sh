#!/bin/bash
# Odoo 19 Community Setup Script
# This script installs Odoo 19 Community on Ubuntu VM with all necessary dependencies

set -e  # Exit on any error

echo "Starting Odoo 19 Community installation..."

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
echo "Installing PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Create Odoo database user
echo "Creating Odoo database user..."
sudo -u postgres createuser -s odoo

# Install other dependencies
echo "Installing additional dependencies..."
sudo apt install -y python3-pip python3-dev python3-wheel python3-setuptools \
    build-essential libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev libssl-dev \
    libjpeg-dev libpq-dev libpng-dev libfreetype6-dev liblcms2-dev libwebp-dev \
    git wget curl gcc g++ node-less wkhtmltopdf

# Create Odoo user
echo "Creating Odoo system user..."
sudo adduser --system --home=/opt/odoo --group odoo

# Install Odoo from source
echo "Installing Odoo 19 Community from source..."
cd /opt
sudo -u odoo git clone https://github.com/odoo/odoo.git -b 19.0 --depth 1
cd /opt/odoo/odoo

# Install Python dependencies
echo "Installing Python dependencies..."
sudo -u odoo python3 -m venv /opt/odoo/odoo-venv
source /opt/odoo/odoo-venv/bin/activate
pip3 install wheel
pip3 install -r requirements.txt

# Configure Odoo
echo "Creating Odoo configuration..."
sudo -u odoo cp /opt/odoo/odoo/debian/odoo.conf /etc/odoo.conf
sudo chown odoo: /etc/odoo.conf
sudo chmod 640 /etc/odoo.conf

# Create Odoo log directory
sudo -u odoo mkdir -p /var/log/odoo
sudo chown odoo:root /var/log/odoo

# Set up systemd service
echo "Setting up systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/odoo.service
[Unit]
Description=Odoo
Requires=postgresql.service
After=network.target postgresql.service

[Service]
Type=forking
User=odoo
Group=odoo
ExecStart=/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf
KillMode=mixed
TimeoutStopSec=360
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable and start Odoo
sudo systemctl enable odoo
sudo systemctl start odoo

# Install Certbot and Nginx
echo "Installing Certbot and Nginx..."
sudo apt install -y nginx certbot python3-certbot-nginx

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

echo "Odoo 19 Community installation completed successfully!"
echo "Please proceed with the following manual steps:"
echo "1. Configure your domain DNS to point to this server"
echo "2. Create a basic Nginx config for Odoo reverse proxy:"
echo "   sudo nano /etc/nginx/sites-available/odoo"
echo "3. Enable the site:"
echo "   sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/"
echo "4. Test nginx configuration:"
echo "   sudo nginx -t"
echo "5. Reload Nginx:"
echo "   sudo systemctl reload nginx"
echo "6. Run certbot to obtain SSL certificate:"
echo "   sudo certbot --nginx -d yourdomain.com"

echo ""
echo "Basic Nginx config to use (replace with your actual domain):"
echo "
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8069;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Port \$server_port;
        proxy_redirect off;
    }

    location /longpolling {
        proxy_pass http://127.0.0.1:8072;
    }

    location ~* /web/static/ {
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        alias /opt/odoo/addons/19.0/web/static/;
        # or /opt/odoo/odoo/addons/web/static for newer versions
        proxy_pass http://127.0.0.1:8069;
    }
}
"

echo "Installation complete! Please complete the manual configuration steps above to finish setting up HTTPS."