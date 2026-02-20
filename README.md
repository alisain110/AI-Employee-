# AI Employee Vault - Complete Personal AI Employee System

A comprehensive AI employee system that automates business and personal tasks using Claude AI, with monitoring, scheduling, and human approval workflows.

## Features

- **Intelligent Task Processing**: Uses Claude 3.5 Sonnet for complex reasoning and planning
- **Multi-Channel Monitoring**: Gmail, WhatsApp, and LinkedIn watchers
- **Automated Actions**: Email sending via MCP server
- **Social Media Management**: LinkedIn auto-posting with approval
- **Human-in-the-Loop**: Approval system for sensitive actions
- **Scheduling**: Automated daily tasks and monitoring
- **Secure Architecture**: Isolated external actions through MCP server

## Prerequisites

- Python 3.8+
- Chrome browser (for LinkedIn/WhatsApp automation)
- Anthropic API key

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AI_Employee_Vault
```

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate    # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Setup Instructions

### 1. Anthropic API Key
1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Add to `.env` as `ANTHROPIC_API_KEY`

### 2. MCP Server Configuration
1. The system will start an MCP server on port 8001
2. Set `MCP_API_KEY` in `.env` for authentication

### 3. Gmail Watcher Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials and save as `credentials.json`
6. The first run will prompt for OAuth authentication

### 4. LinkedIn Setup
1. Go to [LinkedIn Developer Portal](https://www.linkedin.com/developers/)
2. Create an app and get Client ID/Secret
3. Enable UGC Posts API
4. Set required scopes: `w_member_social`
5. Add to `.env`

### 5. SMTP Configuration (for Email Actions)
- For Gmail: Enable 2FA and create an App Password
- For other providers: Configure SMTP settings

## Usage

### Running the Complete System
```bash
python main_runner.py
```

This starts:
- MCP server on port 8001
- All watcher services
- Task scheduler with automated jobs
- AI agent with all skills loaded

### Running Components Separately

#### MCP Server Only
```bash
cd mcp_server
python run_server.py
# or
uvicorn main:app --host 0.0.0.0 --port 8001
```

#### Direct Agent Usage
```python
from core.agent import AIAgent

agent = AIAgent()
result = agent.run("claude_reasoning_loop",
                   task_description="Create marketing plan",
                   context="For a SaaS product")
```

### Approval System Modes

#### Console Mode (Default)
```bash
APPROVAL_MODE=console python main_runner.py
```
Prompts for approval interactively.

#### Production Mode
```bash
APPROVAL_MODE=production python main_runner.py
```
Uses file-based approval system:
- Requests appear in `Pending_Approval/` folder
- Move to `Approved/` to allow execution
- Move to `Rejected/` to deny execution

## Scheduled Tasks

The system automatically schedules:

- **Daily Business Plan**: 8:00 AM - Creates daily business plan and sales strategy
- **Daily LinkedIn Post**: 9:00 AM - Creates and posts LinkedIn content (with approval)
- **Watchers**: Run continuously, checking every 5 minutes for:
  - Gmail: New emails
  - WhatsApp: New messages
  - LinkedIn: Notifications and messages

## Agent Skills

All functionality is available through these skills:

### Core Skills
- `claude_reasoning_loop`: Generate comprehensive plans with Claude
- `linkedin_auto_post`: Create and post LinkedIn content (requires approval)
- `send_email_skill`: Send emails via MCP server (requires approval)
- `execute_action_skill`: Execute generic actions (requires approval)

### Watcher Skills
- `gmail_watcher_skill`: Start/stop Gmail monitoring
- `whatsapp_watcher_skill`: Start/stop WhatsApp monitoring
- `linkedin_watcher_skill`: Start/stop LinkedIn monitoring

### MCP Skills
- `mcp_server_health_check`: Check MCP server status

## Security

- All external actions go through MCP server with authentication
- Human approval required for sensitive operations
- API keys stored securely in environment variables
- Session persistence for browser-based watchers

## Folder Structure

```
AI_Employee_Vault/
├── skills/                 # Agent skills
├── core/                   # Core agent functionality
├── config/                 # Business profile
├── plans/                  # Generated plans
├── logs/                   # System logs
├── mcp_server/            # MCP server code
├── Pending_Approval/      # Approval requests
├── Approved/              # Approved requests
├── Rejected/              # Rejected requests
├── utilities/             # Utility functions
└── examples/              # Usage examples
```

## Configuration

### Approval System
- Console mode: Interactive approval prompts
- Production mode: File-based approval workflow

### Scheduling
- Daily tasks scheduled via APScheduler
- Alternative cron examples provided

## Troubleshooting

### Common Issues

1. **Chrome/WhatsApp Login Required**: First run needs manual login
2. **API Keys**: Verify all required keys in `.env`
3. **Port Conflicts**: Ensure port 8001 is available
4. **Permissions**: Check file permissions for log/approval folders

### Logs
- System logs: `logs/` directory
- MCP server logs: `mcp_server/logs/`
- Watcher logs: Included in main logs

## Production Deployment

1. Set `APPROVAL_MODE=production` in environment
2. Configure reverse proxy for MCP server (optional)
3. Set up process monitoring
4. Implement log rotation
5. Use strong API keys

## Windows vs Linux

### Windows
- Use `venv\Scripts\activate` for virtual environment
- Environment variables: `set VAR_NAME=value`
- Paths: Use forward slashes `/` or raw strings `r"path"`

### Linux/Mac
- Use `source venv/bin/activate` for virtual environment
- Environment variables: `export VAR_NAME=value`
- Cron jobs can be used as alternative to APScheduler

## Environment Setup

### Windows
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env with your values
python main_runner.py
```

### Linux/Mac
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
python main_runner.py
```

## MCP Server Endpoints

- `GET /health`: Server health check
- `POST /send_email`: Send email (requires auth)
- `POST /execute_action`: Execute generic action (requires auth)

## Approval Workflow

1. Sensitive action requested
2. Approval request created (console prompt or file)
3. Human reviews and approves/rejects
4. Action executes (if approved) or cancels (if rejected)
5. Results logged for audit trail