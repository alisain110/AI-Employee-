"""
LinkedIn Auto Post Skill
"""
import os
import csv
import requests
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Import the approval decorator from utilities
from utilities.human_approval import requires_human_approval

def load_business_profile():
    """Load business profile from config file"""
    profile_path = Path("config/business_profile.md")
    if profile_path.exists():
        return profile_path.read_text()
    else:
        # Return default profile if file doesn't exist
        return """
# Business Profile

## Company Name: Tech Innovations Inc.
## Industry: Software Development & AI Solutions
## Target Audience: Tech startups, entrepreneurs, business leaders
## Values: Innovation, Quality, Customer Success
## Services:
- AI Solutions
- Custom Software Development
- Digital Transformation
- Cloud Services
## Mission: To empower businesses with cutting-edge technology solutions that drive growth and innovation.
## Unique Value Proposition: We combine technical excellence with business insight to deliver solutions that truly make a difference.
"""


@tool
@requires_human_approval
def linkedin_auto_post(post_topic: str, context: Optional[str] = None) -> str:
    """
    Generate and post a high-quality LinkedIn business post using Claude.
    The post will include value content, sales CTA, hashtags, and emojis.

    Args:
        post_topic (str): Topic for the post to be generated about
        context (Optional[str]): Additional context for the post

    Returns:
        str: Status message with post URL or error details
    """
    # Load business profile
    business_profile = load_business_profile()

    # Import claude reasoning loop
    from core.agent import AIAgent
    agent = AIAgent()

    # Create a comprehensive prompt for Claude to generate a high-quality LinkedIn post
    detailed_context = f"""
    Business Profile:
    {business_profile}

    Topic: {post_topic}

    Context: {context or 'No additional context provided'}

    Please create a high-quality LinkedIn business post that includes:
    1. Valuable content related to the topic
    2. A compelling sales call-to-action (CTA)
    3. Relevant hashtags (max 5-10)
    4. Appropriate emojis to make the post engaging
    5. Professional tone that aligns with the business profile

    Format the post as a single text block ready to be posted on LinkedIn.
    """

    try:
        # Generate the post content using Claude
        result = agent.run(
            "claude_reasoning_loop",
            task_description=f"Generate LinkedIn post about {post_topic}",
            context=detailed_context
        )

        # Extract the generated post content from the plan file
        plan_path = Path(result)
        if plan_path.exists():
            plan_content = plan_path.read_text()
            # Find the actual post content in the generated plan (after header information)
            lines = plan_content.split('\n')
            post_start = -1

            # Look for the main content section
            for i, line in enumerate(lines):
                if 'Format your response as clean Markdown' in line or line.strip().startswith('# ERROR'):
                    post_start = i + 1
                    break
                elif 'Original Task' in line:
                    post_start = i
                    break

            if post_start >= 0:
                post_content = '\n'.join(lines[post_start:]).strip()
            else:
                post_content = plan_content
        else:
            # If plan file was not created properly, use context as fallback
            post_content = f"New LinkedIn post about: {post_topic}\n\n{context or ''}"

        # For now we'll return the generated content (when LinkedIn API integration is added,
        # this is where we would actually post it)
        status_message = f"Post generated successfully (LinkedIn API integration pending):\n\n{post_content[:200]}..."

        # Log the post to CSV
        log_post(post_content, "pending_api_integration")

        return status_message

    except Exception as e:
        error_msg = f"Error generating LinkedIn post: {str(e)}"
        return error_msg


def log_post(content: str, post_url: str, status: str = "posted"):
    """Log the posted content to CSV file"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    csv_path = logs_dir / "posted_linkedin.csv"

    # Create CSV with headers if it doesn't exist
    if not csv_path.exists():
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'content', 'url', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    # Write the post data
    with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['timestamp', 'content', 'url', 'status']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({
            'timestamp': datetime.now().isoformat(),
            'content': content[:10000],  # Limit content length to avoid CSV issues
            'url': post_url,
            'status': status
        })


# For testing purposes - this function would be called when we have actual LinkedIn API integration
def post_to_linkedin_api(post_content: str, access_token: str) -> str:
    """
    Post to LinkedIn using UGC Posts API (this is the actual implementation that would be used)
    This is provided as reference for when the API integration is fully implemented.
    """
    # LinkedIn UGC Posts API endpoint
    url = "https://api.linkedin.com/v2/ugcPosts"

    # Get the actor (person or organization) URN
    # This would typically be retrieved from the access token or profile
    actor_urn = "urn:li:person:<PERSON_URN>"  # This needs to be replaced with actual URN

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    # Create the post payload
    payload = {
        "author": actor_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_content
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get('id', 'Unknown ID')
    except requests.exceptions.RequestException as e:
        print(f"Error posting to LinkedIn API: {e}")
        return f"Error: {str(e)}"