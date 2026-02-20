"""
Gmail Watcher Skill
"""
import os
import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GMAIL = True
except ImportError:
    HAS_GMAIL = False
    logger.warning("Gmail API dependencies not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

class GmailWatcher:
    def __init__(self, credentials_path: str = "credentials.json", token_path: str = "token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.running = False
        self.thread = None
        self.check_interval = 300  # 5 minutes

    def authenticate(self):
        """Authenticate with Gmail API"""
        if not HAS_GMAIL:
            raise ImportError("Gmail dependencies not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, ['https://www.googleapis.com/auth/gmail.readonly'])

        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Could not refresh credentials: {e}")
                    # Delete the token file and get new credentials
                    if os.path.exists(self.token_path):
                        os.remove(self.token_path)

                    # Start OAuth flow if credentials file exists
                    if os.path.exists(self.credentials_path):
                        flow = Flow.from_client_secrets_file(
                            self.credentials_path,
                            scopes=['https://www.googleapis.com/auth/gmail.readonly'],
                            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                        )
                        flow.run_local_server(port=0)
                        creds = flow.credentials
                    else:
                        raise Exception("Credentials file not found. Please set up Gmail API credentials.")
            else:
                # Get new credentials
                if os.path.exists(self.credentials_path):
                    flow = Flow.from_client_secrets_file(
                        self.credentials_path,
                        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
                        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
                    )
                    flow.run_local_server(port=0)
                    creds = flow.credentials
                else:
                    raise Exception("Credentials file not found. Please set up Gmail API credentials.")

            # Save the credentials for next run
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('gmail', 'v1', credentials=creds)

    def get_recent_emails(self, since_time: Optional[datetime] = None):
        """Get recent emails from Gmail"""
        if not self.service:
            self.authenticate()

        query = 'is:unread'
        if since_time:
            # Gmail API requires date format like 2023/01/01
            date_str = since_time.strftime('%Y/%m/%d')
            query += f' after:{date_str}'

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()

            messages = results.get('messages', [])
            recent_emails = []

            for msg in messages:
                message = self.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()

                # Extract email data
                headers = {h['name']: h['value'] for h in message['payload']['headers']}
                snippet = message.get('snippet', '')

                email_data = {
                    'id': msg['id'],
                    'subject': headers.get('Subject', 'No Subject'),
                    'from': headers.get('From', 'Unknown'),
                    'date': headers.get('Date', ''),
                    'snippet': snippet,
                    'timestamp': datetime.now()
                }

                recent_emails.append(email_data)

            return recent_emails
        except HttpError as error:
            logger.error(f'An error occurred: {error}')
            return []

    def start_watcher(self):
        """Start the Gmail watcher in a background thread"""
        if self.running:
            logger.info("Gmail watcher is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info("Gmail watcher started")

    def stop_watcher(self):
        """Stop the Gmail watcher"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
        logger.info("Gmail watcher stopped")

    def _watch_loop(self):
        """Main watching loop"""
        last_check = datetime.now() - timedelta(minutes=1)  # Check emails from last minute initially

        while self.running:
            try:
                emails = self.get_recent_emails(since_time=last_check)

                if emails:
                    logger.info(f"Found {len(emails)} new email(s)")

                    # Process each email through Claude reasoning loop
                    for email in emails:
                        self._process_email(email)

                last_check = datetime.now()

                # Wait before next check
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in Gmail watch loop: {e}")
                time.sleep(self.check_interval)  # Wait before retrying

    def _process_email(self, email_data):
        """Process an email and trigger Claude reasoning"""
        try:
            from core.agent import AIAgent

            agent = AIAgent()

            task = f"""
            Process this new email:
            From: {email_data['from']}
            Subject: {email_data['subject']}
            Snippet: {email_data['snippet']}
            Date: {email_data['date']}

            Summarize this email and create a reply/action plan.
            """

            result = agent.run(
                "claude_reasoning_loop",
                task_description=f"Email from {email_data['from']}: {email_data['subject']}",
                context=task
            )

            logger.info(f"Processed email with reasoning loop, result: {result}")

        except Exception as e:
            logger.error(f"Error processing email with Claude: {e}")

@tool
def gmail_watcher_skill(action: str, credentials_path: str = "credentials.json", token_path: str = "token.json") -> str:
    """
    Gmail Watcher Skill to monitor new emails and process them with Claude.

    Args:
        action (str): Either 'start' to start the watcher or 'stop' to stop it
        credentials_path (str): Path to Gmail API credentials file
        token_path (str): Path to Gmail API token file

    Returns:
        str: Status message
    """
    from watcher_state import get_watcher

    # Get or create the watcher instance
    watcher = get_watcher("gmail", credentials_path, token_path)

    if action.lower() == 'start':
        watcher.start_watcher()
        return "Gmail watcher started successfully"
    elif action.lower() == 'stop':
        watcher.stop_watcher()
        return "Gmail watcher stopped successfully"
    else:
        return "Action must be either 'start' or 'stop'"