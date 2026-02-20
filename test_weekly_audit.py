"""
Test script for weekly audit orchestrator
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        from weekly_audit_orchestrator import WeeklyAuditOrchestrator, run_weekly_audit_job
        print("[SUCCESS] Weekly audit orchestrator imported successfully")
    except Exception as e:
        print(f"[ERROR] Could not import weekly audit orchestrator: {e}")
        return False

    try:
        from scheduler import AIEmployeeScheduler
        print("[SUCCESS] Scheduler imported successfully")
    except Exception as e:
        print(f"[ERROR] Could not import scheduler: {e}")
        return False

    return True

def test_orchestrator_creation():
    """Test creating the orchestrator instance"""
    print("\nTesting orchestrator creation...")

    try:
        from weekly_audit_orchestrator import WeeklyAuditOrchestrator
        orchestrator = WeeklyAuditOrchestrator()
        print("[SUCCESS] WeeklyAuditOrchestrator instance created")
        print(f"[INFO] Loaded MCP endpoints: {list(orchestrator.mcp_endpoints.keys())}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not create orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler_integration():
    """Test that scheduler includes the weekly audit job"""
    print("\nTesting scheduler integration...")

    try:
        from core.agent import AIAgent
        from scheduler import AIEmployeeScheduler

        agent = AIAgent()
        scheduler = AIEmployeeScheduler(agent)

        # Check if the weekly audit job is scheduled
        job_ids = [job.id for job in scheduler.scheduler.get_jobs()]
        print(f"[INFO] Scheduled jobs: {job_ids}")

        if 'weekly_audit' in job_ids:
            print("[SUCCESS] Weekly audit job found in scheduler")
            return True
        else:
            print("[ERROR] Weekly audit job not found in scheduler")
            return False
    except Exception as e:
        print(f"[ERROR] Could not test scheduler integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_schedule_details():
    """Show schedule details"""
    print("\nWeekly Audit Schedule Details:")
    print("=" * 50)
    print("Job: Weekly CEO Briefing and Audit")
    print("Schedule: Every Monday at 9:00 AM")
    print("Action: Runs weekly_audit_orchestrator.py")
    print("Output: Creates YYYY-WW_CEO_Briefing.md in /Audits/")
    print("Next action: Moves to /Needs_Action/ as high-priority task")
    print("\nProcess:")
    print("1. Fetch Odoo metrics (revenue, unpaid, expenses)")
    print("2. Generate social media summaries (FB/IG/X)")
    print("3. Create comprehensive report with Claude")
    print("4. Save to Audits folder with proper naming")
    print("5. Move to Needs_Action as high-priority task")

def test_manual_run():
    """Test a manual run (without actually executing to avoid side effects)"""
    print("\nTesting manual run capability...")

    try:
        from weekly_audit_orchestrator import run_weekly_audit_job
        print("[SUCCESS] Manual run function available")
        print("Note: Not executing to avoid creating test files")
        return True
    except Exception as e:
        print(f"[ERROR] Manual run function not available: {e}")
        return False

if __name__ == "__main__":
    print("Testing Weekly Audit Orchestrator Integration")
    print("=" * 50)

    success1 = test_imports()
    success2 = test_orchestrator_creation()
    success3 = test_scheduler_integration()
    success4 = test_manual_run()

    print(f"\nResults:")
    print(f"- Import test: {'[SUCCESS]' if success1 else '[ERROR]'}")
    print(f"- Orchestrator test: {'[SUCCESS]' if success2 else '[ERROR]'}")
    print(f"- Scheduler test: {'[SUCCESS]' if success3 else '[ERROR]'}")
    print(f"- Manual run test: {'[SUCCESS]' if success4 else '[ERROR]'}")

    if success1 and success2 and success3 and success4:
        print(f"\n[SUCCESS] All tests passed! Weekly audit orchestrator is ready.")
        show_schedule_details()
    else:
        print(f"\n[ERROR] Some tests failed.")