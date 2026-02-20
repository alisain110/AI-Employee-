"""
Facebook Poster Agent Skill
Posts text + optional image to Facebook Page (not personal profile)
Uses meta-business-sdk and requires approval for sales-related content
"""
import os
import json
import requests
from typing import Optional
from pathlib import Path
from langchain_core.tools import tool

def create_approval_request(action_data: dict):
    """Create an approval request for sensitive actions"""
    pending_approval_dir = Path("Pending_Approval")
    pending_approval_dir.mkdir(exist_ok=True)

    timestamp = action_data.get('timestamp', '')
    filename = f"facebook_post_approval_{timestamp}.json"
    filepath = pending_approval_dir / filename

    approval_data = {
        "timestamp": action_data.get('timestamp'),
        "action": "facebook_post",
        "details": action_data,
        "status": "pending",
        "approved": False
    }

    with open(filepath, 'w') as f:
        json.dump(approval_data, f, indent=2)

    return str(filepath)


@tool
def facebook_poster(
    text: str,
    image_url: Optional[str] = None,
    page_id: Optional[str] = None,
    access_token: Optional[str] = None
) -> str:
    """
    Post text + optional image to Facebook Page (not personal profile).

    Args:
        text (str): The text content to post
        image_url (Optional[str]): URL of image to attach (optional)
        page_id (Optional[str]): Facebook Page ID (defaults to env var)
        access_token (Optional[str]): Facebook access token (defaults to env var)

    Returns:
        str: Status message about the post or approval request
    """
    # Get credentials from environment if not provided
    if access_token is None:
        access_token = os.getenv('FB_PAGE_ACCESS_TOKEN')
    if page_id is None:
        page_id = os.getenv('FB_PAGE_ID')

    # Validate required parameters
    if not access_token:
        return "Error: Facebook access token not provided and not found in environment variables"
    if not page_id:
        return "Error: Facebook page ID not provided and not found in environment variables"

    # Check if the post is sales-related (contains keywords)
    sales_keywords = ['buy', 'sale', 'discount', 'offer', 'deal', 'price', 'shop', 'order', 'purchase', 'promo']
    is_sales_related = any(keyword in text.lower() for keyword in sales_keywords)

    # For sales-related posts, create an approval request
    if is_sales_related:
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

        approval_data = {
            "timestamp": timestamp,
            "page_id": page_id,
            "text": text,
            "image_url": image_url,
            "is_sales_related": True
        }

        approval_file = create_approval_request(approval_data)
        return f"Sales-related post requested. Approval needed: {approval_file}"

    # For non-sales posts, post directly to Facebook
    try:
        # First, get the page access token by posting as the page
        page_token_url = f"https://graph.facebook.com/v18.0/{page_id}?fields=access_token&access_token={access_token}"
        page_response = requests.get(page_token_url)

        if page_response.status_code != 200:
            return f"Error getting page access token: {page_response.text}"

        page_data = page_response.json()
        if 'access_token' not in page_data:
            return f"Error: Could not retrieve page access token. Make sure the user token has pages_manage_posts permission and the user is a page admin/moderator."

        page_access_token = page_data['access_token']

        # Prepare the post data
        post_url = f"https://graph.facebook.com/v18.0/{page_id}/photos" if image_url else f"https://graph.facebook.com/v18.0/{page_id}/feed"

        post_data = {
            'message': text,
            'access_token': page_access_token
        }

        if image_url and not image_url.strip().startswith('http'):
            return "Error: Invalid image URL format"

        # Make the post
        if image_url:
            post_data['url'] = image_url
            response = requests.post(post_url, data=post_data)
        else:
            response = requests.post(post_url, data=post_data)

        if response.status_code == 200:
            result = response.json()
            post_id = result.get('id', 'unknown')

            # Log the action
            logs_dir = Path("Logs")
            logs_dir.mkdir(exist_ok=True)

            import datetime
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "action": "facebook_post",
                "post_id": post_id,
                "page_id": page_id,
                "sales_related": False
            }

            with open(logs_dir / "social_media_actions.log", 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

            return f"Successfully posted to Facebook Page. Post ID: {post_id}"
        else:
            return f"Error posting to Facebook: {response.text}"

    except Exception as e:
        return f"Error in Facebook poster: {str(e)}"