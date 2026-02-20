"""
X Poster and Summary Agent Skill
Posts to X (Twitter) and generates weekly summaries using X API v2
"""
import os
import json
import requests
import tweepy
import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_core.tools import tool
from anthropic import Anthropic


def create_approval_request(action_data: dict):
    """Create an approval request for sensitive actions"""
    pending_approval_dir = Path("Pending_Approval")
    pending_approval_dir.mkdir(exist_ok=True)

    timestamp = action_data.get('timestamp', '')
    filename = f"x_post_approval_{timestamp}.json"
    filepath = pending_approval_dir / filename

    approval_data = {
        "timestamp": action_data.get('timestamp'),
        "action": "x_post",
        "details": action_data,
        "status": "pending",
        "approved": False
    }

    with open(filepath, 'w') as f:
        json.dump(approval_data, f, indent=2)

    return str(filepath)


@tool
def post_tweet(text: str, media_ids: Optional[List[str]] = None, reply_to: Optional[str] = None) -> str:
    """
    Post a tweet to X (Twitter) with optional media and reply functionality.

    Args:
        text (str): The text content of the tweet
        media_ids (Optional[List[str]]): List of media IDs to attach (optional)
        reply_to (Optional[str]): Tweet ID to reply to (optional)

    Returns:
        str: Status message about the post or approval request
    """
    # Check if the post is sensitive (contains keywords that might be problematic)
    sensitive_keywords = ['buy', 'sale', 'discount', 'offer', 'deal', 'price', 'shop', 'order', 'purchase', 'promo', 'hate', 'angry', 'kill', 'harm']
    is_sensitive = any(keyword in text.lower() for keyword in sensitive_keywords)

    # For sensitive posts, create an approval request
    if is_sensitive:
        import datetime as dt
        timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')

        approval_data = {
            "timestamp": timestamp,
            "action": "post_tweet",
            "text": text,
            "media_ids": media_ids,
            "reply_to": reply_to,
            "is_sensitive": True
        }

        approval_file = create_approval_request(approval_data)
        return f"Sensitive tweet requested. Approval needed: {approval_file}"

    # Get credentials from environment
    bearer_token = os.getenv('X_BEARER_TOKEN')
    consumer_key = os.getenv('X_API_KEY')
    consumer_secret = os.getenv('X_API_SECRET')
    access_token = os.getenv('X_ACCESS_TOKEN')
    access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')

    # Validate required parameters
    if not all([bearer_token, consumer_key, consumer_secret, access_token, access_token_secret]):
        return "Error: X API credentials not found in environment variables"

    try:
        # Initialize tweepy client with OAuth 2.0 Bearer Token + OAuth 1.0a User Context
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )

        # Prepare tweet parameters
        tweet_params = {"text": text}

        if reply_to:
            tweet_params["in_reply_to_tweet_id"] = reply_to

        if media_ids:
            # Note: For media, we need to use the legacy API with tweepy.API
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)

            # Upload media and get media IDs
            media_ids_to_use = []
            for media_url in media_ids:
                if media_url.startswith('http'):
                    # For URLs, we can't directly upload from URL with tweepy
                    # This would require downloading the file first, so we'll skip this approach
                    # and assume media_ids are pre-uploaded media IDs
                    media_ids_to_use.append(int(media_url))
                else:
                    media_ids_to_use.append(int(media_url))

            if media_ids_to_use:
                tweet_params["media_ids"] = media_ids_to_use

        # Post the tweet using tweepy
        response = client.create_tweet(**tweet_params)

        if response.data and 'id' in response.data:
            tweet_id = response.data['id']

            # Log the action
            logs_dir = Path("Logs")
            logs_dir.mkdir(exist_ok=True)

            import datetime as dt
            log_entry = {
                "timestamp": dt.datetime.now().isoformat(),
                "action": "x_post",
                "tweet_id": tweet_id,
                "text": text,
                "sensitive": False
            }

            with open(logs_dir / "social_media_actions.log", 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

            return f"Successfully posted to X. Tweet ID: {tweet_id}"
        else:
            return f"Error posting to X: {response}"

    except tweepy.TooManyRequests:
        return "Error: Rate limit exceeded. Please wait before posting again."
    except tweepy.Unauthorized:
        return "Error: Unauthorized. Check your X API credentials."
    except Exception as e:
        return f"Error in X poster: {str(e)}"


@tool
def generate_weekly_x_summary() -> str:
    """
    Generate weekly summary of X (Twitter) activity for the last 7 days.

    Fetches user's posts, mentions, and replies, then asks Claude to generate
    a comprehensive summary saved to /Social_Summaries/.

    Returns:
        str: Path to the generated summary file
    """
    # Get credentials from environment
    bearer_token = os.getenv('X_BEARER_TOKEN')
    consumer_key = os.getenv('X_API_KEY')
    consumer_secret = os.getenv('X_API_SECRET')
    access_token = os.getenv('X_ACCESS_TOKEN')
    access_token_secret = os.getenv('X_ACCESS_TOKEN_SECRET')

    if not bearer_token:
        return "Error: X_BEARER_TOKEN not found in environment variables"

    try:
        # Initialize tweepy client
        client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )

        # Calculate date range (last 7 days)
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(days=7)

        # Get user ID
        me = client.get_me()
        if not me.data:
            return "Error: Could not get user information"

        user_id = me.data.id

        # Fetch user's recent tweets (last 7 days)
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=100,  # Max allowed
            start_time=start_time,
            end_time=end_time,
            tweet_fields=['created_at', 'public_metrics', 'context_annotations']
        )

        user_tweets_data = []
        if tweets.data:
            for tweet in tweets.data:
                user_tweets_data.append({
                    "id": tweet.id,
                    "text": tweet.text,
                    "created_at": tweet.created_at.isoformat() if tweet.created_at else None,
                    "metrics": tweet.public_metrics or {},
                    "context_annotations": tweet.context_annotations or []
                })

        # Fetch mentions of the user (last 7 days)
        mentions = client.get_users_mentions(
            id=user_id,
            max_results=100,
            start_time=start_time,
            end_time=end_time,
            tweet_fields=['created_at', 'author_id', 'public_metrics']
        )

        mentions_data = []
        if mentions.data:
            for mention in mentions.data:
                mentions_data.append({
                    "id": mention.id,
                    "text": mention.text,
                    "author_id": mention.author_id,
                    "created_at": mention.created_at.isoformat() if mention.created_at else None,
                    "metrics": mention.public_metrics or {}
                })

        # Fetch user's replies to others (last 7 days)
        # This requires filtering the user's tweets to find those that are replies
        replies_data = []
        for tweet in user_tweets_data:
            # A tweet is a reply if it has a referenced tweet that is not from the same user
            if 'in_reply_to_user_id' in str(tweet.get('text', '').lower()) or tweet.get('text', '').startswith('@'):
                replies_data.append(tweet)

        # Prepare data for Claude
        x_data = {
            "platform": "x",
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "user_tweets": user_tweets_data,
            "mentions": mentions_data,
            "replies": replies_data,
            "summary": {
                "total_tweets": len(user_tweets_data),
                "total_mentions": len(mentions_data),
                "total_replies": len(replies_data)
            }
        }

        # Generate summary using Claude
        anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        system_prompt = """
        You are an expert social media analyst. Create a comprehensive weekly summary
        of X (Twitter) activity for the last 7 days, including analysis of reach,
        engagement, top-performing content, audience sentiment, and recommendations.
        """

        user_prompt = f"""
        X (Twitter) Platform Weekly Activity Summary
        Date Range: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}

        Data:
        {json.dumps(x_data, indent=2)}

        Please provide a detailed summary with the following sections:
        1. Executive Summary
        2. Performance Metrics (total tweets, mentions, replies, engagement metrics)
        3. Content Analysis (top-performing tweets, themes, topics)
        4. Audience Engagement (mentions analysis, sentiment)
        5. Reply Analysis (conversations participated in)
        6. Recommendations for improvement

        Format your response as clean Markdown with appropriate headers.
        """

        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        summary_content = response.content[0].text

        # Save summary to file
        date_str = end_time.strftime('%Y-%m-%d')
        summary_dir = Path("Social_Summaries")
        summary_dir.mkdir(exist_ok=True)

        filename = f"{summary_dir}/{date_str}_x_weekly_summary.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# X (Twitter) Weekly Summary\n")
            f.write(f"## {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}\n\n")
            f.write(summary_content)
            f.write(f"\n\n---\n")
            f.write(f"*Generated by Claude AI on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
            f.write(f"*Period: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}*\n")
            f.write(f"*Platform: X (Twitter)*\n")

        return f"Weekly X summary saved to: {filename}"

    except tweepy.TooManyRequests:
        return "Error: Rate limit exceeded while fetching X data"
    except tweepy.Unauthorized:
        return "Error: Unauthorized. Check your X API credentials."
    except Exception as e:
        return f"Error in X summary generator: {str(e)}"