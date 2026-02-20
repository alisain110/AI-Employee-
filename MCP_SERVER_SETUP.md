# MCP Server Setup Guide

This document provides instructions for setting up and running the MCP (Model Context Protocol) server.

## Overview

The MCP server is a FastAPI-based service that handles external actions for the AI Employee, such as sending emails. It provides a secure interface that the AI agent can call to perform actions that require external authentication or security considerations.

## Prerequisites

- Python 3.8+
- pip package manager

## Installation

1. Install the required packages:
   ```bash
   pip install -r mcp_server/requirements.txt
   ```

2. Create your environment file:
   ```bash
   cp mcp_server/.env.example .env
   ```
   Then edit `.env` to set your configuration values.

## Configuration

### Environment Variables

- `MCP_API_KEY`: Secret key for authenticating requests to the MCP server
- `MCP_SERVER_URL`: URL where the MCP server is running (default: http://localhost:8001)
- `SMTP_SERVER`: SMTP server address (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP server port (default: 587)
- `SMTP_USERNAME`: Your email address for SMTP authentication
- `SMTP_PASSWORD`: Your app password for SMTP authentication

### Email Provider Setup

#### Gmail
1. Enable 2-factor authentication on your Google account
2. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Generate a password for "Mail"
3. Use the App Password as your SMTP_PASSWORD

#### Other Providers
- **Outlook/Hotmail**: `SMTP_SERVER=smtp-mail.outlook.com`
- **Yahoo**: `SMTP_SERVER=smtp.mail.yahoo.com`
- Other providers require similar app-specific password setup

## Running the Server

### Method 1: Direct Python
```bash
cd mcp_server
python run_server.py
```

### Method 2: Using uvicorn directly
```bash
cd mcp_server
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Method 3: Using the main start script
```bash
python start_mcp_server.py
```

The server will be available at `http://localhost:8001`

## API Endpoints

### Health Check
- **GET** `/health`
- Returns server health status

### Send Email
- **POST** `/send_email`
- Headers: `Authorization: Bearer YOUR_API_KEY`
- Body:
  ```json
  {
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "Plain text body",
    "html_body": "<p>HTML body (optional)</p>"
  }
  ```

### Execute Generic Action
- **POST** `/execute_action`
- Headers: `Authorization: Bearer YOUR_API_KEY`
- Body:
  ```json
  {
    "action_type": "action_name",
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    }
  }
  ```

## Security

- All endpoints require Bearer token authentication
- API key should be set in environment variables
- Server logs all requests for audit purposes
- Use HTTPS in production environments

## Using with AI Agent

The AI agent uses the following skills to communicate with the MCP server:

1. `send_email_skill(to, subject, body, html_body)` - Send an email
2. `execute_action_skill(action_type, parameters)` - Execute a generic action
3. `mcp_server_health_check()` - Check server health

## Testing the Server

You can test the server manually using curl:

```bash
# Health check
curl -H "Authorization: Bearer your-api-key" http://localhost:8001/health

# Send test email (replace with actual values)
curl -X POST http://localhost:8001/send_email \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email"
  }'
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Make sure no other process is running on port 8001
2. **Authentication failed**: Verify your API key is correct
3. **SMTP connection issues**: Check your email provider settings and app password
4. **Server not responding**: Check the server logs in the `logs/` directory

### Logs

Server logs are written to:
- `mcp_server/logs/mcp_server.log`
- This contains detailed information about requests and any errors

## Production Deployment

For production use:

1. Use a strong, unique API key
2. Deploy behind a reverse proxy with SSL
3. Use environment-specific configuration
4. Implement proper monitoring
5. Set up log rotation
6. Use a production WSGI server like Gunicorn instead of uvicorn's development server