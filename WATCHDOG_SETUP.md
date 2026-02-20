# Platinum Watchdog Setup Guide

## Overview
The Platinum Watchdog monitors the health of all Platinum Tier services and automatically restarts them if they fail. It also provides health monitoring and alerting capabilities.

## Components

### 1. platinum_watchdog_win.py
Windows-compatible version of the watchdog service that:
- Monitors orchestrators, watchers, and MCP servers
- Automatically restarts dead services
- Tracks restart frequency to prevent infinite restart loops
- Updates heartbeat file for system monitoring
- Logs alerts when services fail repeatedly

### 2. platinum_watchdog.service
Systemd service file for Linux systems that enables the watchdog to start automatically on boot.

## Features

- **Service Monitoring**: Checks if orchestrator, watchers, and MCP servers are running
- **Auto-restart**: Restarts services if they die
- **Restart Throttling**: Prevents excessive restarts (max 3 in 10 minutes)
- **Health Pings**: Updates heartbeat file for system monitoring
- **Alert Logging**: Records excessive restarts in `Logs/alerts.md`
- **Environment Detection**: Separate configurations for cloud vs local

## Setup Instructions

### For Linux/Unix Systems:

1. **Copy the watchdog files to your system:**
```bash
cp platinum_watchdog.py /home/aiuser/AI_Employee_Vault/
cp platinum_watchdog.service /etc/systemd/system/
```

2. **Modify the service file for your environment:**
   - Update `User` and `Group` to match your system user
   - Update `WorkingDirectory` to your AI_Employee_Vault path
   - Change `--env=local` to `--env=cloud` if this is a cloud instance

3. **Set up the service:**
```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable platinum_watchdog.service

# Start the service now
sudo systemctl start platinum_watchdog.service

# Check status
sudo systemctl status platinum_watchdog.service
```

### For Windows Systems:

1. **Run the watchdog manually:**
```bash
# For local environment
python platinum_watchdog_win.py --env=local

# For cloud environment
python platinum_watchdog_win.py --env=cloud
```

2. **To run in background on Windows** (using Task Scheduler), create a batch file:
```batch
@echo off
cd /d "C:\path\to\AI_Employee_Vault"
python platinum_watchdog_win.py --env=local
```

## Service Monitoring

The watchdog monitors these services based on environment:

### Local Environment:
- `platinum_local_orchestrator.py`
- `approval_executor.py`
- `dashboard_merger.py`
- `odoo_execute_mcp.py` (local operations)

### Cloud Environment:
- `cloud_orchestrator.py`
- `email_watcher.py`
- `odoo_draft_mcp.py` (cloud operations)
- Plus all local services

## Configuration

The watchdog has these configurable parameters:
- `max_restarts`: Maximum restarts allowed (default: 3)
- `time_window`: Time window in seconds (default: 600 = 10 minutes)
- `check_interval`: Check interval in seconds (default: 30)

## Log Files

- `Logs/watchdog.log`: Main watchdog operation log
- `Logs/alerts.md`: Alert log for excessive restarts
- `Service_Logs/`: Individual service logs created when services are restarted

## Heartbeat Monitoring

The watchdog creates a `heartbeat.md` file that shows:
- Last update timestamp
- Environment type (cloud/local)
- System health status
- Services being monitored

## Troubleshooting

### Common Issues:

1. **Service won't start automatically:**
   - Check that the service file has correct paths
   - Verify the user exists and has proper permissions
   - Check `sudo journalctl -u platinum_watchdog.service -f` for errors

2. **Services keep restarting:**
   - Check `Logs/alerts.md` for excessive restart alerts
   - Review individual service logs in `Service_Logs/`
   - The watchdog will log "Too many restarts" if exceeding limits

3. **Watchdog not monitoring some services:**
   - Verify the service files exist in the working directory
   - Check watchdog logs for errors during process detection

### Manual Testing:

1. **Test service restart:**
   ```bash
   # Stop a service manually
   pkill -f "platinum_local_orchestrator.py"

   # Watchdog should detect and restart it
   # Monitor with: tail -f Logs/watchdog.log
   ```

2. **Check heartbeat:**
   ```bash
   cat heartbeat.md
   ```

## Security Considerations

- Run the watchdog under a dedicated service user (not root)
- The service uses security settings like `NoNewPrivileges` and `ProtectSystem`
- Logs may contain sensitive information - protect log files accordingly
- Only monitor necessary services to minimize attack surface

## Verification

After setup, verify the watchdog is working:
1. Check that the service is running
2. Verify heartbeat updates in `heartbeat.md`
3. Test by stopping a service and confirming it auto-restarts
4. Review logs for any errors