@echo off
REM Platinum Tier Demo Setup and Verification Script
REM This script helps prepare and verify the Platinum Tier demo environment

echo ================================================
echo Platinum Tier Demo Setup and Verification Script
echo ================================================

REM Check if required directories exist
echo.
echo Checking required directories...
if not exist "Pending_Approval" mkdir Pending_Approval
if not exist "Pending_Approval\cloud" mkdir Pending_Approval\cloud
if not exist "Approved" mkdir Approved
if not exist "Done" mkdir Done
if not exist "Inbox" mkdir Inbox
if not exist "Logs" mkdir Logs
if not exist "Updates" mkdir Updates
echo Required directories verified/created.

REM Check for required files
echo.
echo Checking for required files...
if not exist "platinum_local_orchestrator.py" (
    echo ERROR: platinum_local_orchestrator.py not found!
    pause
    exit /b 1
)
if not exist "approval_executor.py" (
    echo ERROR: approval_executor.py not found!
    pause
    exit /b 1
)
if not exist "dashboard_merger.py" (
    echo ERROR: dashboard_merger.py not found!
    pause
    exit /b 1
)
if not exist ".env" (
    echo WARNING: .env file not found! Please ensure credentials are configured.
)

echo Required files verified.

REM Check if services are running (basic check)
echo.
echo Checking if services are running...
tasklist /fi "imagename eq python.exe" 2>nul | find /i "platinum_local_orchestrator.py" >nul
if %errorlevel%==0 (
    echo platinum_local_orchestrator.py is running.
) else (
    echo WARNING: platinum_local_orchestrator.py is NOT running.
)

tasklist /fi "imagename eq python.exe" 2>nul | find /i "approval_executor.py" >nul
if %errorlevel%==0 (
    echo approval_executor.py is running.
) else (
    echo WARNING: approval_executor.py is NOT running.
)

tasklist /fi "imagename eq python.exe" 2>nul | find /i "dashboard_merger.py" >nul
if %errorlevel%==0 (
    echo dashboard_merger.py is running.
) else (
    echo WARNING: dashboard_merger.py is NOT running.
)

REM Show current status of key directories
echo.
echo Current status of key directories:
echo Pending_Approval\cloud\:
dir /b "Pending_Approval\cloud\" 2>nul || echo   (empty)
echo Approved\:
dir /b "Approved\" 2>nul || echo   (empty)
echo Done\:
dir /b "Done\" 2>nul || echo   (empty)
echo Inbox\:
dir /b "Inbox\" 2>nul || echo   (empty)

REM Show recent log entries
echo.
echo Recent log entries (last 5 lines of each):
if exist "Logs\platinum_local_orchestrator.log" (
    echo platinum_local_orchestrator.log:
    powershell -command "Get-Content 'Logs\platinum_local_orchestrator.log' | Select-Object -Last 5"
) else (
    echo   platinum_local_orchestrator.log not found
)

if exist "Logs\approval_executor.log" (
    echo approval_executor.log:
    powershell -command "Get-Content 'Logs\approval_executor.log' | Select-Object -Last 5"
) else (
    echo   approval_executor.log not found
)

if exist "Logs\dashboard_merger.log" (
    echo dashboard_merger.log:
    powershell -command "Get-Content 'Logs\dashboard_merger.log' | Select-Object -Last 5"
) else (
    echo   dashboard_merger.log not found
)

echo.
echo ================================================
echo Demo Environment Verification Complete
echo ================================================
echo.
echo To start the demo:
echo 1. Ensure all required services are running
echo 2. Send a test email to trigger the process
echo 3. Follow the steps in PLATINUM_TIER_DEMO_SCRIPT.md
echo 4. Monitor logs and directory changes during the process
echo.
pause