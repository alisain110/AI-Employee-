"""
Comprehensive audit logging system for AI Employee Vault
Logs all MCP calls, Claude responses, watcher events in JSON lines format
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import threading
from dataclasses import dataclass, asdict
from enum import Enum


class AuditActor(str, Enum):
    WATCHER = "watcher"
    CLAUDE = "claude"
    MCP = "mcp"
    ORCHESTRATOR = "orchestrator"
    SCHEDULER = "scheduler"
    AGENT = "agent"
    ERROR_DETECTOR = "error_detector"


class AuditAction(str, Enum):
    MCP_CALL = "mcp_call"
    CLAUDE_REQUEST = "claude_request"
    WATCHER_EVENT = "watcher_event"
    TASK_PROCESSED = "task_processed"
    SCHEDULED_JOB = "scheduled_job"
    FILE_OPERATION = "file_operation"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_STATUS = "system_status"
    ERROR_DETECTION = "error_detection"
    ERROR_EXPLANATION = "error_explanation"
    ERROR_FIX_SUGGESTION = "error_fix_suggestion"


@dataclass
class AuditLogEntry:
    """Structure for audit log entries"""
    timestamp: str
    actor: AuditActor
    action: AuditAction
    success: bool
    details: Dict[str, Any]
    error: Optional[str] = None
    session_id: Optional[str] = None


class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self, logs_dir: str = "Logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)

        # Thread-safe logging
        self._lock = threading.Lock()

        # Create file handler for audit logs
        self._setup_audit_logger()

    def _setup_audit_logger(self):
        """Setup audit-specific logger"""
        self.audit_logger = logging.getLogger('audit_logger')
        self.audit_logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self.audit_logger.handlers:
            # Create custom handler for audit logs
            today = datetime.now().strftime('%Y-%m-%d')
            audit_log_file = self.logs_dir / f"audit_{today}.log"

            from logging import FileHandler
            handler = FileHandler(str(audit_log_file), mode='a', encoding='utf-8')
            handler.setLevel(logging.INFO)

            # Use a simple formatter - we'll write JSON manually
            self.audit_logger.addHandler(handler)
            self.audit_logger.propagate = False  # Don't propagate to root logger

    def _get_current_log_file(self) -> Path:
        """Get current day's audit log file"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.logs_dir / f"audit_{today}.log"

    def log_entry(self, entry: AuditLogEntry):
        """Log an audit entry in JSON lines format"""
        with self._lock:
            try:
                # Add current timestamp if not provided
                if not entry.timestamp:
                    entry.timestamp = datetime.now().isoformat()

                # Write as JSON line
                log_line = json.dumps(asdict(entry))
                self.audit_logger.info(log_line)

            except Exception as e:
                # Fallback logging if JSON serialization fails
                error_entry = AuditLogEntry(
                    timestamp=datetime.now().isoformat(),
                    actor=AuditActor.ORCHESTRATOR,
                    action=AuditAction.ERROR_OCCURRED,
                    success=False,
                    details={"original_entry": str(entry)},
                    error=f"Failed to log audit entry: {str(e)}"
                )
                error_line = json.dumps(asdict(error_entry))
                self.audit_logger.error(error_line)

    def log_mcp_call(self,
                    service: str,
                    endpoint: str,
                    data: Dict[str, Any],
                    success: bool,
                    response: Any = None,
                    error: str = None,
                    session_id: str = None):
        """Log MCP endpoint calls"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.MCP,
            action=AuditAction.MCP_CALL,
            success=success,
            details={
                "service": service,
                "endpoint": endpoint,
                "request_data": data,
                "response_summary": self._safe_summary(response),
                "call_duration": None  # Can be added if timing is measured
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_claude_request(self,
                          model: str,
                          prompt_length: int,
                          response_length: int,
                          success: bool,
                          error: str = None,
                          session_id: str = None):
        """Log Claude API requests"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.CLAUDE,
            action=AuditAction.CLAUDE_REQUEST,
            success=success,
            details={
                "model": model,
                "prompt_length": prompt_length,
                "response_length": response_length,
                "timestamp": datetime.now().isoformat()
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_watcher_event(self,
                         watcher_type: str,
                         event_type: str,
                         event_data: Dict[str, Any],
                         success: bool,
                         error: str = None,
                         session_id: str = None):
        """Log watcher events"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.WATCHER,
            action=AuditAction.WATCHER_EVENT,
            success=success,
            details={
                "watcher_type": watcher_type,
                "event_type": event_type,
                "event_data": event_data
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_task_processed(self,
                          task_id: str,
                          task_type: str,
                          processing_time: float,
                          success: bool,
                          error: str = None,
                          session_id: str = None):
        """Log task processing events"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.ORCHESTRATOR,
            action=AuditAction.TASK_PROCESSED,
            success=success,
            details={
                "task_id": task_id,
                "task_type": task_type,
                "processing_time": processing_time
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_error(self,
                 error_type: str,
                 error_message: str,
                 context: Dict[str, Any],
                 severity: str = "medium",
                 session_id: str = None):
        """Log error events"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.ORCHESTRATOR,
            action=AuditAction.ERROR_OCCURRED,
            success=False,
            details={
                "error_type": error_type,
                "context": context,
                "severity": severity
            },
            error=error_message,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_error_detection(self,
                          filename: str,
                          total_errors: int,
                          processing_time: float,
                          success: bool,
                          error: str = None,
                          session_id: str = None):
        """Log error detection events"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.CLAUDE,
            action=AuditAction.ERROR_DETECTION,
            success=success,
            details={
                "filename": filename,
                "total_errors": total_errors,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_error_explanation(self,
                            error_type: str,
                            error_message: str,
                            explanation_provided: bool,
                            success: bool,
                            error: str = None,
                            session_id: str = None):
        """Log error explanation events"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.CLAUDE,
            action=AuditAction.ERROR_EXPLANATION,
            success=success,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "explanation_provided": explanation_provided,
                "timestamp": datetime.now().isoformat()
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def log_error_fix_suggestion(self,
                               error_type: str,
                               error_message: str,
                               fix_suggested: bool,
                               success: bool,
                               error: str = None,
                               session_id: str = None):
        """Log error fix suggestion events"""
        entry = AuditLogEntry(
            timestamp=datetime.now().isoformat(),
            actor=AuditActor.CLAUDE,
            action=AuditAction.ERROR_FIX_SUGGESTION,
            success=success,
            details={
                "error_type": error_type,
                "error_message": error_message,
                "fix_suggested": fix_suggested,
                "timestamp": datetime.now().isoformat()
            },
            error=error,
            session_id=session_id
        )
        self.log_entry(entry)

    def _safe_summary(self, obj):
        """Create a safe summary of potentially large objects"""
        if obj is None:
            return None
        if isinstance(obj, (str, int, float, bool)):
            return obj
        if isinstance(obj, dict):
            # Return a summary of dictionary
            keys = list(obj.keys())
            if len(keys) > 10:
                return {"summary": f"Dict with {len(keys)} keys", "sample_keys": keys[:5]}
            else:
                return {k: self._safe_summary(v) for k, v in list(obj.items())[:10]}
        if isinstance(obj, list):
            if len(obj) > 10:
                return {"summary": f"List with {len(obj)} items", "sample_items": obj[:5]}
            else:
                return [self._safe_summary(item) for item in obj[:10]]
        return str(type(obj))


# Global audit logger instance
_audit_logger = None
def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Error recovery utilities
import time
import random
from functools import wraps

def retry_on_transient_error(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator to retry functions on transient errors.
    Retries on network errors, 429, 500, and similar transient errors.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):  # +1 to include original attempt
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Check if this is a transient error we should retry
                    should_retry = (
                        any(phrase in error_str for phrase in ['network', 'timeout', 'connection', '500', '502', '503', '429']) or
                        'rate limit' in error_str or
                        'exceeded' in error_str or
                        'temporarily unavailable' in error_str
                    )

                    if attempt < max_retries and should_retry:
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Attempt {attempt + 1} failed with {type(e).__name__}: {e}. Retrying in {delay:.2f}s...")
                        time.sleep(delay)
                        continue
                    else:
                        # If it's not a transient error or we've exhausted retries, raise
                        raise e

            # This shouldn't be reached, but just in case
            raise last_exception
        return wrapper
    return decorator


def graceful_fallback(fallback_action=None):
    """
    Decorator to provide graceful fallback when primary action fails.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                audit_logger = get_audit_logger()
                audit_logger.log_error(
                    error_type="function_failure",
                    error_message=str(e),
                    context={"function": func.__name__, "args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                    severity="high"
                )

                if fallback_action:
                    try:
                        return fallback_action(*args, **kwargs)
                    except Exception as fallback_error:
                        audit_logger.log_error(
                            error_type="fallback_failure",
                            error_message=str(fallback_error),
                            context={"original_error": str(e), "fallback_function": fallback_action.__name__}
                        )
                        raise  # Re-raise original error if fallback also fails
                else:
                    raise
        return wrapper
    return decorator