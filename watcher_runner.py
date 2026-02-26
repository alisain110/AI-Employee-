#!/usr/bin/env python3
"""
Watcher Runner Script
This script runs individual watchers based on command line arguments.
"""
import sys
import time
from core.agent import AIAgent

def run_watcher(watcher_type):
    """Run a specific watcher"""
    agent = AIAgent()

    try:
        if watcher_type == 'gmail':
            result = agent.run('gmail_watcher_skill', action='start')
            print(f"Gmail watcher result: {result}")
        elif watcher_type == 'whatsapp':
            result = agent.run('whatsapp_watcher_skill', action='start')
            print(f"WhatsApp watcher result: {result}")
        elif watcher_type == 'linkedin':
            result = agent.run('linkedin_watcher_skill', action='start')
            print(f"LinkedIn watcher result: {result}")
        else:
            print(f"Unknown watcher type: {watcher_type}")
            return False

        print(f"{watcher_type} watcher started successfully. Running indefinitely...")

        # Keep the process alive
        while True:
            time.sleep(60)  # Sleep for 1 minute

    except KeyboardInterrupt:
        print(f"Stopping {watcher_type} watcher...")
        try:
            if watcher_type == 'gmail':
                result = agent.run('gmail_watcher_skill', action='stop')
            elif watcher_type == 'whatsapp':
                result = agent.run('whatsapp_watcher_skill', action='stop')
            elif watcher_type == 'linkedin':
                result = agent.run('linkedin_watcher_skill', action='stop')
            print(f"Watcher stopped: {result}")
        except Exception as e:
            print(f"Error stopping watcher: {e}")
    except Exception as e:
        print(f"Error running {watcher_type} watcher: {e}")
        return False

    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python watcher_runner.py <gmail|whatsapp|linkedin>")
        sys.exit(1)

    watcher_type = sys.argv[1]
    success = run_watcher(watcher_type)

    if not success:
        sys.exit(1)