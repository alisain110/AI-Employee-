import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# This finds the folder where watcher.py lives (the /Scripts folder)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# This goes UP one level to the main Vault, then into the subfolders
WATCH_DIRECTORY = os.path.join(BASE_DIR, "..", "01_Inbox")
ACTION_DIRECTORY = os.path.join(BASE_DIR, "..", "02_Needs_Action")

# Ensure the folders actually exist before starting
os.makedirs(WATCH_DIRECTORY, exist_ok=True)
os.makedirs(ACTION_DIRECTORY, exist_ok=True)

class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"📦 New file detected: {event.src_path}")
            filename = os.path.basename(event.src_path)
            dest_path = os.path.join(ACTION_DIRECTORY, filename)
            
            # Small delay to ensure the file is fully written/copied
            time.sleep(0.5) 
            os.rename(event.src_path, dest_path)
            print(f"🚀 Moved to: {dest_path}")

if __name__ == "__main__":
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=False)
    observer.start()
    print(f"👀 Watcher is active!")
    print(f"📂 Watching: {os.path.abspath(WATCH_DIRECTORY)}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()