# Registers the Olympic Paints Portal Trigger Server as a logon-time scheduled task.
# Run once as the user (no admin needed for user-scope task).

$TaskName  = "OlympicPortalTriggerServer"
$ScriptDir = "$env:USERPROFILE\workspace-dashboard\scripts"
$Python    = (Get-Command python).Source
$Script    = Join-Path $ScriptDir "portal_trigger_server.py"

# Action: run python on the trigger server
$Action = New-ScheduledTaskAction `
  -Execute $Python `
  -Argument "`"$Script`"" `
  -WorkingDirectory $ScriptDir

# Trigger: at user logon
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: restart on failure, allow on battery
$Settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -DontStopIfGoingOnBatteries `
  -AllowStartIfOnBatteries `
  -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

# Principal: run as current user, no elevation
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register (replaces any existing task of the same name)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask `
  -TaskName $TaskName `
  -Action $Action `
  -Trigger $Trigger `
  -Settings $Settings `
  -Principal $Principal `
  -Description "Local Flask trigger server for Olympic Paints workspace portal (regenerate-button backend)."

Write-Host "Registered task: $TaskName"
Write-Host "To start now without re-logging in, run:"
Write-Host "  Start-ScheduledTask -TaskName $TaskName"
