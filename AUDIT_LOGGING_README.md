# Audit Logging System for AI Employee Vault

## Overview

The audit logging system provides comprehensive logging for all MCP calls, Claude responses, watcher events, and system operations. It follows JSON Lines format for easy parsing and analysis.

## Key Features

### 1. Comprehensive Audit Trail
- **MCP Calls**: All Model Context Protocol server interactions
- **Claude Requests**: AI model interactions with prompt/response details
- **Watcher Events**: All watcher activity and triggered events
- **Task Processing**: File operations, task completion, and status changes
- **Error Logging**: System errors with context and severity levels

### 2. Error Recovery Patterns
- **Retry Logic**: Automatic retry on transient errors (429, 500, network issues)
- **Exponential Backoff**: Increasing delays between retry attempts
- **Graceful Fallbacks**: Safe operation when primary services are unavailable
- **Rate Limit Handling**: Sleep and exponential backoff for Claude API rate limits

### 3. Safety and Monitoring
- **Emergency Stops**: Ability to halt operations when needed
- **Session Tracking**: All operations tied to session IDs for correlation
- **Security Logging**: API key validation and access attempts
- **Performance Monitoring**: Call duration and resource usage tracking

## Architecture

### Core Components

#### `audit_logger.py`
- **AuditLogger**: Main logging class with thread-safe operations
- **AuditLogEntry**: Structured data class for audit records
- **AuditActor/AuditAction**: Enumerations for consistent categorization
- **Retry Decorators**: Error recovery utilities

#### Log Format (JSON Lines)
Each log entry is a single JSON object on its own line:
```json
{
  "timestamp": "2026-02-20T07:21:42.457Z",
  "actor": "mcp",
  "action": "mcp_call",
  "success": true,
  "details": { ... },
  "error": null,
  "session_id": "session-123"
}
```

### Integrated Systems

#### Orchestrator (orchestrator_gold.py)
- **MCP Endpoint Calls**: All calls to external services are logged
- **Claude Interactions**: AI model requests and responses
- **Task Processing**: File operations and status changes
- **Ralph Mode**: Iteration-by-iteration logging with context

#### MCP Servers (social_mcp_server.py, odoo_mcp_server.py)
- **Authentication**: API key validation and security events
- **Endpoints**: All incoming requests and outgoing responses
- **Data Operations**: Database interactions and business logic
- **Error Handling**: Service unavailability and failure scenarios

## Usage Examples

### Logging an MCP Call
```python
from audit_logger import get_audit_logger

audit_logger = get_audit_logger()
audit_logger.log_mcp_call(
    service="social_mcp",
    endpoint="facebook_post",
    data={"text": "Hello World", "image_url": "https://..."},
    success=True,
    response={"post_id": "12345"},
    session_id="session-123"
)
```

### Adding Error Recovery to Functions
```python
from audit_logger import retry_on_transient_error

@retry_on_transient_error(max_retries=3, base_delay=1.0)
def call_external_api():
    # Function that may have transient failures
    pass
```

### Graceful Fallbacks
```python
from audit_logger import graceful_fallback

def fallback_function():
    # Fallback implementation
    return "Manual processing completed"

@graceful_fallback(fallback_action=fallback_function)
def primary_function():
    # Primary implementation
    pass
```

## Error Recovery Implementation

### Transient Error Detection
The system automatically detects and retries for:
- HTTP 429 (Rate Limit Exceeded)
- HTTP 500/502/503 (Server errors)
- Network timeouts and connection issues
- Claude API rate limits and quota exceeded

### Retry Strategy
- **Max Retries**: Configurable (default 3)
- **Backoff**: Exponential with jitter to prevent thundering herd
- **Delay Pattern**: base_delay * (2^attempt) + random_jitter

### Fallback Mechanisms
- **Service Unavailability**: If Odoo is down, create manual tasks
- **AI Limits**: Handle Claude rate limits gracefully
- **Network Issues**: Retry with exponential backoff

## Directory Structure
```
Logs/
├── audit_YYYY-MM-DD.log    # Daily audit logs in JSON Lines format
├── orchestrator_gold.log   # Orchestrator logs
├── social_mcp_actions.log  # Social MCP server logs
└── odoo_actions.log        # Odoo MCP server logs
```

## Integration Points

### Orchestrator Integration
- MCP endpoint calls are logged automatically
- Claude interactions include prompt/response lengths
- Ralph mode iterations are tracked with step-by-step details
- File operations and task processing are logged

### MCP Server Integration
- All incoming requests are logged with details
- Authentication attempts (successful and failed) are tracked
- External service calls are monitored
- Health check results are recorded

## Benefits

### Operational Visibility
- Complete audit trail of all system operations
- Performance monitoring and response time tracking
- Error patterns and frequency analysis
- Service availability and reliability metrics

### Security & Compliance
- API key validation and access logging
- Sensitive operations tracking (payments, customer creation)
- Failed authentication attempts monitoring
- Change tracking for financial data

### Reliability
- Automatic error recovery reduces manual intervention
- Graceful degradation when services are unavailable
- Rate limit handling prevents service disruption
- Session tracking aids debugging

### Maintenance
- Structured logs for automated analysis
- Easy parsing with standard JSON Lines tools
- Consistent format across all system components
- Performance metrics for optimization

## Monitoring and Analysis

### Log Analysis Tools
The JSON Lines format works well with:
- `jq` for command-line JSON processing
- Log aggregation systems (ELK stack, etc.)
- Custom analysis scripts
- Real-time monitoring dashboards

### Alerting
- Unusual error patterns
- Service performance degradation
- Security-related events
- Resource utilization trends

This audit logging system provides comprehensive visibility into AI Employee Vault operations while ensuring reliability through robust error recovery mechanisms.