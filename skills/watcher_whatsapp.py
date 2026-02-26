"""
WhatsApp Watcher Skill
"""
import os
import threading
import time
import logging
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

class WhatsAppWatcher:
    def __init__(self, session_folder: str = "./whatsapp_session"):
        self.session_folder = Path(session_folder)
        self.driver = None
        self.running = False
        self.thread = None
        self.check_interval = 300  # 5 minutes

    def _setup_driver(self):
        """Setup Chrome driver with session persistence"""
        if not HAS_SELENIUM:
            raise ImportError("Selenium not installed. Install with: pip install selenium")

        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument("--headless")           # must for server
        chrome_options.add_argument("--no-sandbox")         # required on Render/Linux servers
        chrome_options.add_argument("--disable-dev-shm-usage")  # avoids memory issues
        chrome_options.add_argument("--disable-gpu")        # often helps in headless
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-data-dir={self.session_folder.absolute()}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Create session folder if it doesn't exist
        self.session_folder.mkdir(parents=True, exist_ok=True)

        # Auto install & use correct driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def authenticate(self):
        """Authenticate with WhatsApp Web"""
        if not self.driver:
            self._setup_driver()

        self.driver.get("https://web.whatsapp.com")
        logger.info("Please scan the QR code to log in to WhatsApp Web")

        # Wait for user to scan QR code
        wait = WebDriverWait(self.driver, 60)
        try:
            # Wait for the chat list to appear (which means login was successful)
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@id='pane-side']")))
            logger.info("Successfully logged in to WhatsApp Web")
        except:
            logger.error("Failed to log in to WhatsApp Web within 60 seconds")

    def get_recent_messages(self):
        """Get recent messages from WhatsApp"""
        if not self.driver:
            self._setup_driver()
            self.authenticate()

        try:
            # Find the chat list
            chat_list = self.driver.find_elements(By.XPATH, "//div[@aria-label='Chat list']//div[@tabindex='-1']")

            recent_messages = []

            for chat in chat_list[:10]:  # Check first 10 chats
                try:
                    # Get chat name
                    chat_name = chat.find_element(By.XPATH, ".//span[contains(@class, 'emoji') or contains(@class, 'matched-text') or @dir='auto']").text

                    # Check for unread messages indicators
                    unread_badge = chat.find_elements(By.XPATH, ".//span[@data-icon='muted']")
                    if unread_badge:
                        # This chat has unread messages
                        chat.click()  # Open the chat
                        time.sleep(2)  # Wait for messages to load

                        # Get messages
                        message_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'copyable-text')]")

                        for msg_element in message_elements[-5:]:  # Last 5 messages
                            try:
                                sender = msg_element.get_attribute('data-pre-plain-text')
                                message_text = msg_element.text

                                if sender and message_text:
                                    msg_data = {
                                        'chat_name': chat_name,
                                        'sender': sender,
                                        'message': message_text,
                                        'timestamp': datetime.now()
                                    }
                                    recent_messages.append(msg_data)
                            except Exception as e:
                                continue  # Skip if we can't parse the message

                        # Go back to chat list
                        self.driver.get("https://web.whatsapp.com")
                        time.sleep(2)

                except Exception as e:
                    continue  # Skip if we can't process this chat

            return recent_messages

        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []

    def start_watcher(self):
        """Start the WhatsApp watcher in a background thread"""
        if self.running:
            logger.info("WhatsApp watcher is already running")
            return

        # Initialize driver before starting thread
        if not self.driver:
            try:
                self._setup_driver()
                self.authenticate()
            except Exception as e:
                logger.error(f"Could not start WhatsApp watcher: {e}")
                return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info("WhatsApp watcher started")

    def stop_watcher(self):
        """Stop the WhatsApp watcher"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
        if self.driver:
            self.driver.quit()
        logger.info("WhatsApp watcher stopped")

    def _watch_loop(self):
        """Main watching loop"""
        while self.running:
            try:
                messages = self.get_recent_messages()

                if messages:
                    logger.info(f"Found {len(messages)} new message(s)")

                    # Process each message through Claude reasoning loop
                    for message in messages:
                        self._process_message(message)

                # Wait before next check
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

            except Exception as e:
                logger.error(f"Error in WhatsApp watch loop: {e}")
                time.sleep(self.check_interval)  # Wait before retrying

    def _process_message(self, message_data):
        """Process a WhatsApp message and trigger Claude reasoning"""
        try:
            from core.agent import AIAgent

            agent = AIAgent()

            task = f"""
            Process this new WhatsApp message:
            From: {message_data['sender']}
            Chat: {message_data['chat_name']}
            Message: {message_data['message']}

            Summarize this message and create a reply/action plan.
            """

            result = agent.run(
                "claude_reasoning_loop",
                task_description=f"WhatsApp message from {message_data['sender']} in {message_data['chat_name']}",
                context=task
            )

            logger.info(f"Processed WhatsApp message with reasoning loop, result: {result}")

        except Exception as e:
            logger.error(f"Error processing WhatsApp message with Claude: {e}")

@tool
def whatsapp_watcher_skill(action: str, session_folder: str = "./whatsapp_session") -> str:
    """
    WhatsApp Watcher Skill to monitor new messages and process them with Claude.

    Args:
        action (str): Either 'start' to start the watcher or 'stop' to stop it
        session_folder (str): Path to store WhatsApp Web session data

    Returns:
        str: Status message
    """
    from watcher_state import get_watcher

    # Get or create the watcher instance
    watcher = get_watcher("whatsapp", session_folder)

    if action.lower() == 'start':
        watcher.start_watcher()
        return "WhatsApp watcher started successfully"
    elif action.lower() == 'stop':
        watcher.stop_watcher()
        return "WhatsApp watcher stopped successfully"
    else:
        return "Action must be either 'start' or 'stop'"