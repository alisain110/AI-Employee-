#!/bin/bash

echo "Starting all MCP servers..."

# Start Email MCP Server (port 8001)
echo "Starting Email MCP Server on port 8001..."
python -m uvicorn mcp_server.main:app --host 0.0.0.0 --port 8001 --log-level info &
EMAIL_PID=$!

sleep 5

# Start Odoo MCP Server (port 8002)
echo "Starting Odoo MCP Server on port 8002..."
python -m uvicorn odoo_mcp_server:app --host 0.0.0.0 --port 8002 --log-level info &
ODOO_PID=$!

sleep 5

# Start Social MCP Server (port 8003)
echo "Starting Social MCP Server on port 8003..."
python -m uvicorn social_mcp_server:app --host 0.0.0.0 --port 8003 --log-level info &
SOCIAL_PID=$!

echo
echo "All MCP servers started!"
echo
echo "Email MCP Server: http://localhost:8001/docs"
echo "Odoo MCP Server: http://localhost:8002/docs"
echo "Social MCP Server: http://localhost:8003/docs"
echo
echo "Server PIDs: Email=$EMAIL_PID, Odoo=$ODOO_PID, Social=$SOCIAL_PID"
echo
echo "Press Ctrl+C to stop all servers"
echo

# Function to handle shutdown
cleanup() {
    echo
    echo "Shutting down MCP servers..."
    kill $EMAIL_PID $ODOO_PID $SOCIAL_PID 2>/dev/null
    exit 0
}

# Set up signal trapping
trap cleanup INT TERM

# Wait indefinitely
while true; do
    sleep 1
done