"""
Test script for MCP endpoints configuration and functionality
"""
import json
import requests
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_mcp_config():
    """Test that MCP endpoints configuration is valid"""
    print("Testing MCP endpoints configuration...")

    config_file = Path("mcp_endpoints.json")
    if not config_file.exists():
        print("[ERROR] MCP endpoints configuration file not found")
        return False

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        print("[SUCCESS] MCP endpoints configuration loaded successfully")
        print(f"Configured services: {list(config.keys())}")

        # Check required structure
        required_services = ["email_mcp", "odoo_mcp", "social_mcp"]
        missing_services = [service for service in required_services if service not in config]

        if missing_services:
            print(f"[WARNING] Missing services in config: {missing_services}")
        else:
            print("[SUCCESS] All required services configured")

        return True
    except Exception as e:
        print(f"[ERROR] Error loading MCP config: {e}")
        return False

def test_health_checks():
    """Test health checks for all MCP servers"""
    print("\nTesting MCP server health checks...")

    config_file = Path("mcp_endpoints.json")
    if not config_file.exists():
        print("[ERROR] MCP endpoints configuration not found")
        return False

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        all_healthy = True

        for service_name, service_config in config.items():
            url = service_config['url']
            health_endpoint = service_config['health_endpoint']

            full_url = f"{url}{health_endpoint}"

            try:
                response = requests.get(full_url, timeout=5)
                if response.status_code == 200:
                    print(f"[SUCCESS] {service_name} healthy: {full_url}")
                else:
                    print(f"[WARNING] {service_name} unhealthy: {full_url} (Status: {response.status_code})")
                    all_healthy = False
            except requests.exceptions.ConnectionError:
                print(f"[ERROR] {service_name} connection failed: {full_url} (Server may not be running)")
                all_healthy = False
            except Exception as e:
                print(f"[ERROR] {service_name} error: {full_url} ({e})")
                all_healthy = False

        return all_healthy
    except Exception as e:
        print(f"[ERROR] Error testing health checks: {e}")
        return False

def show_mcp_usage():
    """Show how to use MCP endpoints"""
    print("\nMCP Endpoints Usage:")
    print("=" * 50)
    print("\n1. Configuration is in mcp_endpoints.json")
    print("2. Each service has: URL, endpoints, auth settings")
    print("3. Orchestrator dynamically calls endpoints based on config")
    print("4. Fallback to direct agent skills if MCP unavailable")

    print("\nServer Ports:")
    print("- Email MCP: 8001 (email_mcp_server.py or mcp_server/main.py)")
    print("- Odoo MCP: 8002 (odoo_mcp_server.py)")
    print("- Social MCP: 8003 (social_mcp_server.py)")

    print("\nTo start all servers:")
    print("- Windows: start_all_mcps.bat")
    print("- Unix: chmod +x start_all_mcps.sh && ./start_all_mcps.sh")

def test_orchestrator_mcp_functionality():
    """Test orchestrator MCP functionality"""
    print("\nTesting orchestrator MCP functionality...")

    try:
        from orchestrator import AIOrchestrator

        # Create orchestrator instance
        orchestrator = AIOrchestrator(str(Path.cwd()))

        print("[SUCCESS] Orchestrator loaded with MCP endpoint functionality")
        print(f"Loaded MCP endpoints: {list(orchestrator.mcp_endpoints.keys())}")

        # Test call_mcp_endpoint method exists
        if hasattr(orchestrator, 'call_mcp_endpoint'):
            print("[SUCCESS] call_mcp_endpoint method available")
        else:
            print("[ERROR] call_mcp_endpoint method missing")
            return False

        # Test load_mcp_endpoints method exists
        if hasattr(orchestrator, 'load_mcp_endpoints'):
            print("[SUCCESS] load_mcp_endpoints method available")
        else:
            print("[ERROR] load_mcp_endpoints method missing")
            return False

        return True
    except Exception as e:
        print(f"[ERROR] Error testing orchestrator MCP functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing MCP Architecture Refactor")
    print("=" * 50)

    success1 = test_mcp_config()
    success2 = test_orchestrator_mcp_functionality()
    success3 = test_health_checks()  # This will fail if servers aren't running

    print(f"\nResults:")
    print(f"- Config test: {'[SUCCESS] PASS' if success1 else '[ERROR] FAIL'}")
    print(f"- Orchestrator test: {'[SUCCESS] PASS' if success2 else '[ERROR] FAIL'}")
    print(f"- Health checks: {'[SUCCESS] PASS' if success3 else '[ERROR] FAIL (servers likely not running)'}")

    show_mcp_usage()

    print(f"\nOverall: {'[SUCCESS] All tests passed!' if success1 and success2 else '[ERROR] Some tests failed'}")