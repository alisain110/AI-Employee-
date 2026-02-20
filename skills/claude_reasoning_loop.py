"""
Claude Reasoning Loop Skill
"""
import os
from datetime import datetime
from typing import Optional
from pathlib import Path
from langchain_core.tools import tool
from anthropic import Anthropic

@tool
def claude_reasoning_loop(task_description: str, context: Optional[str] = None) -> str:
    """
    Deep reasoning with Claude to create professional Plan.md files for any task or business goal.

    Args:
        task_description (str): The main task or business goal to create a plan for
        context (Optional[str]): Additional context to consider in planning

    Returns:
        str: Path to the created plan file
    """
    # Initialize Anthropic client
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Prepare the prompt for Claude
    system_prompt = """
    You are an expert business analyst and project planner. Create a comprehensive, well-structured plan
    that breaks down the given task into actionable steps. Your output should be professional,
    detailed, and executable. Include considerations for risk management, dependencies,
    resource allocation, and quality measures.
    """

    user_prompt = f"""
    Task: {task_description}

    Context: {context or 'No additional context provided'}

    Please provide a detailed plan with the following sections:
    1. Executive Summary
    2. Task Breakdown (detailed subtasks)
    3. Timeline Estimation
    4. Resource Requirements
    5. Risk Assessment
    6. Dependencies
    7. Success Criteria
    8. Quality Assurance Measures

    Format your response as clean Markdown with appropriate headers.
    """

    try:
        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        plan_content = response.content[0].text
    except Exception as e:
        # Handle API errors gracefully
        plan_content = f"""# ERROR: {str(e)}

Could not generate plan using Claude AI. The plan could not be created due to an API error.

## Original Task
{task_description}

## Context
{context or 'No context provided'}

## Next Steps
- Verify that ANTHROPIC_API_KEY is set correctly in environment variables
- Check API connection and credentials
- Try running the task again later"""

    # Create plans directory if it doesn't exist
    plans_dir = Path("./plans")
    plans_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    plan_filename = f"Plan_{timestamp}.md"
    plan_path = plans_dir / plan_filename

    # Write the plan to the individual file
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write(f"# Plan: {task_description}\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(plan_content)

    # Append to the main Plan.md file
    main_plan_path = plans_dir / "Plan.md"
    with open(main_plan_path, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n")
        f.write(f"# Plan: {task_description}\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(plan_content)
        f.write(f"\n---\n")

    return str(plan_path)