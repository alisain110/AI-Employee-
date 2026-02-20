#!/usr/bin/env python3
"""
Script to start the MCP server
"""
import os
import subprocess
import sys
import time
import threading
from pathlib import Path

def start_server():
    """Start the MCP server in a subprocess"""
    print("Starting MCP Server on port 8001...")

    # Change to the mcp_server directory
    server_dir = Path(__file__).parent / "mcp_server"
    os.chdir(server_dir)

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Run the server using uvicorn
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload", "False"]

    try:
        print("MCP server started successfully on http://localhost:8001")
        print("Press Ctrl+C to stop the server")

        server_process = subprocess.Popen(cmd)

        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down MCP server...")
            server_process.terminate()
            server_process.wait()
            print("MCP server stopped.")

    except Exception as e:
        print(f"Failed to start MCP server: {e}")

if __name__ == "__main__":
    start_server()