"""
Test script for X (Twitter) skills
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_skills_loading():
    """Test that the X skills can be loaded properly"""
    print("Testing X skills loading...")

    try:
        # Test loading the skills
        from skills.x_poster_and_summary import post_tweet, generate_weekly_x_summary

        print("[SUCCESS] X skills loaded successfully")

        # Print tool info
        print(f"Post tweet tool: {post_tweet.name}")
        print(f"Generate weekly X summary tool: {generate_weekly_x_summary.name}")

        return True
    except Exception as e:
        print(f"[ERROR] Error loading X skills: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_integration():
    """Test that the X skills work with the agent"""
    print("\nTesting X agent integration...")

    try:
        from core.agent import AIAgent

        agent = AIAgent()

        # Check if our X skills are loaded
        skills = agent.list_skills()
        print(f"Loaded skills: {len(skills)}")

        # Check for our specific X skills
        has_post_tweet = "post_tweet" in skills
        has_weekly_summary = "generate_weekly_x_summary" in skills

        print(f"[SUCCESS] post_tweet skill loaded: {has_post_tweet}")
        print(f"[SUCCESS] generate_weekly_x_summary skill loaded: {has_weekly_summary}")

        return has_post_tweet and has_weekly_summary
    except Exception as e:
        print(f"[ERROR] Error testing X agent integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_example_usage():
    """Show example usage of the X skills"""
    print("\nExample Usage:")
    print("=" * 50)

    print("\n1. Post Tweet Skill:")
    print("   agent.run('post_tweet', text='Check out our new feature!')")

    print("\n2. Post Tweet with Media:")
    print("   agent.run('post_tweet', text='New product launch!', media_ids=['1234567890'])")

    print("\n3. Post Tweet as Reply:")
    print("   agent.run('post_tweet', text='@username Thanks for the feedback!', reply_to='0987654321')")

    print("\n4. Generate Weekly X Summary:")
    print("   agent.run('generate_weekly_x_summary')")

    print("\n5. Sensitive content (containing words like 'buy', 'sale', etc.) will automatically")
    print("   create approval requests in the Pending_Approval folder.")

    print("\n6. To use these skills, make sure your .env file contains:")
    print("   - X_API_KEY")
    print("   - X_API_SECRET")
    print("   - X_ACCESS_TOKEN")
    print("   - X_ACCESS_TOKEN_SECRET")
    print("   - X_BEARER_TOKEN")
    print("   - ANTHROPIC_API_KEY (for Claude summaries)")

def show_setup_instructions():
    """Show setup instructions"""
    print("\nSetup Instructions:")
    print("=" * 50)
    print("1. Get X API credentials from https://developer.twitter.com/")
    print("2. Create a Twitter App and get API keys")
    print("3. Copy .env_x_example to .env and add your credentials")
    print("4. Install required packages: pip install tweepy")
    print("5. Make sure ANTHROPIC_API_KEY is also set for summaries")

if __name__ == "__main__":
    print("Testing X (Twitter) Skills")
    print("=" * 50)

    success1 = test_skills_loading()
    success2 = test_agent_integration()

    if success1 and success2:
        print("\n[SUCCESS] All X skill tests passed! X skills are ready to use.")
        show_setup_instructions()
        show_example_usage()
    else:
        print("\n[ERROR] Some X skill tests failed.")