"""
Cloud-specific watchers for Platinum Tier AI Employee Vault
Only Gmail and social media mentions (no WhatsApp on cloud)
"""
import os
import time
import logging
from datetime import datetime
from pathlib import Path
import imaplib
import email
from email.header import decode_header

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "cloud_watchers.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CloudGmailWatcher:
    """Cloud Gmail watcher - only reads and creates tasks, never sends"""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.needs_action.mkdir(exist_ok=True)

        # Load Gmail credentials (should be in .env.local on cloud)
        self.email_address = os.getenv("GMAIL_ADDRESS")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")
        self.imap_server = "imap.gmail.com"

        # Track seen emails to avoid duplicates
        self.seen_emails_file = self.vault_path / ".cloud_seen_emails"
        self.seen_emails = self._load_seen_emails()

    def _load_seen_emails(self):
        """Load previously seen email IDs"""
        if self.seen_emails_file.exists():
            with open(self.seen_emails_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_seen_emails(self):
        """Save seen email IDs to file"""
        with open(self.seen_emails_file, 'w') as f:
            for email_id in self.seen_emails:
                f.write(f"{email_id}\n")

    def _decode_mime_words(self, s):
        """Decode MIME encoded words in headers"""
        decoded_fragments = decode_header(s)
        fragments = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    fragment = fragment.decode(encoding)
                else:
                    fragment = fragment.decode('utf-8', errors='ignore')
            fragments.append(fragment)
        return ''.join(fragments)

    def check_new_emails(self):
        """Check for new emails and create tasks"""
        if not self.email_address or not self.app_password:
            logger.warning("Gmail credentials not found in environment variables")
            return

        try:
            # Connect to Gmail
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_address, self.app_password)

            # Select inbox
            mail.select('inbox')

            # Search for all emails
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()

            new_emails_count = 0

            for email_id in email_ids:
                email_str = email_id.decode()

                # Skip if we've already processed this email
                if email_str in self.seen_emails:
                    continue

                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Extract email details
                        subject = self._decode_mime_words(msg['Subject']) if msg['Subject'] else "No Subject"
                        from_addr = self._decode_mime_words(msg['From']) if msg['From'] else "Unknown"

                        # Get email body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

                        # Create task file
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        task_filename = f"EMAIL_{timestamp}_{email_str}.md"
                        task_file = self.needs_action / task_filename

                        task_content = f"""---
type: email
from: {from_addr}
subject: {subject}
received: {datetime.now().isoformat()}
source: cloud_gmail_watcher
---

# Email from: {from_addr}

## Subject: {subject}

## Email Content
{body}

## Action Required
Process this email and generate appropriate response draft.
"""

                        task_file.write_text(task_content)
                        logger.info(f"Created email task: {task_file.name}")
                        new_emails_count += 1

                # Mark email as seen
                self.seen_emails.add(email_str)

            # Save seen emails
            self._save_seen_emails()

            # Logout
            mail.logout()

            if new_emails_count > 0:
                logger.info(f"Processed {new_emails_count} new emails")

        except Exception as e:
            logger.error(f"Error checking emails: {e}")

    def run(self):
        """Run the Gmail watcher continuously"""
        logger.info("Cloud Gmail Watcher started")

        while True:
            try:
                self.check_new_emails()
                # Check every 5 minutes
                time.sleep(300)
            except KeyboardInterrupt:
                logger.info("Cloud Gmail Watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in Gmail watcher: {e}")
                # Wait longer after error
                time.sleep(60)


class CloudSocialWatcher:
    """Cloud social media mentions watcher - monitor mentions only"""

    def __init__(self, vault_path: str = "."):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.needs_action.mkdir(exist_ok=True)

        # Social media API credentials (should be in .env.local on cloud)
        self.social_credentials = {
            'facebook': os.getenv('FACEBOOK_PAGE_TOKEN'),
            'twitter': os.getenv('TWITTER_BEARER_TOKEN'),
            'instagram': os.getenv('INSTAGRAM_ACCESS_TOKEN')
        }

    def check_social_mentions(self):
        """Check for new mentions on social platforms"""
        logger.info("Checking for social media mentions...")

        # For this example, we'll simulate checking
        # In a real implementation, you'd use the appropriate APIs

        # This would normally use the social media APIs to check for mentions
        # For now, let's just log that we're checking
        logger.info("Checked social media mentions (simulated)")

        # Example: If mentions are found, create a task
        # This is just a placeholder - real implementation would be platform-specific
        pass

    def run(self):
        """Run the social watcher continuously"""
        logger.info("Cloud Social Watcher started")

        while True:
            try:
                self.check_social_mentions()
                # Check every 10 minutes
                time.sleep(600)
            except KeyboardInterrupt:
                logger.info("Cloud Social Watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in social watcher: {e}")
                # Wait longer after error
                time.sleep(60)


def main():
    """Main function to start cloud watchers"""
    import sys
    from threading import Thread

    if len(sys.argv) < 2 or sys.argv[1] not in ['gmail', 'social', 'both']:
        print("Usage: python cloud_watchers.py [gmail|social|both]")
        return

    mode = sys.argv[1]

    if mode in ['gmail', 'both']:
        gmail_watcher = CloudGmailWatcher()
        gmail_thread = Thread(target=gmail_watcher.run, daemon=True)
        gmail_thread.start()
        logger.info("Gmail watcher started")

    if mode in ['social', 'both']:
        social_watcher = CloudSocialWatcher()
        social_thread = Thread(target=social_watcher.run, daemon=True)
        social_thread.start()
        logger.info("Social watcher started")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Cloud watchers stopped by user")


if __name__ == "__main__":
    main()