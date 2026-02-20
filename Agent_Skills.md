# AI Employee Agent Skills

## Overview
This file defines the agent skills for the AI Employee system. These skills enable Claude Code to interact with the local file system and perform various tasks autonomously.

## Skill: File Management
### Description
Handles reading, writing, and moving files within the AI Employee vault.

### Functions
1. **Read File**: Reads the content of a file from the vault
2. **Write File**: Creates or updates a file in the specified directory
3. **Move File**: Moves a file from one directory to another
4. **List Files**: Lists all files in a specified directory

### Usage
```
- Read file "Inbox/some_file.md" to see its content
- Write file "Needs_Action/new_task.md" with specific content
- Move file "Inbox/urgent.md" to "Needs_Action/"
- List all files in "Done/" to see completed tasks
```

## Skill: Task Processing
### Description
Manages the workflow of processing tasks from intake to completion.

### Functions
1. **Process Task**: Takes a task from Needs_Action and processes it
2. **Create Plan**: Creates a plan file for multi-step tasks
3. **Request Approval**: Creates an approval request for sensitive tasks
4. **Update Dashboard**: Updates the dashboard with current status

### Usage
```
- Process all files in Needs_Action/
- Create a plan for complex multi-step tasks
- Request approval for financial transactions
- Update dashboard with latest status
```

## Skill: Communication Handling
### Description
Manages incoming and outgoing communications.

### Functions
1. **Handle Email**: Process incoming emails and draft responses
2. **Handle Message**: Process instant messages and generate replies
3. **Schedule Communication**: Schedule future communications
4. **Archive Communication**: Move processed communications to archive

### Usage
```
- Handle new email from client
- Draft response to inquiry
- Schedule weekly newsletter
- Archive old communications
```

## Skill: Financial Tracking
### Description
Manages financial records and transactions.

### Functions
1. **Record Transaction**: Log a new financial transaction
2. **Categorize Expense**: Categorize an expense according to business rules
3. **Generate Report**: Create financial reports
4. **Flag Anomaly**: Identify unusual financial patterns

### Usage
```
- Record a new business expense
- Categorize subscription costs
- Generate weekly financial summary
- Flag unusual spending patterns
```

## Skill: Monitoring and Alerts
### Description
Monitors systems and raises alerts when needed.

### Functions
1. **Monitor Directory**: Watch a directory for new files
2. **Check Thresholds**: Compare values against defined thresholds
3. **Generate Alert**: Create alert messages when thresholds exceeded
4. **Send Notification**: Notify human operator of important events

### Usage
```
- Monitor Inbox for new files
- Check if expenses exceed monthly budget
- Generate alert for urgent tasks
- Send notification to human operator
```

## Implementation Requirements
- All skills must log their actions in the Logs/ directory
- All skills must respect the Company_Handbook.md guidelines
- All sensitive operations must require human approval
- All operations must update the Dashboard.md accordingly