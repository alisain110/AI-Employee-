"""
Example showing the complete approval workflow
"""
import os
from pathlib import Path

# Set environment
os.environ['ANTHROPIC_API_KEY'] = 'fake_key_for_testing'
os.environ['APPROVAL_MODE'] = 'console'  # Use 'production' for file-based approval

def example_approval_workflow():
    """
    Example showing how the approval workflow works
    """
    print("AI Employee - Approval Workflow Example")
    print("=" * 50)

    print("\n1. Loading AI Agent with approval system...")
    from core.agent import AIAgent
    agent = AIAgent()

    print(f"   Loaded {len(agent.list_skills())} skills")
    sensitive_skills = ['linkedin_auto_post', 'send_email_skill', 'execute_action_skill']
    loaded_sensitive = [skill for skill in sensitive_skills if skill in agent.list_skills()]
    print(f"   Sensitive skills with approval: {loaded_sensitive}")

    print("\n2. Running non-sensitive action (no approval required)...")
    try:
        result = agent.run('claude_reasoning_loop',
                          task_description='Create a simple task plan',
                          context='Just a test task')
        print(f"   ✓ Claude reasoning completed: {result}")
    except Exception as e:
        print(f"   ✗ Claude reasoning failed: {e}")

    print("\n3. Attempting sensitive action (approval required)...")
    print("   This will trigger the approval system")

    # Example of what would happen with a sensitive action
    print("   In console mode: User would be prompted for approval")
    print("   In production mode: Approval request file would be created")

    # Show the approval system is working by checking for pending approvals
    from utilities.human_approval import check_for_approvals
    pending = check_for_approvals()
    print(f"   Current pending approvals: {pending}")

    print("\n4. Example approval request structure:")
    print("   When a sensitive action is requested, the system creates:")
    print("   - An approval request file in Pending_Approval/")
    print("   - Contains action details, arguments, timestamp")
    print("   - Waits for human decision (YES/NO or file move)")

    print("\n5. Approval flow options:")
    print("   Console Mode: Interactive YES/NO prompt")
    print("   Production Mode: File-based system")
    print("     - Request appears in Pending_Approval/")
    print("     - Move to Approved/ to allow execution")
    print("     - Move to Rejected/ to deny execution")

    print("\n6. Sensitive skills that require approval:")
    for skill in loaded_sensitive:
        print(f"   - {skill}")

    print("\n7. Environment configuration:")
    print(f"   APPROVAL_MODE = {os.environ.get('APPROVAL_MODE', 'console')}")
    print(f"   Approval directories exist: {all(Path(d).exists() for d in ['approvals', 'Pending_Approval', 'Approved', 'Rejected'])}")

    print("\nExample completed successfully!")
    print("\nTo run in production mode:")
    print("   Set APPROVAL_MODE=production")
    print("   Monitor Pending_Approval/ folder for approval requests")

if __name__ == "__main__":
    example_approval_workflow()