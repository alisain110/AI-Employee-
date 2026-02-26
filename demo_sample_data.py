"""
Demo script to simulate the AI Employee Vault system with sample data
This demonstrates how the orchestrator and watchers would process real data
"""

import os
import sys
import time
from datetime import datetime
import json
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, ".")

def create_sample_data():
    """Create sample data that would be processed by the system"""
    print("Creating sample data for AI Employee Vault system...")

    # Create sample directories if they don't exist
    dirs = ["Inbox", "Needs_Action", "Done", "Pending_Approval", "Approved", "Plans", "Logs"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)

    # Create sample incoming data for orchestrator to process
    inbox_files = [
        {
            "filename": "new_client_inquiry.md",
            "content": """---
type: client_request
priority: high
date: 2026-02-22
---

# New Client Inquiry

A potential client has reached out requesting a custom business automation solution.

## Details
- Client: TechCorp Solutions
- Budget: $50,000 - $75,000
- Timeline: 3 months
- Requirements: CRM integration, automated reporting, workflow management

## Next Steps
Please create a comprehensive proposal and schedule a call with the client.
"""
        },
        {
            "filename": "quarterly_review_task.md",
            "content": """---
type: business_task
priority: medium
date: 2026-02-22
---

# Quarterly Review Task

Please analyze the business performance for Q1 2026 and create a strategic plan for Q2.

## Requirements
- Review financial metrics
- Analyze market trends
- Identify growth opportunities
- Create action plan
"""
        }
    ]

    # Create sample Gmail-like data (simulating what Gmail watcher would detect)
    gmail_simulated_data = {
        "subject": "New business opportunity from TechCorp",
        "from": "contact@techcorp.com",
        "date": "2026-02-22T10:30:00Z",
        "snippet": "We're looking for help building a custom automation solution for our business..."
    }

    # Create sample WhatsApp-like data (simulating what WhatsApp watcher would detect)
    whatsapp_simulated_data = {
        "chat_name": "Sales Team",
        "sender": "John Smith",
        "message": "Just got off the call with TechCorp - they're very interested in our automation services. Need to prepare a proposal.",
        "timestamp": "2026-02-22T11:15:00"
    }

    # Create sample LinkedIn-like data (simulating what LinkedIn watcher would detect)
    linkedin_simulated_data = {
        "type": "notification",
        "content": "John Doe has mentioned you in a comment on your recent post about AI automation",
        "timestamp": "2026-02-22T09:45:00"
    }

    # Write sample inbox files
    for file_data in inbox_files:
        file_path = Path("Inbox") / file_data["filename"]
        file_path.write_text(file_data["content"])
        print(f"Created sample file: {file_path}")

    # Create a sample dashboard
    dashboard_content = f"""# AI Employee Vault Dashboard

## Executive Summary
Welcome to your AI Employee dashboard. This system monitors your personal and business affairs 24/7.

## System Status
- **Date:** {datetime.now().strftime('%Y-%m-%d')}
- **AI Employee Status:** Active
- **Last Processed:** {datetime.now().strftime('%H:%M:%S')}
- **System Uptime:** 0 hours

## Current Services
- Platinum Orchestrator: Running
- Gmail Watcher: Running
- WhatsApp Watcher: Running
- LinkedIn Watcher: Running

## Recent Activity
- {datetime.now().strftime('%H:%M:%S')} - System initialized
- 10:30:00 - New email from contact@techcorp.com
- 11:15:00 - WhatsApp message received from Sales Team
- 09:45:00 - LinkedIn notification received

## System Health
- Overall Status: Excellent
- Active Services: 4/4
- Memory Usage: 45%
- CPU Usage: 12%

## Quick Stats
- Files in Inbox: {len(list(Path("Inbox").glob('*.md')))}
- Files in Needs_Action: 0
- Files in Approved: 0
- Files in Done: 0
- Pending Approvals: 0

## Next Actions
- Monitor for new files in Inbox
- Process any high-priority tasks first
- Continue following Company_Handbook.md guidelines
"""

    Path("Dashboard.md").write_text(dashboard_content)
    print("Created sample Dashboard.md")

    # Create a sample mcp_endpoints.json for the orchestrator
    mcp_config = {
        "social_mcp": {
            "url": "http://localhost:8001",
            "endpoints": {
                "facebook_post": "/facebook/post",
                "x_post": "/x/post",
                "generate_facebook_summary": "/social/summary/facebook",
                "generate_instagram_summary": "/social/summary/instagram",
                "generate_x_summary": "/social/summary/x"
            },
            "auth_required": True,
            "api_key_env": "SOCIAL_MCP_API_KEY"
        }
    }

    Path("mcp_endpoints.json").write_text(json.dumps(mcp_config, indent=2))
    print("Created sample mcp_endpoints.json")

    return gmail_simulated_data, whatsapp_simulated_data, linkedin_simulated_data

def simulate_orchestrator_processing():
    """Simulate what happens when orchestrator processes the sample data"""
    print("\n" + "="*60)
    print("SIMULATING ORCHESTRATOR PROCESSING...")
    print("="*60)

    inbox_files = list(Path("Inbox").glob("*.md"))

    if not inbox_files:
        print("No files found in Inbox to process")
        return

    print(f"Found {len(inbox_files)} file(s) in Inbox to process")

    for file_path in inbox_files:
        print(f"\nProcessing: {file_path.name}")

        # Read the file content
        content = file_path.read_text()
        print(f"  Content preview: {content[:100]}...")

        # Simulate what orchestrator would do
        print("  - Analyzing content with Claude reasoning...")
        print("  - Determining appropriate action...")

        # For our sample files, the orchestrator would create plans
        if "client" in content.lower():
            print("  - Identified as client inquiry - creating proposal plan...")
        elif "review" in content.lower():
            print("  - Identified as quarterly review - creating analysis plan...")

        print("  - Creating action plan...")
        print(f"  - Moving {file_path.name} to Needs_Action folder")

        # Move to Needs_Action (simulating orchestrator behavior)
        new_path = Path("Needs_Action") / file_path.name

        # Check if destination file already exists and handle it
        if new_path.exists():
            # If it exists, we'll skip the rename to avoid the error
            print(f"  - File {new_path.name} already exists in Needs_Action, skipping move")
        else:
            file_path.rename(new_path)
            print(f"  - Moved to: {new_path}")

        # Create a sample plan
        plan_content = f"""---
type: plan
created: {datetime.now().isoformat()}
status: pending
original_file: {file_path.name}
---

# Plan for {file_path.name.replace('.md', '').replace('_', ' ').title()}

## Executive Summary
This plan addresses the request from the incoming file: {file_path.name}

## Task Breakdown
1. Analyze the request details
2. Research client requirements
3. Create detailed proposal
4. Schedule follow-up meeting
5. Deliver final solution

## Timeline Estimation
- Analysis: 1 day
- Research: 2 days
- Proposal Creation: 3 days
- Implementation: 1-3 months (depending on scope)

## Resource Requirements
- Business Analyst: 2 days
- Technical Lead: 3 days
- Development Team: 1-12 weeks

## Risk Assessment
- Client budget constraints
- Timeline feasibility
- Technical complexity

## Success Criteria
- Client satisfaction
- Project completion within timeline
- Budget adherence

## Next Steps
1. Review this plan with stakeholders
2. Assign team members
3. Begin initial analysis
"""

        plan_filename = f"PLAN_{file_path.stem}.md"
        plan_path = Path("Plans") / plan_filename
        plan_path.write_text(plan_content)
        print(f"  - Created plan: {plan_path}")

        print("  [OK] Processing completed")

def simulate_watcher_behavior():
    """Simulate what watchers would do with their sample data"""
    print("\n" + "="*60)
    print("SIMULATING WATCHER BEHAVIOR...")
    print("="*60)

    # Create session directories if they don't exist
    Path("gmail_session").mkdir(exist_ok=True)
    Path("whatsapp_session").mkdir(exist_ok=True)
    Path("linkedin_session").mkdir(exist_ok=True)

    print("\nGmail Watcher Simulation:")
    print("  - Monitoring for new emails...")
    print("  - Found new email: 'New business opportunity from TechCorp'")
    print("  - Processing through Claude reasoning loop...")
    print("  - Generated follow-up task: Create response to TechCorp inquiry")
    print("  - Added to Inbox for orchestrator processing")

    print("\nWhatsApp Watcher Simulation:")
    print("  - Monitoring for new messages...")
    print("  - Found message in 'Sales Team': 'Just got off the call with TechCorp...'")
    print("  - Processing through Claude reasoning loop...")
    print("  - Generated action: Prioritize TechCorp proposal preparation")
    print("  - Added to Needs_Action for immediate attention")

    print("\nLinkedIn Watcher Simulation:")
    print("  - Monitoring for notifications...")
    print("  - Found notification: 'John Doe mentioned you in a comment...'")
    print("  - Processing through Claude reasoning loop...")
    print("  - Generated response: Send personalized LinkedIn message to John Doe")
    print("  - Created follow-up task in Plans directory")

def show_system_status():
    """Show the current status of the system after processing"""
    print("\n" + "="*60)
    print("SYSTEM STATUS AFTER PROCESSING")
    print("="*60)

    # Count files in each directory
    inbox_count = len(list(Path("Inbox").glob('*')))
    needs_action_count = len(list(Path("Needs_Action").glob('*')))
    done_count = len(list(Path("Done").glob('*')))
    pending_approval_count = len(list(Path("Pending_Approval").glob('*')))
    plans_count = len(list(Path("Plans").glob('*.md')))

    print(f"[INBOX] Inbox: {inbox_count} files")
    print(f"[NEEDS] Needs_Action: {needs_action_count} files")
    print(f"[DONE] Done: {done_count} files")
    print(f"[PEND] Pending Approval: {pending_approval_count} files")
    print(f"[PLAN] Plans Created: {plans_count} files")

    print(f"\n[PLAN] Plans Directory Contents:")
    for plan_file in Path("Plans").glob("*.md"):
        print(f"  - {plan_file.name}")

    print(f"\n[NEEDS] Needs_Action Directory Contents:")
    for file in Path("Needs_Action").glob('*'):
        print(f"  - {file.name}")

    # Show updated dashboard
    if Path("Dashboard.md").exists():
        dashboard = Path("Dashboard.md").read_text()
        # Print just the stats part
        lines = dashboard.split('\n')
        print(f"\n[DASH] Current Dashboard Stats:")
        for line in lines:
            if any(stat in line for stat in ["Files in Inbox:", "Files in Needs_Action:",
                                           "Files in Approved:", "Files in Done:",
                                           "Pending Approvals:"]):
                print(f"  {line.strip()}")

def main():
    print("AI EMPLOYEE VAULT - SAMPLE DATA DEMONSTRATION")
    print("=" * 50)

    # Create sample data
    gmail_data, whatsapp_data, linkedin_data = create_sample_data()

    # Simulate orchestrator processing
    simulate_orchestrator_processing()

    # Simulate watcher behavior
    simulate_watcher_behavior()

    # Show final system status
    show_system_status()

    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE!")
    print("="*60)
    print("This simulation shows how the AI Employee Vault system")
    print("would process real data in a 24/7 operation:")
    print("• Orchestrator monitors file system and processes tasks")
    print("• Watchers monitor external services (email, WhatsApp, LinkedIn)")
    print("• All processing goes through Claude reasoning loop")
    print("• Plans and actions are systematically organized")
    print("• System maintains dashboard and status tracking")

if __name__ == "__main__":
    main()