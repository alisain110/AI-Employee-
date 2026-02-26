#!/bin/bash

# AI Employee Vault Startup Script
# This script starts the orchestrator and all watchers

# Set the project directory
PROJECT_DIR="/home/ubuntu/ai_employee_vault"
LOG_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/pids"

# Create necessary directories
mkdir -p $LOG_DIR
mkdir -p $PID_DIR

# Function to start a process
start_process() {
    local name=$1
    local cmd=$2
    local log_file="$LOG_DIR/${name}.log"

    echo "Starting $name..."

    # Check if process is already running
    local pid_file="$PID_DIR/${name}.pid"
    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat $pid_file)
        if ps -p $existing_pid > /dev/null 2>&1; then
            echo "$name is already running with PID $existing_pid"
            return 1
        fi
    fi

    # Start the process in background and redirect output to log file
    nohup $cmd >> $log_file 2>&1 &
    local new_pid=$!

    # Save the PID
    echo $new_pid > $pid_file

    echo "$name started with PID $new_pid"
    return 0
}

# Change to project directory
cd $PROJECT_DIR

# Start orchestrator
start_process "orchestrator" "python3 orchestrator.py"

# Start Gmail watcher
start_process "gmail_watcher" "python3 -c \"
from core.agent import AIAgent
agent = AIAgent()
result = agent.run('gmail_watcher_skill', action='start')
print(f'Gmail watcher result: {result}')
\""

# Start WhatsApp watcher
start_process "whatsapp_watcher" "python3 -c \"
from core.agent import AIAgent
agent = AIAgent()
result = agent.run('whatsapp_watcher_skill', action='start')
print(f'WhatsApp watcher result: {result}')
\""

# Start LinkedIn watcher
start_process "linkedin_watcher" "python3 -c \"
from core.agent import AIAgent
agent = AIAgent()
result = agent.run('linkedin_watcher_skill', action='start')
print(f'LinkedIn watcher result: {result}')
\""

echo "All services started. Check logs in $LOG_DIR/"