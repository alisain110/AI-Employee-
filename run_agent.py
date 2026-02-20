"""
Example script to run the AI Agent with Claude Reasoning Loop
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the agent
from core.agent import AIAgent

def main():
    # Create the plans directory if it doesn't exist
    plans_dir = Path("./plans")
    plans_dir.mkdir(exist_ok=True)

    # Initialize the agent
    agent = AIAgent()

    print("AI Agent initialized with the following skills:")
    for skill_name in agent.list_skills():
        print(f"- {skill_name}")

    print("\n" + "="*50)

    # Example 1: Create a marketing plan
    print("Example 1: Creating a marketing plan...")
    try:
        result = agent.run(
            "claude_reasoning_loop",
            task_description="Create a comprehensive marketing strategy for launching a new SaaS product",
            context="The product is a project management tool for small development teams. Target audience is tech startups with 5-20 employees."
        )
        print(f"✓ Plan created: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("Note: Make sure to set your ANTHROPIC_API_KEY in the environment")

    print("\n" + "="*50)

    # Example 2: Create a project plan
    print("Example 2: Creating a project plan...")
    try:
        result = agent.run(
            "claude_reasoning_loop",
            task_description="Develop a 3-month roadmap for implementing a new customer support system",
            context="Current system is email-based, needs to be replaced with a ticketing system. Team has 3 developers and 1 designer."
        )
        print(f"✓ Plan created: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "="*50)
    print("All plans have been saved to the 'plans' folder.")
    print("The main Plan.md file contains all plans appended together.")

if __name__ == "__main__":
    main()