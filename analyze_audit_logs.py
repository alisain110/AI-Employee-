"""
Script to analyze audit log files
"""
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

def analyze_audit_logs(days_back=1):
    """Analyze audit logs for the specified number of days"""
    print(f"Analyzing audit logs for the last {days_back} day(s)...")

    # Find audit log files
    today = datetime.now().date()
    log_files = []

    for i in range(days_back):
        date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        log_file = Path('Logs') / f'audit_{date_str}.log'
        if log_file.exists():
            log_files.append(log_file)

    if not log_files:
        print("No audit log files found!")
        return

    # Analyze each log file
    total_entries = 0
    actors = Counter()
    actions = Counter()
    errors = []
    success_rate = defaultdict(lambda: {'total': 0, 'success': 0})

    for log_file in log_files:
        print(f"\nAnalyzing: {log_file.name}")

        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    total_entries += 1

                    # Count actors
                    actor = entry.get('actor', 'unknown')
                    actors[actor] += 1

                    # Count actions
                    action = entry.get('action', 'unknown')
                    actions[action] += 1

                    # Track success/failure
                    is_success = entry.get('success', True)
                    success_rate[actor]['total'] += 1
                    if is_success:
                        success_rate[actor]['success'] += 1

                    # Collect errors
                    if not is_success and entry.get('error'):
                        errors.append({
                            'timestamp': entry.get('timestamp'),
                            'actor': actor,
                            'action': action,
                            'error': entry['error'],
                            'details': entry.get('details', {})
                        })

                except json.JSONDecodeError as e:
                    print(f"  Warning: Could not parse line {line_num}: {e}")

    print(f"\n{'='*60}")
    print("AUDIT LOG ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total entries analyzed: {total_entries}")

    print(f"\nTop Actors:")
    for actor, count in actors.most_common():
        rate = (success_rate[actor]['success'] / success_rate[actor]['total'] * 100) if success_rate[actor]['total'] > 0 else 0
        print(f"  {actor}: {count} entries ({rate:.1f}% successful)")

    print(f"\nTop Actions:")
    for action, count in actions.most_common():
        print(f"  {action}: {count} occurrences")

    print(f"\nRecent Errors:")
    if errors:
        for error in errors[-10:]:  # Show last 10 errors
            print(f"  {error['timestamp']} - {error['actor']}.{error['action']}: {error['error'][:100]}")
    else:
        print("  No errors found!")

    print(f"\nError Summary:")
    print(f"  Total errors: {len(errors)}")
    print(f"  Success rate: {((total_entries - len(errors)) / total_entries * 100):.1f}% if {total_entries > 0}")

def show_recent_activity(hours=24):
    """Show recent activity from audit logs"""
    print(f"\nRecent activity (last {hours} hours):")
    print("-" * 50)

    today = datetime.now().date()
    log_files = []

    # Look at current and previous day
    for i in range(2):
        date_str = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        log_file = Path('Logs') / f'audit_{date_str}.log'
        if log_file.exists():
            log_files.append(log_file)

    recent_entries = []

    for log_file in log_files:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                    timestamp_str = entry.get('timestamp', '')
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        if (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds() < hours * 3600:
                            recent_entries.append(entry)
                except:
                    continue

    # Sort by timestamp
    recent_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    for entry in recent_entries[:20]:  # Show last 20 entries
        timestamp = entry.get('timestamp', '')[:19].replace('T', ' ')
        actor = entry.get('actor', 'unknown')
        action = entry.get('action', 'unknown')
        success = "[OK]" if entry.get('success', True) else "[ERR]"
        print(f"  {timestamp} {success} {actor}.{action}")

def main():
    print("AI Employee Vault - Audit Log Analyzer")
    print("=" * 50)

    analyze_audit_logs(1)  # Analyze last day
    show_recent_activity(24)  # Show last 24 hours

    print(f"\n{'='*50}")
    print("Analysis complete!")

if __name__ == "__main__":
    main()