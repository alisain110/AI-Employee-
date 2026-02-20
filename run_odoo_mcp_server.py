"""
Run script for Odoo MCP Server
"""
import subprocess
import sys

def run_server():
    """Run the Odoo MCP server using uvicorn"""
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "odoo_mcp_server:app",
            "--host", "0.0.0.0",
            "--port", "8002",
            "--reload", "false",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\nShutting down Odoo MCP Server...")
    except Exception as e:
        print(f"Error running server: {e}")

if __name__ == "__main__":
    run_server()