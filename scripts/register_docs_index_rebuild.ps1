# register_docs_index_rebuild.ps1
# Registers a weekly Task Scheduler job to sync .md files and rebuild the
# Docs Index table in the Control Tower. Runs every Wednesday at 06:00.

$TaskName   = "OlympicPaints_DocsIndex_WeeklyRebuild"
$Python     = "C:\Python313\python.exe"
$Script     = "C:\Users\Administrator\workspace-dashboard\scripts\rebuild_docs_index.py"
$WorkingDir = "C:\Users\Administrator\workspace-dashboard"
$LogFile    = "C:\Users\Administrator\workspace-dashboard\logs\docs_index_rebuild.log"

# Ensure log directory exists
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile) | Out-Null

$Action  = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c `"$Python`" `"$Script`" >> `"$LogFile`" 2>&1" `
    -WorkingDirectory $WorkingDir

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Wednesday -At "06:00"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask `
    -TaskName  $TaskName `
    -Action    $Action `
    -Trigger   $Trigger `
    -Settings  $Settings `
    -Principal $Principal `
    -Description "Weekly sync of .md files into docs/md/ and rebuild of Docs Index rows in Control Tower index.html. Commits and pushes to main." | Out-Null

Write-Host "Registered: $TaskName (Wednesdays 06:00)"
