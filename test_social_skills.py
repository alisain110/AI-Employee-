"""
Test script for social media skills
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_skills_loading():
    """Test that the skills can be loaded properly"""
    print("Testing social media skills loading...")

    try:
        # Test loading the skills
        from skills.facebook_poster import facebook_poster
        from skills.social_summary_generator import social_summary_generator

        print("[SUCCESS] Skills loaded successfully")

        # Print tool info
        print(f"Facebook poster tool: {facebook_poster.name}")
        print(f"Social summary generator tool: {social_summary_generator.name}")

        return True
    except Exception as e:
        print(f"[ERROR] Error loading skills: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_integration():
    """Test that the skills work with the agent"""
    print("\nTesting agent integration...")

    try:
        from core.agent import AIAgent

        agent = AIAgent()

        # Check if our skills are loaded
        skills = agent.list_skills()
        print(f"Loaded skills: {len(skills)}")

        # Check for our specific skills
        has_facebook_poster = "facebook_poster" in skills
        has_social_summary = "social_summary_generator" in skills

        print(f"[SUCCESS] facebook_poster skill loaded: {has_facebook_poster}")
        print(f"[SUCCESS] social_summary_generator skill loaded: {has_social_summary}")

        return has_facebook_poster and has_social_summary
    except Exception as e:
        print(f"[ERROR] Error testing agent integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_example_usage():
    """Show example usage of the skills"""
    print("\nExample Usage:")
    print("=" * 50)

    print("\n1. Facebook Poster Skill:")
    print("   agent.run('facebook_poster', text='Check out our new product!', image_url='https://example.com/image.jpg')")

    print("\n2. Social Summary Generator Skill:")
    print("   agent.run('social_summary_generator', platform='facebook')")
    print("   agent.run('social_summary_generator', platform='instagram')")
    print("   agent.run('social_summary_generator', platform='x')")

    print("\n3. The orchestrator will automatically detect social media tasks in files")
    print("   and call the appropriate skills when it finds keywords like:")
    print("   - 'facebook post', 'instagram share', 'x summary', etc.")

if __name__ == "__main__":
    print("Testing Social Media Skills")
    print("=" * 50)

    success1 = test_skills_loading()
    success2 = test_agent_integration()

    if success1 and success2:
        print("\n[SUCCESS] All tests passed! Social media skills are ready to use.")
        show_example_usage()
    else:
        print("\n[ERROR] Some tests failed.")