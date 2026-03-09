# ==============================================================================
#  Setup-EdgeMonitor.ps1
#  Run ONCE as Administrator to register the Task Scheduler job
#  and create the directory structure.
#
#  Usage:
#    powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\Setup-EdgeMonitor.ps1
# ==============================================================================

#Requires -RunAsAdministrator

$SCRIPT_PATH  = "C:\Scripts\healthchecks.ps1"
$LOG_DIR      = "C:\Scripts\Logs"
$TASK_NAME    = "EdgeMonitor-Healthcheck"
$INTERVAL_MIN = 5   # Run every N minutes

Write-Host "=== Edge Monitor Setup ===" -ForegroundColor Cyan

# Create directories
foreach ($dir in @("C:\Scripts", $LOG_DIR)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

# Copy script if not already there
if (-not (Test-Path $SCRIPT_PATH)) {
    Write-Host "ERROR: Place healthchecks.ps1 at $SCRIPT_PATH first." -ForegroundColor Red
    exit 1
}

# Remove existing task if present
if (Get-ScheduledTask -TaskName $TASK_NAME -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TASK_NAME -Confirm:$false
    Write-Host "Removed existing task." -ForegroundColor Yellow
}

# Create the scheduled task
$action  = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -NonInteractive -WindowStyle Hidden -File `"$SCRIPT_PATH`""

$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes $INTERVAL_MIN) -Once -At (Get-Date)

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TASK_NAME `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Edge Monitor — sends structured healthcheck pings with full system telemetry" | Out-Null

Write-Host "Task registered: $TASK_NAME (every $INTERVAL_MIN min, runs as SYSTEM)" -ForegroundColor Green

# Run immediately to verify
Write-Host "`nRunning first check now..." -ForegroundColor Cyan
Start-ScheduledTask -TaskName $TASK_NAME
Start-Sleep -Seconds 5
$last = (Get-ScheduledTaskInfo -TaskName $TASK_NAME).LastTaskResult
Write-Host "Last result code: $last  (0 = success, 1 = degraded, 2 = ping failed)" -ForegroundColor $(if ($last -eq 0) {"Green"} else {"Yellow"})

Write-Host "`n=== Setup complete ===" -ForegroundColor Cyan
Write-Host "Logs : $LOG_DIR\edge-monitor.log"
Write-Host "JSONL: $LOG_DIR\edge-monitor-events.jsonl  (point Splunk UF here)"
