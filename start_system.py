#!/usr/bin/env python3
"""
Complete startup script for AI Employee System
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Main entry point for the AI Employee system"""
    print("AI Employee System - Complete Startup")
    print("=" * 50)

    # Check that environment file exists
    if not Path('.env').exists():
        print("Warning: .env file not found. Creating from example...")
        if Path('.env.example').exists():
            with open('.env.example', 'r') as src, open('.env', 'w') as dst:
                dst.write(src.read())
            print("Created .env from .env.example. Please update with your credentials.")
        else:
            print("No .env.example file found. Please create .env with required variables.")

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    print("Starting AI Employee System...")
    print("This will start:")
    print("- MCP Server (port 8001)")
    print("- All Watchers (Gmail, WhatsApp, LinkedIn)")
    print("- Scheduler with automated tasks")
    print("- AI Agent with all skills")
    print()
    print("Press Ctrl+C to stop the system")
    print("=" * 50)

    try:
        # Import and run the main runner
        from main_runner import AIEmployeeMainRunner
        runner = AIEmployeeMainRunner()
        runner.start()
    except KeyboardInterrupt:
        print("\n\nSystem interrupted by user.")
    except Exception as e:
        print(f"\nError starting system: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()