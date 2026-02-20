"""
Script to run the MCP server
"""
import os
import sys
import subprocess
import threading
import time
import requests
from pathlib import Path

def check_port(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def run_server():
    """Run the MCP server"""
    print("Starting MCP Server on port 8001...")

    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Run the server
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"])

if __name__ == "__main__":
    port = 8001

    if not check_port(port):
        print(f"Port {port} is already in use. Please stop any existing server on this port first.")
        sys.exit(1)

    # Check if required environment variables are set
    api_key = os.getenv("MCP_API_KEY", "your-secret-api-key")
    if api_key == "your-secret-api-key":
        print("Warning: Using default API key. For production, set MCP_API_KEY environment variable.")

    run_server()