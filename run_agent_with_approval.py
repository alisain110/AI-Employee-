"""
Example script to run the AI Agent with Human Approval System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set approval mode (console for direct interaction, production for file-based)
os.environ['APPROVAL_MODE'] = os.getenv('APPROVAL_MODE', 'console')  # Change to 'production' for file-based approval

# Import the agent
from core.agent import AIAgent

def main():
    # Create the plans directory if it doesn't exist
    plans_dir = Path("./plans")
    plans_dir.mkdir(exist_ok=True)

    # Initialize the agent
    agent = AIAgent()

    print(f"AI Agent initialized in {os.environ['APPROVAL_MODE']} mode")
    print("Available skills:")
    for skill_name in agent.list_skills():
        print(f"- {skill_name}")

    print("\n" + "="*50)

    # Example: Run Claude reasoning (doesn't require approval)
    print("Example 1: Running Claude reasoning (no approval needed)...")
    try:
        result = agent.run(
            "claude_reasoning_loop",
            task_description="Create a summary of Q1 goals",
            context="Focus on increasing customer engagement and sales"
        )
        print(f"✓ Plan created: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "="*50)

    # Example: Try to send an email (requires approval)
    print("Example 2: Attempting to send email (requires approval)...")
    try:
        result = agent.run(
            "send_email_skill",
            to="test@example.com",
            subject="Test from AI Employee",
            body="This is a test email from the AI Employee system."
        )
        print(f"Email result: {result}")
    except Exception as e:
        print(f"Email error: {e}")
        print("Note: In console mode, you'll be prompted for approval")

    print("\n" + "="*50)

    # Example: Try LinkedIn post (requires approval)
    print("Example 3: Attempting LinkedIn post (requires approval)...")
    try:
        result = agent.run(
            "linkedin_auto_post",
            post_topic="AI in business",
            context="Share insights about AI adoption in enterprises"
        )
        print(f"LinkedIn post result: {result}")
    except Exception as e:
        print(f"LinkedIn post error: {e}")
        print("Note: You'll be prompted for approval")

    print("\n" + "="*50)
    print("Examples completed. Check the Pending_Approval folder for any pending requests.")

if __name__ == "__main__":
    main()