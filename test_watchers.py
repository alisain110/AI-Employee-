"""
Simple test script to verify watcher functionality
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up API key
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'fake_key_for_testing')

from core.agent import AIAgent

def test_watchers():
    # Initialize the agent
    agent = AIAgent()

    print("Skills available:", agent.list_skills())
    print()

    # Test Claude reasoning loop (should work)
    print("Testing Claude reasoning loop...")
    try:
        result = agent.run(
            "claude_reasoning_loop",
            task_description="Create a test plan",
            context="This is just for testing"
        )
        print("Claude reasoning loop: SUCCESS")
        print("Result:", result)
    except Exception as e:
        print(f"Claude reasoning loop: FAILED - {e}")

    print()

    # Test each watcher individually
    watchers = [
        ("gmail_watcher_skill", {"action": "start"}),
        ("whatsapp_watcher_skill", {"action": "start"}),
        ("linkedin_watcher_skill", {"action": "start"})
    ]

    for watcher_name, params in watchers:
        print(f"Testing {watcher_name}...")
        try:
            result = agent.run(watcher_name, **params)
            print(f"{watcher_name}: SUCCESS - {result}")
        except Exception as e:
            print(f"{watcher_name}: ERROR - {e}")

        # Also test the stop action
        try:
            result = agent.run(watcher_name, action="stop")
            print(f"{watcher_name} (stop): SUCCESS - {result}")
        except Exception as e:
            print(f"{watcher_name} (stop): ERROR - {e}")

        print()

if __name__ == "__main__":
    test_watchers()