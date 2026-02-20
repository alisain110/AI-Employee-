"""
Script to create an emergency stop file for Ralph mode
"""
import sys
from pathlib import Path

def create_emergency_stop():
    """Create an emergency stop file to halt Ralph loops"""
    vault_path = Path.cwd()
    emergency_stop_file = vault_path / "EMERGENCY_STOP_RALPH"

    if emergency_stop_file.exists():
        print(f"Emergency stop file already exists: {emergency_stop_file}")
        print("Ralph loops will terminate on next iteration check.")
    else:
        emergency_stop_file.write_text("Emergency stop for Ralph mode - created at " + str(Path.cwd()))
        print(f"Created emergency stop file: {emergency_stop_file}")
        print("All Ralph loops will terminate on next iteration check.")

    return str(emergency_stop_file)

def remove_emergency_stop():
    """Remove the emergency stop file to allow Ralph loops to continue"""
    vault_path = Path.cwd()
    emergency_stop_file = vault_path / "EMERGENCY_STOP_RALPH"

    if emergency_stop_file.exists():
        emergency_stop_file.unlink()
        print(f"Removed emergency stop file: {emergency_stop_file}")
        print("Ralph loops can now run again.")
    else:
        print("No emergency stop file exists.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Manage Ralph mode emergency stop')
    parser.add_argument('action', choices=['create', 'remove', 'status'], help='Action to perform')

    args = parser.parse_args()

    if args.action == 'create':
        create_emergency_stop()
    elif args.action == 'remove':
        remove_emergency_stop()
    elif args.action == 'status':
        emergency_stop_file = Path.cwd() / "EMERGENCY_STOP_RALPH"
        if emergency_stop_file.exists():
            print("EMERGENCY_STOP_RALPH file exists - Ralph loops are halted")
        else:
            print("No EMERGENCY_STOP_RALPH file exists - Ralph loops can run")