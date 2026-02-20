# Ralph Wiggum Mode Implementation

## Overview

Ralph Wiggum mode is an advanced iterative processing feature in the AI Employee Vault orchestrator that enables complex tasks to be processed through multiple reasoning loops with dynamic tool execution.

## Key Features

### Dual Mode System
- **Normal Mode**: Single reasoning pass for straightforward tasks
- **Ralph Mode**: Iterative processing for complex, multi-step tasks

### Ralph Mode Characteristics
- **Trigger**: `mode: ralph` flag in task configuration
- **Iteration Limit**: Maximum 15 iterations per task
- **Time Cap**: 2-hour maximum processing time
- **Fresh Context**: Each iteration receives fresh context without accumulated history
- **Tool Execution**: Dynamic MCP endpoint routing for tool calls
- **State Management**: Supports DONE, CONTINUE, FAILED, and NEEDS_HUMAN states

## How It Works

### 1. Detection
The orchestrator scans task files for the `mode: ralph` configuration flag:

```markdown
## Configuration
mode: ralph
```

### 2. Iterative Process
Each iteration follows this pattern:
1. Read current task + all related files
2. Prepare fresh context (no huge history)
3. Send context to Claude for analysis
4. Claude outputs structured JSON with:
   - `thought`: Reasoning about the current state
   - `tool_calls`: Tools to execute with arguments
   - `next_action`: Decision to CONTINUE, DONE, FAILED, or NEEDS_HUMAN

### 3. Tool Execution
- Direct agent skills are executed if available
- MCP endpoints are dynamically routed based on configuration
- Results are logged and fed into the next iteration

### 4. Safety Mechanisms
- **Iteration Cap**: Automatically stops after 15 iterations
- **Time Cap**: Terminates if processing exceeds 2 hours
- **Emergency Stop**: Monitors for `EMERGENCY_STOP_RALPH` file

## Directory Structure

```
Vault/
├── Ralph_Logs/           # Stores iteration logs
│   └── {task_name}/
│       ├── step_01.md    # First iteration
│       ├── step_02.md    # Second iteration
│       └── ...
├── Pending_Approval/     # Human approval requests
├── Needs_Action/         # Tasks awaiting processing
└── ...
```

## Example Task

The `example_ralph_task.md` file demonstrates how to trigger Ralph mode:

```markdown
---
title: Example Ralph Wiggum Mode Task
---

# Example Ralph Mode Task

## Configuration
mode: ralph

## Task Description
This is an example task that will trigger Ralph Wiggum mode...
```

## JSON Response Format

Claude responses must follow this structure:

```json
{
  "thought": "Your brief thought about the current state",
  "tool_calls": [
    {
      "name": "tool_name",
      "arguments": {"arg1": "value1", "arg2": "value2"}
    }
  ],
  "next_action": "DONE | CONTINUE | FAILED | NEEDS_HUMAN"
}
```

## MCP Endpoint Integration

Ralph mode supports dynamic MCP endpoint routing:

- Endpoints configured in `mcp_endpoints.json`
- Tool names like `odoo_create_invoice` route to `odoo_mcp` service
- Automatic fallback if endpoint doesn't exist

## Safety Features

### Emergency Stop
Create an `EMERGENCY_STOP_RALPH` file in the vault root to immediately halt all Ralph loops.

### Logging
Each iteration is logged to:
- File: `/Ralph_Logs/{task_name}/step_{XX}.md`
- Format: Markdown with timestamp and Claude response

### Human Intervention
When `next_action` is `NEEDS_HUMAN`, the task is moved to the `Pending_Approval` folder for review.

## Usage

1. Create a task file in `Needs_Action/` with `mode: ralph`
2. The orchestrator will detect and process in iterative mode
3. Monitor progress in the `Ralph_Logs/` directory
4. Handle any approval requests in `Pending_Approval/`