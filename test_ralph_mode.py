"""
Test script to demonstrate Ralph Wiggum mode functionality
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_ralph_mode_detection():
    """Test that the orchestrator can detect Ralph mode in task files"""
    print("Testing Ralph mode detection...")

    from orchestrator_gold import RalphOrchestrator

    # Create a temporary task file with Ralph mode
    vault_path = Path.cwd()
    orchestrator = RalphOrchestrator(str(vault_path))

    # Test content with Ralph mode
    ralph_task_content = """---
title: Test Ralph Task
---

# Test Task

## Configuration
mode: ralph

## Description
This task should trigger Ralph mode.
"""

    # Parse the configuration
    config = orchestrator.parse_task_config(ralph_task_content)

    if config.mode == 'ralph':
        print("[SUCCESS] Ralph mode detected correctly")
        print(f"Config: mode={config.mode}, max_iterations={config.max_iterations}, max_duration_minutes={config.max_duration_minutes}")
        return True
    else:
        print("[ERROR] Ralph mode not detected")
        return False

def test_normal_mode_detection():
    """Test that normal mode is detected when Ralph mode is not specified"""
    print("\nTesting normal mode detection...")

    from orchestrator_gold import RalphOrchestrator

    vault_path = Path.cwd()
    orchestrator = RalphOrchestrator(str(vault_path))

    # Test content without Ralph mode
    normal_task_content = """---
title: Test Normal Task
---

# Test Task

## Description
This task should run in normal mode.
"""

    # Parse the configuration
    config = orchestrator.parse_task_config(normal_task_content)

    if config.mode == 'normal':
        print("[SUCCESS] Normal mode detected correctly")
        print(f"Config: mode={config.mode}")
        return True
    else:
        print("[ERROR] Normal mode not detected correctly")
        return False

def show_ralph_features():
    """Show the key features of Ralph mode"""
    print("\n" + "="*60)
    print("RALPH WIGGUM MODE FEATURES")
    print("="*60)
    print("• Iterative processing: while not done and iterations < 15")
    print("• Fresh context per iteration (no huge history)")
    print("• Tool execution with MCP endpoint routing")
    print("• Safety features:")
    print("  - Max 15 iterations")
    print("  - 2-hour time cap")
    print("  - Emergency stop file detection")
    print("• JSON output: thought, tool_calls, next_action")
    print("• Log generation: /Ralph_Logs/{task_id}_step_N.md")
    print("• State management: DONE/CONTINUE/FAILED/NEEDS_HUMAN")
    print("• Human approval requests go to Pending_Approval folder")
    print("="*60)

if __name__ == "__main__":
    print("Testing Ralph Wiggum Mode Implementation")
    print("="*50)

    success1 = test_ralph_mode_detection()
    success2 = test_normal_mode_detection()

    show_ralph_features()

    print(f"\nResults:")
    print(f"- Ralph mode detection: {'[SUCCESS]' if success1 else '[ERROR]'}")
    print(f"- Normal mode detection: {'[SUCCESS]' if success2 else '[ERROR]'}")

    if success1 and success2:
        print(f"\n[SUCCESS] All tests passed! Ralph Wiggum mode is ready.")
    else:
        print(f"\n[ERROR] Some tests failed.")