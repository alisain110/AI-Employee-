# Watcher Skills Setup Guide

This document provides setup instructions for the three watcher skills: Gmail, WhatsApp, and LinkedIn.

## Prerequisites

Make sure you have installed all dependencies:
```bash
pip install -r requirements.txt
```

## Gmail Watcher Setup

### 1. Enable Gmail API
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in your project root

### 2. Scopes Required
- `https://www.googleapis.com/auth/gmail.readonly`

### 3. Usage
```python
from core.agent import AIAgent
agent = AIAgent()

# Start watching
result = agent.run("gmail_watcher_skill", action="start")
print(result)

# Stop watching
result = agent.run("gmail_watcher_skill", action="stop")
print(result)
```

## WhatsApp Watcher Setup

### 1. Requirements
- Chrome browser installed
- WhatsApp account

### 2. Session Persistence
The watcher uses session persistence to avoid having to scan QR code every time:
- Sessions are stored in `./whatsapp_session/` by default
- After first login, the session will persist between runs

### 3. Usage
```python
from core.agent import AIAgent
agent = AIAgent()

# Start watching with custom session folder
result = agent.run("whatsapp_watcher_skill", action="start", session_folder="./my_whatsapp_session")
print(result)

# Stop watching
result = agent.run("whatsapp_watcher_skill", action="stop")
print(result)
```

**Note**: On first run, you'll need to manually scan the QR code in the Chrome window that opens.

## LinkedIn Watcher Setup

### 1. Requirements
- Chrome browser installed
- LinkedIn account

### 2. Session Persistence
Similar to WhatsApp, LinkedIn sessions are persisted:
- Sessions are stored in `./linkedin_session/` by default

### 3. Usage
```python
from core.agent import AIAgent
agent = AIAgent()

# Start watching with custom session folder
result = agent.run("linkedin_watcher_skill", action="start", session_folder="./my_linkedin_session")
print(result)

# Stop watching
result = agent.run("linkedin_watcher_skill", action="stop")
print(result)
```

**Note**: On first run, you'll need to manually log in to LinkedIn in the Chrome window that opens.

## Common Issues and Troubleshooting

### Selenium-related Issues
- Make sure Chrome browser is installed
- If you get driver issues, install ChromeDriver separately or update your Chrome browser

### API Quotas
- Gmail API has quotas, so the 5-minute polling interval helps avoid hitting limits
- If you encounter quota errors, increase the polling interval

### Session Files
- Sessions are stored locally and contain authentication data
- Keep session folders secure as they contain login information
- To force re-login, delete the session folder

## How Watchers Work

Each watcher:
1. Runs in a background thread
2. Polls for new activity every 5 minutes (or uses push notifications where available)
3. When new activity is detected:
   - Logs the activity
   - Automatically calls `claude_reasoning_loop`
   - Summarizes the message/notification
   - Creates an action plan
   - Saves the plan to the `plans/` directory

## Starting All Watchers

```python
from core.agent import AIAgent

agent = AIAgent()

# Start all watchers
agent.run("gmail_watcher_skill", action="start")
agent.run("whatsapp_watcher_skill", action="start")
agent.run("linkedin_watcher_skill", action="start")

print("All watchers started successfully!")
print("They will run in background threads until stopped.")
```

## Stopping All Watchers

```python
from core.agent import AIAgent

agent = AIAgent()

# Stop all watchers
agent.run("gmail_watcher_skill", action="stop")
agent.run("whatsapp_watcher_skill", action="stop")
agent.run("linkedin_watcher_skill", action="stop")

print("All watchers stopped successfully!")
```

## Environment Variables

Create a `.env` file for your API keys:
```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Security Considerations

- Store API keys securely in environment variables
- Keep session folders secure as they contain authentication data
- Regularly update your credentials
- Monitor API usage to stay within quotas