"""
Example script to run all watcher skills with the AI Agent
"""
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agent
from core.agent import AIAgent

def main():
    # Set up API key (use fake one for testing)
    os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'fake_key_for_testing')

    # Initialize the agent
    agent = AIAgent()

    print("AI Agent initialized with the following skills:")
    for skill_name in agent.list_skills():
        print(f"- {skill_name}")
    print()

    print("="*60)
    print("WATCHER MANAGEMENT EXAMPLE")
    print("="*60)

    # Example 1: Start all watchers
    print("1. Starting all watchers...")

    try:
        # Start Gmail watcher
        result = agent.run("gmail_watcher_skill", action="start")
        print(f"✓ Gmail watcher: {result}")
    except Exception as e:
        print(f"x Gmail watcher error: {e}")
        print("   Note: Gmail requires proper OAuth setup (see documentation)")

    try:
        # Start WhatsApp watcher
        result = agent.run("whatsapp_watcher_skill", action="start")
        print(f"v WhatsApp watcher: {result}")
    except Exception as e:
        print(f"x WhatsApp watcher error: {e}")
        print("   Note: WhatsApp requires Chrome browser and manual login")

    try:
        # Start LinkedIn watcher
        result = agent.run("linkedin_watcher_skill", action="start")
        print(f"v LinkedIn watcher: {result}")
    except Exception as e:
        print(f"x LinkedIn watcher error: {e}")
        print("   Note: LinkedIn requires Chrome browser and manual login")

    print()
    print("Watchers are now running in the background!")
    print("They will monitor for new activity and automatically process")
    print("notifications/messages through Claude reasoning.")
    print()

    print("2. Example of Claude reasoning loop (standalone):")
    try:
        result = agent.run(
            "claude_reasoning_loop",
            task_description="Create a customer outreach plan",
            context="We need to reach out to potential customers in the tech industry"
        )
        print(f"✓ Plan created: {result}")
    except Exception as e:
        print(f"✗ Claude reasoning error: {e}")

    print()
    print("3. To stop all watchers, run:")
    print("   agent.run('gmail_watcher_skill', action='stop')")
    print("   agent.run('whatsapp_watcher_skill', action='stop')")
    print("   agent.run('linkedin_watcher_skill', action='stop')")

    print()
    print("Watchers continue running in background threads until stopped.")
    print("They check for new activity every 5 minutes and process it automatically.")

if __name__ == "__main__":
    main()