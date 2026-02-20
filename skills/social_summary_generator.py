"""
Social Summary Generator Agent Skill
Fetches last 7 days posts + comments + reactions and generates summary using Claude
"""
import os
import json
import requests
import datetime
from typing import Dict, List, Any
from pathlib import Path
from langchain_core.tools import tool
from anthropic import Anthropic


@tool
def social_summary_generator(platform: str) -> str:
    """
    Generate social media summary from last 7 days of data.

    Args:
        platform (str): Social media platform ("facebook", "instagram", "x")

    Returns:
        str: Path to the generated summary file
    """
    # Validate platform
    valid_platforms = ["facebook", "instagram", "x"]
    if platform.lower() not in valid_platforms:
        return f"Error: Invalid platform. Valid options are: {valid_platforms}"

    platform = platform.lower()

    # Get today's date and 7 days ago
    today = datetime.date.today()
    seven_days_ago = today - datetime.timedelta(days=7)

    # Initialize Anthropic client
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Fetch social media data based on platform
    try:
        if platform == "facebook":
            data = fetch_facebook_data(seven_days_ago, today)
        elif platform == "instagram":
            data = fetch_instagram_data(seven_days_ago, today)
        elif platform == "x":  # X/Twitter
            data = fetch_x_data(seven_days_ago, today)
        else:
            return f"Error: Unsupported platform: {platform}"
    except Exception as e:
        return f"Error fetching {platform} data: {str(e)}"

    # Generate summary using Claude
    try:
        summary = generate_claude_summary(data, platform, seven_days_ago, today)
    except Exception as e:
        return f"Error generating Claude summary: {str(e)}"

    # Save summary to file
    try:
        date_str = today.strftime('%Y-%m-%d')
        summary_dir = Path("Social_Summaries")
        summary_dir.mkdir(exist_ok=True)

        filename = f"{summary_dir}/{date_str}_{platform}_summary.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)

        return f"Social summary saved to: {filename}"
    except Exception as e:
        return f"Error saving summary file: {str(e)}"


def fetch_facebook_data(start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """
    Fetch Facebook data for the given date range
    This is a placeholder implementation - in a real system, you would use the Facebook Graph API
    """
    # Get credentials from environment
    page_id = os.getenv('FB_PAGE_ID')
    access_token = os.getenv('FB_PAGE_ACCESS_TOKEN')

    if not page_id or not access_token:
        # Return mock data for testing
        return {
            "platform": "facebook",
            "period": f"{start_date} to {end_date}",
            "posts": [
                {
                    "id": "post_1",
                    "text": "Great products for you!",
                    "timestamp": str(start_date + datetime.timedelta(days=1)),
                    "reach": 1200,
                    "engagement": 150,
                    "likes": 100,
                    "comments": 30,
                    "shares": 20,
                    "top_comments": [
                        {"author": "User1", "text": "Love this!", "likes": 5},
                        {"author": "User2", "text": "Great quality", "likes": 3}
                    ]
                }
            ],
            "summary": {
                "total_posts": 1,
                "total_reach": 1200,
                "total_engagement": 150,
                "avg_engagement_rate": 0.125
            }
        }

    # Real implementation would use Facebook Graph API
    # Example: https://graph.facebook.com/v18.0/{page_id}/posts?fields=message,created_time,engagement,comments,likes&since={start_date}&until={end_date}
    # In a real implementation, you would fetch actual data
    posts_url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
    params = {
        'access_token': access_token,
        'fields': 'id,message,created_time,shares,likes.summary(true),comments.summary(true)',
        'since': int(datetime.datetime.combine(start_date, datetime.datetime.min.time()).timestamp()),
        'until': int(datetime.datetime.combine(end_date, datetime.datetime.max.time()).timestamp())
    }

    response = requests.get(posts_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Facebook API error: {response.text}")

    data = response.json()
    posts = data.get('data', [])

    # Process and format the data
    processed_posts = []
    for post in posts:
        # Fetch detailed engagement data for each post
        post_engagement_url = f"https://graph.facebook.com/v18.0/{post['id']}?fields=engagement,shares,likes.summary(true),comments.summary(true)&access_token={access_token}"
        engagement_response = requests.get(post_engagement_url)
        engagement_data = engagement_response.json() if engagement_response.status_code == 200 else {}

        # Fetch top comments
        comments_url = f"https://graph.facebook.com/v18.0/{post['id']}/comments?fields=from,message,like_count&limit=5&access_token={access_token}"
        comments_response = requests.get(comments_url)
        top_comments = []
        if comments_response.status_code == 200:
            comments_data = comments_response.json()
            for comment in comments_data.get('data', []):
                top_comments.append({
                    "author": comment.get('from', {}).get('name', 'Unknown'),
                    "text": comment.get('message', ''),
                    "likes": comment.get('like_count', 0)
                })

        processed_posts.append({
            "id": post.get('id'),
            "text": post.get('message', ''),
            "timestamp": post.get('created_time', ''),
            "reach": 0,  # Facebook doesn't provide reach in public API easily
            "engagement": engagement_data.get('engagement', {}).get('count', 0) if 'engagement' in engagement_data else 0,
            "likes": engagement_data.get('likes', {}).get('summary', {}).get('total_count', 0) if 'likes' in engagement_data else 0,
            "comments": engagement_data.get('comments', {}).get('summary', {}).get('total_count', 0) if 'comments' in engagement_data else 0,
            "shares": engagement_data.get('shares', {}).get('count', 0) if 'shares' in engagement_data else 0,
            "top_comments": top_comments
        })

    total_reach = sum(p.get('reach', 0) for p in processed_posts)
    total_engagement = sum(p.get('engagement', 0) for p in processed_posts)
    avg_engagement_rate = total_engagement / total_reach if total_reach > 0 else 0

    return {
        "platform": "facebook",
        "period": f"{start_date} to {end_date}",
        "posts": processed_posts,
        "summary": {
            "total_posts": len(processed_posts),
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": avg_engagement_rate
        }
    }


def fetch_instagram_data(start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """
    Fetch Instagram data for the given date range
    """
    # Get credentials from environment
    account_id = os.getenv('INSTAGRAM_ACCOUNT_ID')
    access_token = os.getenv('META_ACCESS_TOKEN')

    if not account_id or not access_token:
        # Return mock data for testing
        return {
            "platform": "instagram",
            "period": f"{start_date} to {end_date}",
            "posts": [
                {
                    "id": "insta_post_1",
                    "text": "Great products for you!",
                    "timestamp": str(start_date + datetime.timedelta(days=1)),
                    "reach": 800,
                    "engagement": 100,
                    "likes": 80,
                    "comments": 20,
                    "shares": 5,
                    "top_comments": [
                        {"author": "User1", "text": "Love this!", "likes": 5},
                        {"author": "User2", "text": "Great quality", "likes": 3}
                    ]
                }
            ],
            "summary": {
                "total_posts": 1,
                "total_reach": 800,
                "total_engagement": 100,
                "avg_engagement_rate": 0.125
            }
        }

    # Real implementation would use Instagram Graph API
    # This is a simplified example
    media_url = f"https://graph.facebook.com/v18.0/{account_id}/media"
    params = {
        'access_token': access_token,
        'fields': 'id,caption,like_count,comments_count,timestamp',
        'limit': 50  # Get up to 50 media items
    }

    response = requests.get(media_url, params=params)
    if response.status_code != 200:
        raise Exception(f"Instagram API error: {response.text}")

    data = response.json()
    posts = data.get('data', [])

    # Filter posts to the date range
    filtered_posts = []
    for post in posts:
        post_date = datetime.datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00')).date()
        if start_date <= post_date <= end_date:
            # Get insights for each post
            insights_url = f"https://graph.facebook.com/v18.0/{post['id']}/insights?metric=reach,engagement&access_token={access_token}"
            insights_response = requests.get(insights_url)
            insights_data = insights_response.json() if insights_response.status_code == 200 else {"data": []}

            reach = 0
            engagement = 0
            for insight in insights_data.get('data', []):
                if insight['name'] == 'reach':
                    reach = insight['values'][0]['value'] if insight['values'] else 0
                elif insight['name'] == 'engagement':
                    engagement = insight['values'][0]['value'] if insight['values'] else 0

            # Get comments for the post
            comments_url = f"https://graph.facebook.com/v18.0/{post['id']}/comments?access_token={access_token}&fields=from,message,like_count"
            comments_response = requests.get(comments_url)
            top_comments = []
            if comments_response.status_code == 200:
                comments_data = comments_response.json()
                for comment in comments_data.get('data', []):
                    top_comments.append({
                        "author": comment.get('from', {}).get('name', 'Unknown'),
                        "text": comment.get('message', ''),
                        "likes": comment.get('like_count', 0)
                    })

            filtered_posts.append({
                "id": post.get('id'),
                "text": post.get('caption', ''),
                "timestamp": post.get('timestamp', ''),
                "reach": reach,
                "engagement": engagement,
                "likes": post.get('like_count', 0),
                "comments": post.get('comments_count', 0),
                "shares": 0,  # Instagram doesn't have shares like Facebook
                "top_comments": top_comments
            })

    total_reach = sum(p.get('reach', 0) for p in filtered_posts)
    total_engagement = sum(p.get('engagement', 0) for p in filtered_posts)
    avg_engagement_rate = total_engagement / total_reach if total_reach > 0 else 0

    return {
        "platform": "instagram",
        "period": f"{start_date} to {end_date}",
        "posts": filtered_posts,
        "summary": {
            "total_posts": len(filtered_posts),
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": avg_engagement_rate
        }
    }


def fetch_x_data(start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
    """
    Fetch X (Twitter) data for the given date range
    """
    # Get credentials from environment
    bearer_token = os.getenv('X_BEARER_TOKEN')

    if not bearer_token:
        # Return mock data for testing
        return {
            "platform": "x",
            "period": f"{start_date} to {end_date}",
            "posts": [
                {
                    "id": "x_post_1",
                    "text": "Great products for you! #deals",
                    "timestamp": str(start_date + datetime.timedelta(days=1)),
                    "reach": 2500,
                    "engagement": 45,
                    "likes": 30,
                    "comments": 5,
                    "shares": 10,
                    "top_comments": [
                        {"author": "User1", "text": "Thanks for sharing!", "likes": 2},
                        {"author": "User2", "text": "Interesting", "likes": 1}
                    ]
                }
            ],
            "summary": {
                "total_posts": 1,
                "total_reach": 2500,
                "total_engagement": 45,
                "avg_engagement_rate": 0.018
            }
        }

    # Real implementation would use X API v2
    # Example: Use recent tweets endpoint
    headers = {
        'Authorization': f'Bearer {bearer_token}'
    }

    # Calculate date range in ISO format
    start_str = start_date.isoformat() + 'T00:00:00Z'
    end_str = end_date.isoformat() + 'T23:59:59Z'

    # Get user's tweets
    # Note: In a real scenario, you'd need to get the user ID first
    user_id = os.getenv('X_USER_ID', 'user_123')  # You'd get this from API call in real implementation

    tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    params = {
        'max_results': 100,
        'start_time': start_str,
        'end_time': end_str,
        'tweet.fields': 'public_metrics,created_at,context_annotations'
    }

    response = requests.get(tweets_url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"X API error: {response.text}")

    data = response.json()
    tweets = data.get('data', [])

    # Process tweets
    processed_tweets = []
    for tweet in tweets:
        metrics = tweet.get('public_metrics', {})
        processed_tweets.append({
            "id": tweet.get('id'),
            "text": tweet.get('text', ''),
            "timestamp": tweet.get('created_at', ''),
            "reach": 0,  # X doesn't provide reach directly
            "engagement": metrics.get('like_count', 0) + metrics.get('retweet_count', 0) + metrics.get('reply_count', 0),
            "likes": metrics.get('like_count', 0),
            "comments": metrics.get('reply_count', 0),  # Replies are like comments
            "shares": metrics.get('retweet_count', 0),  # Retweets are like shares
            "top_comments": []  # X API v2 doesn't easily provide top comments without additional calls
        })

    # In a real implementation, you'd need to make additional API calls to get comments/replies

    total_engagement = sum(p.get('engagement', 0) for p in processed_tweets)

    return {
        "platform": "x",
        "period": f"{start_date} to {end_date}",
        "posts": processed_tweets,
        "summary": {
            "total_posts": len(processed_tweets),
            "total_reach": 0,  # X doesn't provide reach in basic API
            "total_engagement": total_engagement,
            "avg_engagement_rate": 0  # Can't calculate without reach
        }
    }


def generate_claude_summary(data: Dict[str, Any], platform: str, start_date: datetime.date, end_date: datetime.date) -> str:
    """
    Generate summary using Claude AI
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Prepare the prompt for Claude
    system_prompt = f"""
    You are an expert social media analyst. Create a comprehensive summary of the performance
    for {platform} over the last 7 days. Include information about reach, engagement,
    top-performing content, audience sentiment, and recommendations for improvement.
    """

    user_prompt = f"""
    Social Media Platform: {platform}
    Date Range: {start_date} to {end_date}

    Data:
    {json.dumps(data, indent=2)}

    Please provide a detailed summary with the following sections:
    1. Executive Summary
    2. Performance Metrics (reach, engagement, engagement rate)
    3. Content Analysis (top-performing posts, themes)
    4. Audience Engagement (comments, sentiment)
    5. Recommendations for improvement

    Format your response as clean Markdown with appropriate headers.
    """

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2000,
        temperature=0.3,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    summary_content = response.content[0].text

    # Create the final summary with metadata
    final_summary = f"""# {platform.title()} Social Media Summary
## {start_date} to {end_date}

{summary_content}

---

*Generated by Claude AI on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Period: {start_date} to {end_date}*
*Platform: {platform}*
"""

    return final_summary