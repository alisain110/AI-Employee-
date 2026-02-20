import threading
from skills.watcher_gmail import GmailWatcher
from skills.watcher_whatsapp import WhatsAppWatcher
from skills.watcher_linkedin import LinkedInWatcher

# Global storage for watcher instances with thread-safe access
_watchers = {}
_watchers_lock = threading.Lock()

def get_watcher(watcher_type: str, *args, **kwargs):
    """
    Get or create a watcher instance

    Args:
        watcher_type (str): Type of watcher ('gmail', 'whatsapp', 'linkedin')
        *args, **kwargs: Arguments to pass to watcher constructor

    Returns:
        Watcher instance
    """
    global _watchers

    with _watchers_lock:
        if watcher_type not in _watchers:
            if watcher_type == 'gmail':
                _watchers[watcher_type] = GmailWatcher(*args, **kwargs)
            elif watcher_type == 'whatsapp':
                _watchers[watcher_type] = WhatsAppWatcher(*args, **kwargs)
            elif watcher_type == 'linkedin':
                _watchers[watcher_type] = LinkedInWatcher(*args, **kwargs)
            else:
                raise ValueError(f"Unknown watcher type: {watcher_type}")

    return _watchers[watcher_type]
