@echo off
REM Dashboard Status and Quick Checks for Platinum Tier Demo

echo ================================================
echo Platinum Tier Dashboard Status
echo ================================================

REM Create basic dashboard if it doesn't exist
if not exist "Dashboard.md" (
    echo Creating basic Dashboard.md...
    echo # AI Employee Dashboard > Dashboard.md
    echo. >> Dashboard.md
    echo ## Executive Summary >> Dashboard.md
    echo Welcome to your AI Employee dashboard. This system monitors your personal and business affairs 24/7. >> Dashboard.md
    echo. >> Dashboard.md
    echo ## Current Status >> Dashboard.md
    echo - **Date:** %date% >> Dashboard.md
    echo - **AI Employee Status:** Active >> Dashboard.md
    echo - **Last Processed:** %time% >> Dashboard.md
    echo. >> Dashboard.md
    echo ## Recent Activity >> Dashboard.md
    echo - %time% - Dashboard initialized for demo >> Dashboard.md
    echo. >> Dashboard.md
    echo ## Demo Stats >> Dashboard.md
    echo - Files in Pending_Approval/cloud/: 0 >> Dashboard.md
    echo - Files in Approved/: 0 >> Dashboard.md
    echo - Files in Done/: 0 >> Dashboard.md
)

REM Show dashboard summary
echo Dashboard Summary:
echo ==================
type Dashboard.md | findstr /C:"## Current Status" /C:"## Recent Activity" /C:"- Files in"
echo.

REM Show directory stats
echo Directory Status:
echo ================
echo Pending_Approval\cloud\:
dir Pending_Approval\cloud\ /b 2>nul | find /c /v "" > temp_count.txt
set /p pending_count=<temp_count.txt
del temp_count.txt
if not defined pending_count set pending_count=0
echo   %pending_count% files
echo.
echo Approved\:
dir Approved\ /b 2>nul | find /c /v "" > temp_count.txt
set /p approved_count=<temp_count.txt
del temp_count.txt
if not defined approved_count set approved_count=0
echo   %approved_count% files
echo.
echo Done\:
dir Done\ /b 2>nul | find /c /v "" > temp_count.txt
set /p done_count=<temp_count.txt
del temp_count.txt
if not defined done_count set done_count=0
echo   %done_count% files
echo.

REM Show recent log entries
echo Recent Activity Logs:
echo ====================
if exist "Logs\platinum_local_orchestrator.log" (
    echo Last entries from platinum_local_orchestrator.log:
    powershell -command "Get-Content 'Logs\platinum_local_orchestrator.log' | Select-Object -Last 3"
    echo.
)
if exist "Logs\approval_executor.log" (
    echo Last entries from approval_executor.log:
    powershell -command "Get-Content 'Logs\approval_executor.log' | Select-Object -Last 3"
    echo.
)
if exist "Logs\dashboard_merger.log" (
    echo Last entries from dashboard_merger.log:
    powershell -command "Get-Content 'Logs\dashboard_merger.log' | Select-Object -Last 3"
    echo.
)

REM Quick service check
echo System Services:
echo ==============
tasklist /fi "imagename eq python.exe" 2>nul | find /i "orchestrator" >nul
if %errorlevel%==0 (
    echo - Platinum Local Orchestrator: RUNNING
) else (
    echo - Platinum Local Orchestrator: NOT RUNNING
)

tasklist /fi "imagename eq python.exe" 2>nul | find /i "approval_executor" >nul
if %errorlevel%==0 (
    echo - Approval Executor: RUNNING
) else (
    echo - Approval Executor: NOT RUNNING
)

tasklist /fi "imagename eq python.exe" 2>nul | find /i "dashboard_merger" >nul
if %errorlevel%==0 (
    echo - Dashboard Merger: RUNNING
) else (
    echo - Dashboard Merger: NOT RUNNING
)

echo.
echo ================================================
echo Status check completed at %date% %time%
echo ================================================
pause