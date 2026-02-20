"""
Script to run the weekly audit manually (for testing or on-demand execution)
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def run_manual_weekly_audit():
    """Run the weekly audit manually"""
    print("Running manual weekly audit...")
    print("This will generate a CEO briefing based on current data.")

    try:
        from weekly_audit_orchestrator import run_weekly_audit_job
        result = run_weekly_audit_job()

        if result:
            print(f"\n[SUCCESS] Weekly audit completed!")
            print(f"Report saved to: {result}")
            print("Report moved to Needs_Action folder for review.")
        else:
            print("\n[ERROR] Weekly audit failed. Check logs for details.")

    except Exception as e:
        print(f"[ERROR] Error running weekly audit: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Manual Weekly Audit Runner")
    print("=" * 30)
    run_manual_weekly_audit()