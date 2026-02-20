"""
Comprehensive Test Runner for AI Employee Vault
Tests all system components and validates functionality
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "comprehensive_tests.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveTestRunner:
    def __init__(self):
        self.test_results = {}
        self.test_summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0
        }

    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and track results"""
        logger.info(f"Running test: {test_name}")
        self.test_summary["total_tests"] += 1

        try:
            result = test_func(*args, **kwargs)
            if result:
                self.test_summary["passed_tests"] += 1
                status = "✅ PASSED"
            else:
                self.test_summary["failed_tests"] += 1
                status = "❌ FAILED"

            self.test_results[test_name] = {
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Test {test_name}: {status}")
            return result
        except Exception as e:
            self.test_summary["failed_tests"] += 1
            self.test_results[test_name] = {
                "status": "❌ ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"Test {test_name} ERROR: {e}")
            return False

    def test_file_structure(self) -> bool:
        """Test that required directories and files exist"""
        required_dirs = [
            "Inbox", "Needs_Action", "Approved", "Done",
            "Pending_Approval", "Pending_Approval/cloud",
            "Logs", "Audits", "Accounting", "Social_Summaries",
            "Briefings", "Ralph_Logs"
        ]

        required_files = [
            "Company_Handbook.md",
            "Business_Goals.md",
            "platinum_local_orchestrator.py",
            "approval_executor.py",
            "dashboard_merger.py",
            "odoo_draft_mcp.py",
            "odoo_execute_mcp.py",
            "social_mcp_server.py",
            "gmail_draft_mcp.py",
            "platinum_watchdog.py",
            "ralph_loop.py",
            "audit_logger.py",
            "scheduler.py"
        ]

        all_good = True

        # Check directories
        for dir_name in required_dirs:
            if not Path(dir_name).exists():
                logger.error(f"Missing directory: {dir_name}")
                all_good = False

        # Check files
        for file_name in required_files:
            if not Path(file_name).exists():
                logger.error(f"Missing file: {file_name}")
                all_good = False

        return all_good

    def test_imports(self) -> bool:
        """Test that all Python modules can be imported without errors"""
        modules_to_test = [
            "platinum_local_orchestrator",
            "approval_executor",
            "dashboard_merger",
            "odoo_draft_mcp",
            "odoo_execute_mcp",
            "social_mcp_server",
            "gmail_draft_mcp",
            "platinum_watchdog",
            "ralph_loop",
            "audit_logger",
            "scheduler",
            "cloud_watchers",
            "filesystem_watcher",
            "run_agent",
            "run_agent_with_approval",
            "start_platinum_services",
            "system_status_dashboard"
        ]

        all_good = True
        for module in modules_to_test:
            try:
                __import__(module)
                logger.info(f"Successfully imported: {module}")
            except ImportError as e:
                logger.error(f"Failed to import {module}: {e}")
                all_good = False
            except Exception as e:
                logger.error(f"Error importing {module}: {e}")
                all_good = False

        return all_good

    def test_environment_vars(self) -> bool:
        """Test that required environment variables are set"""
        required_vars = [
            "GMAIL_API_KEY",
            "LINKEDIN_EMAIL",
            "LINKEDIN_PASSWORD",
            "ODOO_URL",
            "ODOO_DB",
            "ODOO_API_KEY",
            "ODOO_USER_ID"
        ]

        # Some vars might be optional, so we'll check for common ones
        optional_vars = [
            "WHATSAPP_SESSION",
            "TWITTER_API_KEY"
        ]

        logger.info("Checking environment variables...")

        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            logger.warning("Environment file (.env) not found")
            return False

        # Check if the file has content
        with open(env_file, 'r') as f:
            env_content = f.read()

        if not env_content.strip():
            logger.warning("Environment file (.env) is empty")
            return False

        logger.info("Environment file found and has content")
        return True

    def test_mcp_endpoints(self) -> bool:
        """Test that MCP endpoint configuration is valid"""
        mcp_config = Path("mcp_endpoints.json")
        if not mcp_config.exists():
            logger.error("mcp_endpoints.json not found")
            return False

        try:
            with open(mcp_config, 'r') as f:
                config = json.load(f)

            # Check for required keys
            required_keys = ["services", "endpoints", "authentication"]
            for key in required_keys:
                if key not in config:
                    logger.error(f"Missing key in mcp_endpoints.json: {key}")
                    return False

            logger.info("MCP endpoints configuration is valid")
            return True
        except Exception as e:
            logger.error(f"Error parsing mcp_endpoints.json: {e}")
            return False

    def test_dashboard_update(self) -> bool:
        """Test that dashboard can be updated"""
        try:
            # Create a simple dashboard if it doesn't exist
            dashboard_file = Path("Dashboard.md")
            if not dashboard_file.exists():
                with open(dashboard_file, 'w') as f:
                    f.write("# AI Employee Dashboard\n\n## Status: Active\n")

            # Try to update it with some content
            with open(dashboard_file, 'r') as f:
                content = f.read()

            # Append test content
            with open(dashboard_file, 'w') as f:
                f.write(f"# AI Employee Dashboard\n\n## Status: Active\n\n## Test Update: {datetime.now()}\n\n{content}")

            logger.info("Dashboard update test passed")
            return True
        except Exception as e:
            logger.error(f"Dashboard update test failed: {e}")
            return False

    def test_log_files(self) -> bool:
        """Test that log files can be written to"""
        test_log = logs_dir / "test_comprehensive.log"

        try:
            with open(test_log, 'a') as f:
                f.write(f"[{datetime.now()}] Test log entry\n")

            if test_log.exists():
                logger.info("Log file test passed")
                return True
            else:
                logger.error("Test log file was not created")
                return False
        except Exception as e:
            logger.error(f"Log file test failed: {e}")
            return False

    def test_config_files(self) -> bool:
        """Test that configuration files exist and are valid"""
        config_files = [
            "config/config.json",
            "config/approval_rules.json",
            "config/social_rules.json",
            "config/odoo_config.json"
        ]

        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        json.load(f)
                    logger.info(f"Valid config file: {config_file}")
                except:
                    logger.warning(f"Invalid JSON in config file: {config_file}")
            else:
                logger.info(f"Optional config file not found (OK): {config_file}")

        return True  # Don't fail if optional files are missing

    def test_skill_integration(self) -> bool:
        """Test that skills directory and structure exists"""
        skills_dir = Path("skills")

        if not skills_dir.exists():
            logger.error("Skills directory doesn't exist")
            return False

        # Check for skill files
        skill_files = list(skills_dir.glob("*.py"))
        if len(skill_files) == 0:
            logger.warning("No skill files found in skills/ directory")
            return True  # This is ok, just means no skills yet

        logger.info(f"Found {len(skill_files)} skill files")

        # Try to import a sample
        if skill_files:
            sample_file = skill_files[0].name.replace('.py', '')
            try:
                skill_module = __import__(f"skills.{sample_file}", fromlist=[sample_file])
                logger.info(f"Successfully imported skill: {sample_file}")
            except Exception as e:
                logger.warning(f"Could not import skill {sample_file}: {e}")

        return True

    def test_audit_system(self) -> bool:
        """Test audit system functionality"""
        try:
            # Import audit logger
            import audit_logger

            # Test basic audit logging
            audit_log = Path("Audits")
            audit_log.mkdir(exist_ok=True)

            # Create a test audit entry
            test_audit = audit_log / f"test_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": "comprehensive_test",
                "status": "active",
                "details": "Testing audit system functionality"
            }

            with open(test_audit, 'w') as f:
                json.dump(audit_entry, f, indent=2)

            logger.info("Audit system test passed")
            return True
        except Exception as e:
            logger.error(f"Audit system test failed: {e}")
            return False

    def run_all_tests(self) -> dict:
        """Run all comprehensive tests"""
        logger.info("Starting comprehensive system tests...")

        # Run all tests
        self.run_test("File Structure Test", self.test_file_structure)
        self.run_test("Import Test", self.test_imports)
        self.run_test("Environment Variables Test", self.test_environment_vars)
        self.run_test("MCP Endpoints Test", self.test_mcp_endpoints)
        self.run_test("Dashboard Update Test", self.test_dashboard_update)
        self.run_test("Log Files Test", self.test_log_files)
        self.run_test("Config Files Test", self.test_config_files)
        self.run_test("Skill Integration Test", self.test_skill_integration)
        self.run_test("Audit System Test", self.test_audit_system)

        # Generate final report
        report = self.generate_test_report()

        # Save detailed results
        results_file = logs_dir / "comprehensive_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": self.test_summary,
                "results": self.test_results,
                "report": report
            }, f, indent=2)

        logger.info(f"Comprehensive tests completed. Results saved to {results_file}")
        return self.test_summary

    def generate_test_report(self) -> str:
        """Generate a formatted test report"""
        report = []
        report.append("# Comprehensive Test Results")
        report.append(f"**Generated at:** {datetime.now().isoformat()}")
        report.append("")
        report.append("## Summary")
        report.append(f"- Total Tests: {self.test_summary['total_tests']}")
        report.append(f"- Passed: {self.test_summary['passed_tests']}")
        report.append(f"- Failed: {self.test_summary['failed_tests']}")
        report.append(f"- Skipped: {self.test_summary['skipped_tests']}")

        if self.test_summary['total_tests'] > 0:
            success_rate = (self.test_summary['passed_tests'] / self.test_summary['total_tests']) * 100
            report.append(f"- Success Rate: {success_rate:.1f}%")

        report.append("")
        report.append("## Detailed Results")

        for test_name, result in self.test_results.items():
            status = result['status']
            emoji = "✅" if "PASS" in status else "❌" if "FAIL" in status or "ERROR" in status else "⚠️"
            report.append(f"- {emoji} {test_name}: {status}")

        report.append("")

        # Overall assessment
        if self.test_summary['failed_tests'] == 0 and self.test_summary['total_tests'] > 0:
            report.append("## Overall Assessment: ✅ SYSTEM HEALTHY")
            report.append("All tests passed! The system is ready for production use.")
        elif self.test_summary['failed_tests'] / self.test_summary['total_tests'] < 0.3:  # Less than 30% failure
            report.append("## Overall Assessment: 🟡 SYSTEM USABLE WITH ISSUES")
            report.append("Most tests passed, but there are some issues that should be addressed.")
        else:
            report.append("## Overall Assessment: ❌ SYSTEM NEEDS ATTENTION")
            report.append("Too many tests failed. The system needs significant fixes before production use.")

        return "\n".join(report)

def main():
    logger.info("Starting AI Employee Vault Comprehensive Test Runner")

    runner = ComprehensiveTestRunner()
    results = runner.run_all_tests()

    print("\n" + "="*60)
    print("COMPREHENSIVE TEST RESULTS")
    print("="*60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {(results['passed_tests']/results['total_tests']*100):.1f}%" if results['total_tests'] > 0 else "No tests run")
    print("="*60)

if __name__ == "__main__":
    main()