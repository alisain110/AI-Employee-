@echo off
REM Platinum Tier Step-by-Step Demo Script
REM Guides user through the complete demo process

echo =================================================
echo Platinum Tier Step-by-Step Demo
echo =================================================
echo This script will guide you through the complete
echo demo process from email arrival to final execution.
echo =================================================
echo.

:step1
echo Step 1: Send test email to yourself
echo -------------------------------------
echo Please send an email from another account to your monitored email address.
echo Subject: "Demo Test: Please Reply"
echo Body: "This is a test email for the Platinum Tier demo. Please send me a reply."
echo.
set /p input="Press Enter when you have sent the test email..."

:step2
echo.
echo Step 2: Wait for cloud to detect and draft reply
echo -----------------------------------------------
echo Watching cloud orchestrator logs for email detection...
echo.
echo Please monitor the cloud side for:
echo - "New email detected" message
echo - Draft reply creation
echo - Approval request generation in Pending_Approval/cloud/
echo.
echo Press Enter when you see the approval file created in Pending_Approval/cloud/...
pause

:step3
echo.
echo Step 3: Git sync to local machine
echo ----------------------------------
echo Performing git pull to sync approval file to local machine...
git pull origin main
if %errorlevel% neq 0 (
    echo Warning: Git pull failed. Please check your git configuration.
    pause
) else (
    echo Git sync completed successfully.
    echo.
    echo Verifying approval file in Pending_Approval/cloud/:
    dir Pending_Approval\cloud\ /b
)
echo.
set /p input="Press Enter when you have verified the approval file is present..."

:step4
echo.
echo Step 4: Approve the request
echo ----------------------------
echo Moving approval file from Pending_Approval/cloud/ to Approved/ to trigger execution...
echo.
echo Files in Pending_Approval/cloud/:
dir Pending_Approval\cloud\ /b
echo.

REM Get the first approval file
for /f "delims=" %%i in ('dir Pending_Approval\cloud\ /b') do set "approval_file=%%i"
if defined approval_file (
    echo Moving %approval_file% to Approved/...
    move "Pending_Approval\cloud\%approval_file%" "Approved\"
    echo.
    echo File moved. Approval executor should now process the request.
) else (
    echo No approval files found in Pending_Approval/cloud/
    echo Please verify the file was created on the cloud side.
    pause
    goto end
)

:step5
echo.
echo Step 5: Monitor execution
echo -------------------------
echo Watching approval executor logs for email sending...
echo.
echo Please monitor the logs for:
echo - "Processing approved request"
echo - "Email sent successfully"
echo - Dashboard updates
echo - File movement to Done/
echo.
echo Press Enter when the email reply has been sent and logged...
pause

:step6
echo.
echo Step 6: Verify final results
echo ----------------------------
echo Checking Dashboard.md for updates...
if exist Dashboard.md (
    echo.
    echo Recent Dashboard entries:
    powershell -command "Get-Content Dashboard.md | Select-Object -First 20"
) else (
    echo Dashboard.md not found - may need to wait for dashboard merger
)

echo.
echo Files in Done/ directory:
dir Done\ /b

echo.
echo Demo process completed!
echo Please verify:
echo 1. Email reply was sent successfully
echo 2. Dashboard.md was updated with the activity
echo 3. Approval file was moved to Done/ directory
echo 4. All logs show successful execution

:end
echo.
echo =================================================
echo Demo Session Complete
echo See PLATINUM_TIER_DEMO_SCRIPT.md for details
echo =================================================
pause