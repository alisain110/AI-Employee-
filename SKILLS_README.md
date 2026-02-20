# AI Employee Skills System

This system implements AI functionality as "Agent Skills" - reusable tools that can be dynamically loaded by the main agent.

## Directory Structure

```
skills/
├── claude_reasoning_loop.py    # Claude-powered planning skill
├── __init__.py                 # Module initialization
core/
├── agent.py                    # Main agent that loads skills
├── __init__.py                 # Module initialization
plans/                          # Generated plans directory
├── Plan.md                     # Main consolidated plan file
├── Plan_YYYY-MM-DD_HH-MM.md    # Individual plan files
```

## Available Skills

### `claude_reasoning_loop`
- **Purpose**: Creates detailed professional plans using Claude 3.5 Sonnet
- **Function**: `claude_reasoning_loop(task_description: str, context: Optional[str] = None)`
- **Output**: Creates markdown plan files in the `plans/` directory

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Anthropic API key:
```bash
# Copy the example file
cp .env.example .env
# Edit .env and add your API key
```

3. Run the agent:
```bash
python run_agent.py
```

## Creating New Skills

To create a new skill:

1. Create a new Python file in the `skills/` folder
2. Import the `tool` decorator from `langchain_core.tools`
3. Decorate your function with `@tool`
4. Include proper type hints and documentation
5. The agent will automatically load it

### Example Skill Template:

```python
from langchain_core.tools import tool
from typing import Optional

@tool
def my_new_skill(input_parameter: str, optional_parameter: Optional[str] = None) -> str:
    """
    Brief description of what this skill does.

    Args:
        input_parameter (str): Description of the main parameter
        optional_parameter (Optional[str]): Description of optional parameter

    Returns:
        str: Description of what the function returns
    """
    # Your skill implementation here
    result = f"Processed {input_parameter} with {optional_parameter}"
    return result
```

## Usage Examples

### Direct Usage:
```python
from core.agent import AIAgent

agent = AIAgent()
result = agent.run(
    "claude_reasoning_loop",
    task_description="Create a marketing plan for a new product",
    context="Product is a productivity app for remote teams"
)
```

### In Claude Conversations:
When acting as the Silver Tier AI Employee, if you encounter a complex task, you can call:
```
claude_reasoning_loop(task_description="Create detailed plan for task X", context="Relevant context")
```

The agent will automatically generate a comprehensive plan and save it to the plans folder.

## Security Notes

- Store API keys securely in environment variables
- Never commit API keys to version control
- The system follows proper file handling practices
- All generated plans are saved locally