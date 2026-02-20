"""
Main runner for AI Employee system
Starts MCP server, all watchers, scheduler, and loads agent with all skills
"""
import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIEmployeeMainRunner:
    def __init__(self):
        self.mcp_server_process = None
        self.scheduler = None
        self.agent = None

    def start_mcp_server(self):
        """Start the MCP server in a background process"""
        print("Starting MCP Server...")

        # Change to mcp_server directory
        mcp_dir = Path(__file__).parent / "mcp_server"

        # Create logs directory
        (mcp_dir / "logs").mkdir(exist_ok=True)

        # Start the MCP server using uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--log-level", "info"
        ]

        try:
            self.mcp_server_process = subprocess.Popen(
                cmd,
                cwd=mcp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print("MCP Server started successfully on port 8001")
            return True
        except Exception as e:
            print(f"Failed to start MCP Server: {e}")
            return False

    def wait_for_mcp_server(self, timeout=30):
        """Wait for MCP server to be ready"""
        import requests
        import time

        start_time = time.time()
        mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

        while time.time() - start_time < timeout:
            try:
                # Check if the server is responding
                response = requests.get(f"{mcp_url}/health", timeout=5)
                if response.status_code == 200:
                    print("MCP Server is ready!")
                    return True
            except:
                pass
            time.sleep(1)

        print("MCP Server did not start in time")
        return False

    def load_agent(self):
        """Load the AI agent with all skills"""
        print("Loading AI Agent with all skills...")

        try:
            # Set API key
            if not os.getenv('ANTHROPIC_API_KEY'):
                print("Warning: ANTHROPIC_API_KEY not set in environment")

            from core.agent import AIAgent
            self.agent = AIAgent()

            print(f"AI Agent loaded with {len(self.agent.list_skills())} skills:")
            for skill in self.agent.list_skills():
                print(f"  - {skill}")

            return True
        except Exception as e:
            print(f"Error loading AI Agent: {e}")
            return False

    def start_scheduler(self):
        """Start the task scheduler"""
        print("Starting scheduler...")

        try:
            from scheduler import AIEmployeeScheduler
            self.scheduler = AIEmployeeScheduler(self.agent)
            self.scheduler.start()
            print("Scheduler started successfully")
            return True
        except Exception as e:
            print(f"Error starting scheduler: {e}")
            return False

    def run_health_check(self):
        """Run a basic health check"""
        print("\nRunning system health check...")

        checks = []

        # Check MCP server
        try:
            import requests
            mcp_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
            response = requests.get(f"{mcp_url}/health", timeout=5)
            checks.append(("MCP Server", response.status_code == 200))
        except:
            checks.append(("MCP Server", False))

        # Check agent skills
        if self.agent:
            required_skills = ["claude_reasoning_loop", "linkedin_auto_post",
                             "send_email_skill", "gmail_watcher_skill",
                             "whatsapp_watcher_skill", "linkedin_watcher_skill"]
            loaded_skills = set(self.agent.list_skills())
            skill_check = all(skill in loaded_skills for skill in required_skills)
            checks.append(("Required Skills", skill_check))
        else:
            checks.append(("Required Skills", False))

        # Print health check results
        print("\nHealth Check Results:")
        for check_name, status in checks:
            status_str = "✓" if status else "✗"
            print(f"  {status_str} {check_name}")

        all_good = all(status for _, status in checks)
        return all_good

    def start(self):
        """Start the complete AI Employee system"""
        print("Starting AI Employee System...")
        print("=" * 50)

        # Start MCP server
        if not self.start_mcp_server():
            print("Failed to start MCP server. Exiting...")
            return False

        # Wait for MCP server to be ready
        if not self.wait_for_mcp_server():
            print("MCP server not ready. Exiting...")
            return False

        # Load agent
        if not self.load_agent():
            print("Failed to load AI agent. Exiting...")
            return False

        # Start scheduler
        if not self.start_scheduler():
            print("Failed to start scheduler. Exiting...")
            return False

        # Run health check
        if self.run_health_check():
            print("\n✓ AI Employee System started successfully!")
            print("✓ MCP Server running on http://localhost:8001")
            print("✓ All watchers started (checking every 5 minutes)")
            print("✓ Scheduler running with all scheduled tasks")
            print("✓ System will run until manually stopped")
        else:
            print("\n⚠ System started but with some issues detected")

        print("\nPress Ctrl+C to stop the system...")

        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nShutting down AI Employee System...")
            self.shutdown()

    def shutdown(self):
        """Shut down the system gracefully"""
        print("Shutting down...")

        # Shutdown scheduler
        if self.scheduler:
            try:
                self.scheduler.shutdown()
            except:
                pass

        # Terminate MCP server process
        if self.mcp_server_process:
            try:
                self.mcp_server_process.terminate()
                self.mcp_server_process.wait(timeout=5)
            except:
                try:
                    self.mcp_server_process.kill()
                except:
                    pass

        print("AI Employee System stopped.")


def main():
    """Main entry point"""
    runner = AIEmployeeMainRunner()
    runner.start()


if __name__ == "__main__":
    main()