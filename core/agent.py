"""
Main AI Agent that dynamically loads skills from the skills folder
"""
import os
import sys
from pathlib import Path
from typing import List, Any
import importlib.util

def load_skills_from_folder(skills_folder: str) -> List[Any]:
    """
    Dynamically loads all skill modules from the skills folder.

    Args:
        skills_folder (str): Path to the skills folder

    Returns:
        List of skill functions/tools
    """
    skills = []
    skills_path = Path(skills_folder)

    # Add the skills folder to the Python path
    sys.path.insert(0, str(skills_path.parent))

    # Iterate through all Python files in the skills folder
    for file_path in skills_path.glob("*.py"):
        if file_path.name == "__init__.py":  # Skip the __init__.py file
            continue

        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for functions decorated with @tool
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                # Check if it's a LangChain tool by checking for tool-specific attributes
                # LangChain tools have name, description, and either are callable or have an invoke method
                if (hasattr(attr, 'name') and hasattr(attr, 'description') and
                    (callable(attr) or hasattr(attr, 'invoke')) and  # Tool can be invoked
                    not attr_name.startswith('_') and
                    attr_name != 'tool'):  # Skip the tool decorator itself
                    skills.append(attr)

    return skills

class AIAgent:
    """
    Main AI Agent that loads and manages skills dynamically
    """

    def __init__(self, skills_folder: str = "./skills"):
        self.skills_folder = skills_folder
        self.skills = load_skills_from_folder(skills_folder)
        print(f"Loaded {len(self.skills)} skills from {skills_folder}")

        # Store skills by name for easy access
        # LangChain tools have a 'name' attribute instead of '__name__'
        self.skill_registry = {getattr(skill, 'name', getattr(skill, '__name__', 'unknown')): skill for skill in self.skills}

    def get_skill(self, skill_name: str):
        """Get a specific skill by name"""
        return self.skill_registry.get(skill_name)

    def list_skills(self):
        """List all available skills"""
        return list(self.skill_registry.keys())

    def execute_skill(self, skill_name: str, **kwargs):
        """Execute a skill with given parameters"""
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found")

        # LangChain tools need to be invoked with the invoke method
        # rather than being called directly
        if hasattr(skill, 'invoke'):
            return skill.invoke(kwargs)
        elif callable(skill):
            return skill(**kwargs)
        else:
            raise ValueError(f"Skill '{skill_name}' is not properly callable")

    def run(self, skill_name: str, **kwargs):
        """Main method to run a specific skill"""
        return self.execute_skill(skill_name, **kwargs)

# Example usage
if __name__ == "__main__":
    # Create the plans directory if it doesn't exist
    plans_dir = Path("./plans")
    plans_dir.mkdir(exist_ok=True)

    # Initialize the agent
    agent = AIAgent()

    print("Available skills:", agent.list_skills())

    # Example: Run a skill if available
    if "claude_reasoning_loop" in agent.list_skills():
        print("\nRunning claude_reasoning_loop skill...")
        try:
            result = agent.run(
                "claude_reasoning_loop",
                task_description="Create a marketing plan for a new product launch",
                context="Product is a productivity app for remote teams"
            )
            print(f"Plan created at: {result}")
        except Exception as e:
            print(f"Error running skill: {e}")
            print("Make sure ANTHROPIC_API_KEY is set in your environment")
    else:
        print("claude_reasoning_loop skill not found. Make sure the skills are loaded properly.")