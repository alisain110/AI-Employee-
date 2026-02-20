# Odoo Community 19 Setup with MCP Separation

This setup provides a complete deployment of Odoo Community 19 with Model Context Protocol (MCP) separation for cloud and local operations.

## Architecture Overview

The system implements a "cloud-draft + local-execute" pattern:
- **Cloud (odoo_draft_mcp)**: Draft creation, read operations, approval requests
- **Local (odoo_execute_mcp)**: Final posting, execution of sensitive operations

## Components

### 1. odoo_setup.sh
Shell script to install Odoo 19 Community on Ubuntu VM with all dependencies:
- PostgreSQL database
- Wkhtmltopdf for PDF generation
- Odoo source installation
- Nginx reverse proxy with SSL support

### 2. nginx_odoo_config.txt
Nginx configuration file for reverse proxy with SSL termination using Let's Encrypt certificates.

### 3. odoo_draft_mcp.py
Cloud-only MCP server that handles:
- Create draft invoice
- Create draft customer
- Read reports and queries

### 4. odoo_execute_mcp.py
Local-only MCP server that handles:
- Post/confirm invoice
- Register payment
- Confirm customer

## Setup Instructions

### 1. Install Odoo with the setup script:

```bash
chmod +x odoo_setup.sh
./odoo_setup.sh
```

### 2. Configure Odoo and obtain SSL certificate:

1. Point your domain's DNS to the server
2. Edit the Nginx config:
   ```bash
   sudo nano /etc/nginx/sites-available/odoo
   ```
   Replace "your_domain.com" with your actual domain
3. Enable the site and reload Nginx:
   ```bash
   sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```
4. Obtain SSL certificate:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

### 3. Set up Odoo user and API key:
1. Access your Odoo instance at https://yourdomain.com
2. Create an API key for external access
3. Configure the .env file with your credentials

### 4. Install Python dependencies:
```bash
pip install -r odoo_mcp_requirements.txt
```

### 5. Start the MCP servers:
```bash
python start_odoo_mcp_servers.py
```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Odoo Draft MCP (Cloud)
ODOO_URL=https://yourdomain.com
ODOO_DB=your_odoo_database_name
ODOO_API_KEY=your_odoo_api_key
ODOO_USER_ID=2  # Usually admin ID
ODOO_DRAFT_API_KEY=your_draft_mcp_api_key

# Odoo Execute MCP (Local)
ODOO_LOCAL_URL=http://localhost:8069
ODOO_EXECUTE_API_KEY=your_execute_mcp_api_key
```

## Ports

- Odoo Web Interface: 443 (HTTPS) / 80 (HTTP redirect)
- Odoo Draft MCP: 8001 (cloud operations)
- Odoo Execute MCP: 8002 (local operations)

## Security Features

1. **Separation of Duties**: Cloud for drafting, local for execution
2. **API Key Authentication**: All MCP endpoints require authentication
3. **Approval Workflow**: Sensitive operations require local approval
4. **Audit Logging**: All actions are logged for compliance
5. **HTTPS Protection**: All communications encrypted

## Usage Examples

### Creating a Draft Invoice (Cloud)
```bash
curl -X POST http://your_server:8001/create_invoice \
  -H "Authorization: Bearer your_draft_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "partner_id": 1,
    "products_list": [
      {
        "product_id": 1,
        "quantity": 2,
        "price": 50.00
      }
    ],
    "amounts": {
      "subtotal": 100.00,
      "tax": 10.00,
      "total": 110.00
    }
  }'
```

### Posting an Invoice (Local)
```bash
curl -X POST http://localhost:8002/post_invoice \
  -H "Authorization: Bearer your_execute_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_id": 1
  }'
```

## Health Check

Check the status of your MCP servers:
- Draft MCP: `GET http://your_server:8001/health`
- Execute MCP: `GET http://localhost:8002/health`