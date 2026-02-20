# AI Employee Vault - Gold Tier Architecture

## System Architecture Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Watchers      │    │  Orchestrator    │    │   Ralph Loop     │
│                 │    │                  │    │                  │
│ • Gmail         │───▶│ • File Monitor   │───▶│ • Iterative      │
│ • WhatsApp      │    │ • Task Routing   │    │   Processing     │
│ • LinkedIn      │    │ • Mode Detection │    │ • Safety Cuts    │
│ • Social Media  │    │ • MCP Routing    │    │ • State Track.   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌──────────────────┐    ┌──────────────────┐
                    │  MCP Servers     │    │  External APIs   │
                    │                  │    │                  │
                    │ • Odoo MCP       │───▶│ • Odoo ERP       │
                    │ • Social MCP     │    │ • Social Media   │
                    │ • Custom APIs    │    │ • Other Services │
                    └──────────────────┘    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Obsidian Files  │
                    │                  │
                    │ • /Inbox         │
                    │ • /Needs_Action  │
                    │ • /Done          │
                    │ • /Ralph_Logs    │
                    │ • Dashboard.md   │
                    └──────────────────┘
```

## Components Overview

### Watchers
- **Gmail Watcher**: Monitors email for tasks, approvals, and notifications
- **WhatsApp Watcher**: Processes WhatsApp messages for business requests
- **LinkedIn Watcher**: Monitors LinkedIn for connections and messages
- **Social Media Watchers**: Facebook, Instagram, X (Twitter) monitoring

### Orchestrator (orchestrator_gold.py)
- **File Monitoring**: Watches `/Inbox` and `/Needs_Action` directories
- **Mode Detection**: Detects `mode: ralph` in task files
- **Task Routing**: Routes tasks to normal or Ralph mode processing
- **MCP Routing**: Routes tool calls to appropriate MCP services

### Ralph Loop
- **Iterative Processing**: Runs up to 15 iterations for complex tasks
- **Fresh Context**: Provides clean context for each iteration
- **Safety Mechanisms**: Time caps, iteration limits, emergency stops
- **State Management**: Tracks DONE/CONTINUE/FAILED/NEEDS_HUMAN states

### MCP Servers
- **Odoo MCP**: Handles ERP operations (invoices, customers, P&L)
- **Social MCP**: Manages social media posts and analytics
- **Custom MCPs**: Extensible for other business services

### External APIs
- **Odoo ERP**: Business management and accounting system
- **Social Media APIs**: Facebook, Instagram, X/Twitter integration
- **Claude AI**: Reasoning and decision-making engine

### Obsidian Files
- **File-based Workflow**: All communication via markdown files
- **Status Tracking**: `/Inbox`, `/Needs_Action`, `/Done` directories
- **Audit Trail**: `/Ralph_Logs` and comprehensive logging

## Data Flow

### Normal Mode Processing
```
1. New file → /Inbox or /Needs_Action
2. Orchestrator detects file
3. Parse configuration (normal vs ralph mode)
4. Process with Claude (single pass)
5. Execute identified tools/Skills
6. File → /Done
```

### Ralph Mode Processing
```
1. New file → /Needs_Action with "mode: ralph"
2. Orchestrator detects Ralph mode
3. Start iterative loop (max 15 iterations)
4. Each iteration:
   a. Read task + related files
   b. Send to Claude for reasoning
   c. Get thought/tool_calls/next_action
   d. Execute tools
   e. Log step to /Ralph_Logs
   f. Check for DONE/FAILED/NEEDS_HUMAN
   g. Sleep before next iteration
5. Final state → appropriate folder
```

### MCP Data Flow
```
1. Orchestrator calls MCP endpoint
2. MCP server validates API key
3. Process request via business logic
4. Call external APIs if needed
5. Return results to orchestrator
6. Log all MCP calls for audit
```

## Safety Mechanisms

### Ralph Loop Safety
- **Iteration Limit**: Maximum 15 iterations per task
- **Time Cap**: 2-hour maximum processing time
- **Emergency Stop**: `EMERGENCY_STOP_RALPH` file terminates loops
- **State Management**: Proper DONE/FAILED/NEEDS_HUMAN handling
- **Error Recovery**: Retry with exponential backoff

### Security Measures
- **API Key Validation**: All MCP calls require valid keys
- **Approval Workflow**: Sales-related and sensitive actions require approval
- **Audit Logging**: All actions logged in JSON Lines format
- **File Permissions**: Restricted access to system files

### Error Handling
- **Transient Recovery**: Automatic retry on network errors
- **Graceful Degradation**: Fallback mechanisms when services fail
- **Rate Limiting**: Handles Claude API rate limits appropriately
- **Emergency Stops**: Immediate halt capability for safety

### Monitoring
- **Dashboard Updates**: Real-time status tracking
- **Audit Trail**: Comprehensive action logging
- **Performance Metrics**: Processing time and success rates
- **Error Tracking**: Failure pattern identification