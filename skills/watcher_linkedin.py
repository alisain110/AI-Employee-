"""
LinkedIn Watcher Skill
"""
import os
import threading
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    logger.warning("Selenium not installed. Install with: pip install selenium")

class LinkedInWatcher:
    def __init__(self, session_folder: str = "./linkedin_session", access_token: Optional[str] = None):
        self.session_folder = Path(session_folder)
        self.access_token = access_token
        self.driver = None
        self.running = False
        self.thread = None
        self.check_interval = 300  # 5 minutes

    def _setup_driver(self):
        """Setup Chrome driver with session persistence"""
        if not HAS_SELENIUM:
            raise ImportError("Selenium not installed. Install with: pip install selenium")

        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={self.session_folder.absolute()}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Create session folder if it doesn't exist
        self.session_folder.mkdir(parents=True, exist_ok=True)

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def authenticate(self):
        """Authenticate with LinkedIn"""
        if not self.driver:
            self._setup_driver()

        self.driver.get("https://www.linkedin.com/")
        logger.info("Please log in to LinkedIn in the browser window")

        # Wait for user to log in manually
        wait = WebDriverWait(self.driver, 120)  # Wait up to 2 minutes
        try:
            # Wait for main LinkedIn page to load (indicates successful login)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'share-box-feed-entry__container')] | //button[contains(@class, 'global-nav__primary-link')]")))
            logger.info("Successfully logged in to LinkedIn")
        except:
            logger.error("Failed to log in to LinkedIn within 2 minutes")

    def get_recent_notifications(self):
        """Get recent notifications from LinkedIn using Selenium"""
        if not self.driver:
            self._setup_driver()
            self.authenticate()

        try:
            # Navigate to notifications page
            self.driver.get("https://www.linkedin.com/notifications/")
            time.sleep(3)  # Wait for page to load

            # Find notification elements
            notification_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'occludable-update')]")

            recent_notifications = []

            for element in notification_elements[:10]:  # Get first 10 notifications
                try:
                    # Extract notification text
                    notification_text = element.text

                    if notification_text.strip():  # Only add non-empty notifications
                        notification_data = {
                            'text': notification_text,
                            'timestamp': datetime.now()
                        }
                        recent_notifications.append(notification_data)
                except Exception as e:
                    continue  # Skip if we can't parse this notification

            return recent_notifications

        except Exception as e:
            logger.error(f"Error getting LinkedIn notifications: {e}")
            return []

    def get_recent_connections(self):
        """Get recent connection requests and messages"""
        if not self.driver:
            self._setup_driver()
            self.authenticate()

        try:
            # Navigate to messages page
            self.driver.get("https://www.linkedin.com/messaging/")
            time.sleep(3)  # Wait for page to load

            # Find conversation elements (recent messages)
            conversation_elements = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'msg-conversation-listitem')]")

            recent_messages = []

            for element in conversation_elements[:5]:  # Get first 5 conversations
                try:
                    # Extract sender and message preview
                    sender_element = element.find_elements(By.XPATH, ".//span[contains(@class, 'msg-conversation-listitem__participant-names')] | .//h3[contains(@class, '')] | .//div[contains(@class, '')]")
                    message_preview_element = element.find_elements(By.XPATH, ".//p[contains(@class, 'msg-conversation-card__message-snippet')]")

                    sender = sender_element[0].text if sender_element else "Unknown"
                    message_preview = message_preview_element[0].text if message_preview_element else ""

                    if sender.strip() or message_preview.strip():
                        message_data = {
                            'sender': sender,
                            'message_preview': message_preview,
                            'timestamp': datetime.now()
                        }
                        recent_messages.append(message_data)
                except Exception as e:
                    continue  # Skip if we can't parse this conversation

            return recent_messages

        except Exception as e:
            logger.error(f"Error getting LinkedIn messages: {e}")
            return []

    def start_watcher(self):
        """Start the LinkedIn watcher in a background thread"""
        if self.running:
            logger.info("LinkedIn watcher is already running")
            return

        # Initialize driver before starting thread
        if not self.driver:
            try:
                self._setup_driver()
                self.authenticate()
            except Exception as e:
                logger.error(f"Could not start LinkedIn watcher: {e}")
                return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info("LinkedIn watcher started")

    def stop_watcher(self):
        """Stop the LinkedIn watcher"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
        if self.driver:
            self.driver.quit()
        logger.info("LinkedIn watcher stopped")

    def _watch_loop(self):
        """Main watching loop"""
        while self.running:
            try:
                # Get both notifications and messages
                notifications = self.get_recent_notifications()
                messages = self.get_recent_connections()

                all_updates = []

                # Prepare notification updates
                for notification in notifications:
                    update = {
                        'type': 'notification',
                        'content': notification['text'],
                        'timestamp': notification['timestamp']
                    }
                    all_updates.append(update)

                # Prepare message updates
                for message in messages:
                    update = {
                        'type': 'message',
                        'sender': message['sender'],
                        'content': message['message_preview'],
                        'timestamp': message['timestamp']
                    }
                    all_updates.append(update)

                if all_updates:
                    logger.info(f"Found {len(all_updates)} new LinkedIn update(s)")

                    # Process each update through Claude reasoning loop
                    for update in all_updates:
                        self._process_update(update)

                # Wait before next check
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in LinkedIn watch loop: {e}")
                time.sleep(self.check_interval)  # Wait before retrying

    def _process_update(self, update_data):
        """Process a LinkedIn update and trigger Claude reasoning"""
        try:
            from core.agent import AIAgent

            agent = AIAgent()

            if update_data['type'] == 'notification':
                task = f"""
                Process this new LinkedIn notification:
                Content: {update_data['content']}

                Summarize this notification and create an action plan.
                """
                task_description = f"LinkedIn notification: {update_data['content'][:50]}..."
            else:  # message
                task = f"""
                Process this new LinkedIn message:
                From: {update_data.get('sender', 'Unknown')}
                Content: {update_data['content']}

                Summarize this message and create a reply/action plan.
                """
                task_description = f"LinkedIn message from {update_data.get('sender', 'Unknown')}"

            result = agent.run(
                "claude_reasoning_loop",
                task_description=task_description,
                context=task
            )

            logger.info(f"Processed LinkedIn {update_data['type']} with reasoning loop, result: {result}")

        except Exception as e:
            logger.error(f"Error processing LinkedIn update with Claude: {e}")

@tool
def linkedin_watcher_skill(action: str, session_folder: str = "./linkedin_session", access_token: Optional[str] = None) -> str:
    """
    LinkedIn Watcher Skill to monitor new notifications and messages, processing them with Claude.

    Args:
        action (str): Either 'start' to start the watcher or 'stop' to stop it
        session_folder (str): Path to store LinkedIn session data
        access_token (Optional[str]): LinkedIn API access token (optional, for API-based approach)

    Returns:
        str: Status message
    """
    from watcher_state import get_watcher

    # Get or create the watcher instance
    watcher = get_watcher("linkedin", session_folder, access_token)

    if action.lower() == 'start':
        watcher.start_watcher()
        return "LinkedIn watcher started successfully"
    elif action.lower() == 'stop':
        watcher.stop_watcher()
        return "LinkedIn watcher stopped successfully"
    else:
        return "Action must be either 'start' or 'stop'"