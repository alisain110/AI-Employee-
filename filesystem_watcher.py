import time
import logging
from pathlib import Path
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/watcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DropFolderHandler(FileSystemEventHandler):
    """Handles file system events for the drop folder"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.inbox = self.vault_path / 'Inbox'
        # Create directories if they don't exist
        self.needs_action.mkdir(exist_ok=True)
        self.inbox.mkdir(exist_ok=True)

    def on_created(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)
        # Only process files in the Inbox folder
        if self.inbox in source.parents:
            logger.info(f"New file detected: {source.name}")
            # Move the file to Needs_Action for processing
            dest = self.needs_action / source.name
            try:
                shutil.move(str(source), str(dest))
                logger.info(f"Moved {source.name} to Needs_Action folder")
                # Create a metadata file for the AI to process
                self.create_metadata_file(dest)
            except Exception as e:
                logger.error(f"Error moving file: {e}")

    def on_modified(self, event):
        if event.is_directory:
            return

        source = Path(event.src_path)
        # Only process files in the Inbox folder
        if self.inbox in source.parents:
            logger.info(f"File modified: {source.name}")
            # Create a metadata file for the AI to process
            self.create_metadata_file(source)

    def create_metadata_file(self, file_path: Path):
        """Create a metadata file for the AI to process"""
        meta_file = file_path.with_suffix('.md')

        metadata_content = f"""---
type: file_drop
original_name: {file_path.name}
size: {file_path.stat().st_size}
timestamp: {time.time()}
---

# New file in inbox: {file_path.name}

This file requires processing. Please determine the appropriate action based on the content.

## File Information:
- Name: {file_path.name}
- Size: {file_path.stat().st_size} bytes
- Type: {file_path.suffix}
- Path: {file_path}

## Action Required:
- [ ] Review content
- [ ] Determine appropriate action
- [ ] Process file according to rules
- [ ] Move original file to appropriate location
- [ ] Update dashboard with results
"""
        meta_file.write_text(metadata_content)
        logger.info(f"Created metadata file: {meta_file.name}")

def main():
    vault_path = Path.cwd()  # Current directory as vault
    inbox_path = vault_path / 'Inbox'

    # Create necessary directories
    inbox_path.mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)

    event_handler = DropFolderHandler(str(vault_path))
    observer = Observer()
    observer.schedule(event_handler, str(inbox_path), recursive=False)

    logger.info("File System Watcher started. Monitoring Inbox folder...")
    logger.info(f"Watching: {inbox_path}")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("File System Watcher stopped.")
    observer.join()

if __name__ == "__main__":
    main()