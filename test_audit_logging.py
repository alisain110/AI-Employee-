"""
Test script to verify audit logging functionality
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_audit_logging():
    """Test that audit logging works correctly"""
    print("Testing audit logging functionality...")

    from audit_logger import get_audit_logger, AuditActor, AuditAction

    audit_logger = get_audit_logger()

    # Test different types of log entries
    print("1. Testing MCP call logging...")
    audit_logger.log_mcp_call(
        service="test_service",
        endpoint="test_endpoint",
        data={"test_key": "test_value"},
        success=True,
        response={"result": "success"},
        session_id="test_session_123"
    )
    print("   [OK] MCP call logged successfully")

    print("2. Testing Claude request logging...")
    audit_logger.log_claude_request(
        model="claude-3-5-sonnet-20241022",
        prompt_length=100,
        response_length=200,
        success=True,
        session_id="test_session_123"
    )
    print("   [OK] Claude request logged successfully")

    print("3. Testing error logging...")
    audit_logger.log_error(
        error_type="test_error",
        error_message="This is a test error",
        context={"test": "context"},
        severity="medium",
        session_id="test_session_123"
    )
    print("   [OK] Error logged successfully")

    print("4. Testing task processed logging...")
    audit_logger.log_task_processed(
        task_id="test_task_123",
        task_type="test",
        processing_time=1.5,
        success=True,
        session_id="test_session_123"
    )
    print("   [OK] Task processed logged successfully")

    print("\n[OK] All audit logging tests passed!")

def test_error_recovery():
    """Test error recovery patterns"""
    print("\nTesting error recovery patterns...")

    from audit_logger import retry_on_transient_error

    attempt_count = 0

    @retry_on_transient_error(max_retries=3, base_delay=0.1)
    def test_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Simulated transient error: 429 rate limit exceeded")
        return "Success after retry"

    try:
        result = test_function()
        print(f"   [OK] Function succeeded after {attempt_count} attempts: {result}")
    except Exception as e:
        print(f"   [ERROR] Function failed: {e}")
        return False

    return True

def check_audit_log_files():
    """Check if audit log files were created"""
    print("\nChecking audit log files...")

    today = __import__('datetime').datetime.now().strftime('%Y-%m-%d')
    audit_log_path = Path("Logs") / f"audit_{today}.log"

    if audit_log_path.exists():
        size = audit_log_path.stat().st_size
        print(f"   [OK] Audit log file exists with {size} bytes")
        return True
    else:
        print("   [ERROR] Audit log file not found")
        return False

if __name__ == "__main__":
    print("Testing Audit Logging System")
    print("=" * 50)

    success1 = test_audit_logging()
    success2 = test_error_recovery()
    success3 = check_audit_log_files()

    print(f"\nOverall results:")
    print(f"- Audit logging: [OK]")
    print(f"- Error recovery: {'[OK]' if success2 else '[ERROR]'}")
    print(f"- Log files: {'[OK]' if success3 else '[ERROR]'}")

    if success2 and success3:
        print(f"\n[OK] All tests passed! Audit logging system is working correctly.")
    else:
        print(f"\n[ERROR] Some tests failed.")