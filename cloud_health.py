"""
Health check endpoint for Cloud Orchestrator Lite
FastAPI endpoint that returns system status and heartbeat
"""
from fastapi import FastAPI
from datetime import datetime
import json
import logging
from pathlib import Path

# Configure logging
logs_dir = Path("Logs")
logs_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / "cloud_health.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Cloud Orchestrator Health Check",
    description="Health check endpoint for Cloud Orchestrator Lite",
    version="1.0.0"
)

# Track the last heartbeat
last_heartbeat = datetime.now().isoformat()

@app.get("/health")
async def health_check():
    """Health check endpoint returning status and last heartbeat"""
    global last_heartbeat
    last_heartbeat = datetime.now().isoformat()

    # Check if key services are running by checking for recent activity
    logs_path = Path("Logs")
    recent_activity = False

    if logs_path.exists():
        for log_file in logs_path.glob("*.log"):
            try:
                # Check if log file was modified in the last hour
                import os
                from datetime import timedelta
                modification_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if datetime.now() - modification_time < timedelta(hours=1):
                    recent_activity = True
                    break
            except:
                continue

    # Check if critical directories exist
    vault_path = Path(".")
    critical_dirs = ["Needs_Action", "In_Progress", "Done", "Pending_Approval", "Plans"]
    dirs_ok = all((vault_path / d).exists() for d in critical_dirs)

    health_status = {
        "status": "ok",
        "last_heartbeat": last_heartbeat,
        "service": "cloud-orchestrator-lite",
        "version": "1.0.0",
        "recent_activity": recent_activity,
        "critical_dirs_ok": dirs_ok,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Health check requested: {health_status}")
    return health_status

@app.get("/status")
async def status_check():
    """More detailed status check"""
    global last_heartbeat

    # Count files in different directories
    vault_path = Path(".")
    status = {
        "last_heartbeat": last_heartbeat,
        "timestamp": datetime.now().isoformat(),
        "directories": {}
    }

    for dir_name in ["Needs_Action", "In_Progress", "Done", "Pending_Approval", "Plans", "Updates"]:
        dir_path = vault_path / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*.md")))
            status["directories"][dir_name] = file_count
        else:
            status["directories"][dir_name] = 0

    # Add system information
    import psutil
    import os

    status["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent if os.name != "nt" else psutil.disk_usage(".").percent,
        "process_count": len(psutil.pids())
    }

    logger.info(f"Status check requested: {status}")
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "cloud_health:app",
        host="0.0.0.0",
        port=8006,  # Cloud health server on port 8006
        reload=False,
        log_level="info"
    )