<#
.SYNOPSIS
    One-shot admin-elevated cleanup of the 3 Task Scheduler stragglers from
    the 2026-05-16 bulk migration.

.DESCRIPTION
    Three tasks were originally created by an elevated process and rejected
    modification by the non-admin user during automated migration:

      1. \Vehicle Report Weekly                                -- duplicate (clean wrapped copy already at \Olympic Paints\SIGMA\Vehicle Report Weekly)
      2. \VAULT Meeting Extraction Daily                       -- duplicate (clean wrapped copy already at \Olympic Paints\VAULT\VAULT Meeting Extraction Daily)
      3. \Olympic Paints\Olympic Paints - Meeting Minutes Extractor -- never migrated; this script wraps it and moves it under VAULT

    This script must run in an elevated PowerShell session (Run as Administrator).

.PARAMETER WhatIf
    Default. Reports what would be done without changing Task Scheduler.

.PARAMETER Apply
    Performs the cleanup.
#>
[CmdletBinding(DefaultParameterSetName='WhatIf')]
param(
    [Parameter(ParameterSetName='WhatIf')] [switch]$WhatIf = $true,
    [Parameter(ParameterSetName='Apply')]  [switch]$Apply
)

$ErrorActionPreference = 'Stop'

# Elevation check (Windows PowerShell 5.1)
$me = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($me)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script must be run in an ELEVATED PowerShell session." -ForegroundColor Red
    Write-Host "Right-click PowerShell -> Run as administrator, then re-run." -ForegroundColor Yellow
    exit 1
}

$svc = New-Object -ComObject Schedule.Service
$svc.Connect()

$wrapper   = '$env:USERPROFILE\workspace-dashboard\scripts\olympic_platform\run_job.py'
$backupDir = "$env:USERPROFILE\.claude\heartbeats\_migration-backups\cleanup-{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss')

if (-not $Apply) {
    Write-Host "DRY RUN -- re-run with -Apply to perform the cleanup." -ForegroundColor Green
    Write-Host "Will perform:" -ForegroundColor Cyan
    Write-Host "  1. Delete root duplicate: \Vehicle Report Weekly"
    Write-Host "  2. Delete root duplicate: \VAULT Meeting Extraction Daily"
    Write-Host "  3. Migrate \Olympic Paints\Olympic Paints - Meeting Minutes Extractor"
    Write-Host "         -> \Olympic Paints\VAULT\Meeting Minutes Extractor (wrapped via run_job.py)"
    Write-Host "  Backups will be written to: $backupDir"
    exit 0
}

New-Item -ItemType Directory -Force $backupDir | Out-Null
Write-Host "Backups -> $backupDir" -ForegroundColor Cyan

# ---------- Helpers ----------
function Backup-Task($oldPath, $safeName) {
    $xml = Join-Path $backupDir "$safeName.xml"
    schtasks /Query /TN $oldPath.TrimStart('\') /XML | Out-File -Encoding utf8 $xml
    if ($LASTEXITCODE -ne 0) { throw "schtasks /Query failed for $oldPath" }
    [IO.File]::WriteAllText((Join-Path $backupDir "$safeName.name.txt"), $oldPath, [System.Text.Encoding]::UTF8)
}

function Build-WrappedDef($oldTask, $newArgs) {
    $old = $oldTask.Definition
    $new = $svc.NewTask(0)
    $new.RegistrationInfo.Description = $old.RegistrationInfo.Description
    $new.Principal.UserId   = $old.Principal.UserId
    $new.Principal.LogonType = $old.Principal.LogonType
    $new.Principal.RunLevel  = $old.Principal.RunLevel
    $new.Settings.Enabled    = $old.Settings.Enabled
    $new.Settings.MultipleInstances = $old.Settings.MultipleInstances
    $new.Settings.StartWhenAvailable = $old.Settings.StartWhenAvailable
    $new.Settings.StopIfGoingOnBatteries = $old.Settings.StopIfGoingOnBatteries
    $new.Settings.DisallowStartIfOnBatteries = $old.Settings.DisallowStartIfOnBatteries
    foreach ($t in $old.Triggers) {
        $c = $new.Triggers.Create($t.Type)
        $c.StartBoundary = $t.StartBoundary
        $c.Enabled = $t.Enabled
        if ($t.Repetition) {
            $c.Repetition.Interval = $t.Repetition.Interval
            $c.Repetition.Duration = $t.Repetition.Duration
        }
        switch ($t.Type) {
            2 { $c.DaysInterval = $t.DaysInterval }
            3 { $c.DaysOfWeek = $t.DaysOfWeek; $c.WeeksInterval = $t.WeeksInterval }
            4 { $c.MonthsOfYear = $t.MonthsOfYear; $c.DaysOfMonth = $t.DaysOfMonth }
            5 { $c.MonthsOfYear = $t.MonthsOfYear; $c.WeeksOfMonth = $t.WeeksOfMonth; $c.DaysOfWeek = $t.DaysOfWeek }
            8 { try { $c.Delay = $t.Delay } catch {} }
            9 { try { $c.UserId = $t.UserId } catch {}; try { $c.Delay = $t.Delay } catch {} }
        }
    }
    $a = $new.Actions.Create(0)
    $a.Path = 'python'
    $a.Arguments = $newArgs
    $a.WorkingDirectory = $old.Actions.Item(1).WorkingDirectory
    return $new
}

# ---------- 1. Delete \Vehicle Report Weekly ----------
Write-Host "=> Deleting \Vehicle Report Weekly (root duplicate)..." -ForegroundColor Yellow
try {
    Backup-Task '\Vehicle Report Weekly' 'Vehicle_Report_Weekly_root_dup'
    $svc.GetFolder('\').DeleteTask('Vehicle Report Weekly', 0)
    Write-Host "   deleted." -ForegroundColor Green
} catch {
    Write-Host "   SKIP: $($_.Exception.Message) (already gone?)" -ForegroundColor DarkGray
}

# ---------- 2. Delete \VAULT Meeting Extraction Daily ----------
Write-Host "=> Deleting \VAULT Meeting Extraction Daily (root duplicate)..." -ForegroundColor Yellow
try {
    Backup-Task '\VAULT Meeting Extraction Daily' 'VAULT_Meeting_Extraction_Daily_root_dup'
    $svc.GetFolder('\').DeleteTask('VAULT Meeting Extraction Daily', 0)
    Write-Host "   deleted." -ForegroundColor Green
} catch {
    Write-Host "   SKIP: $($_.Exception.Message) (already gone?)" -ForegroundColor DarkGray
}

# ---------- 3. Migrate Meeting Minutes Extractor to \VAULT\Meeting Minutes Extractor ----------
Write-Host "=> Migrating Meeting Minutes Extractor -> \Olympic Paints\VAULT\Meeting Minutes Extractor..." -ForegroundColor Yellow
try {
    $oldFolder = $svc.GetFolder('\Olympic Paints')
    $oldTask   = $oldFolder.GetTask('Olympic Paints - Meeting Minutes Extractor')
    Backup-Task '\Olympic Paints\Olympic Paints - Meeting Minutes Extractor' 'Meeting_Minutes_Extractor'

    $bat     = '$env:USERPROFILE\OneDrive\1.Projects\1.Olympic Paints\run_meeting_extractor.bat'
    $newArgs = "`"$wrapper`" meeting-minutes-extractor --agent VAULT -- `"$bat`""
    $def     = Build-WrappedDef $oldTask $newArgs

    try { $svc.GetFolder('\Olympic Paints').CreateFolder('VAULT') | Out-Null } catch {}
    $vault = $svc.GetFolder('\Olympic Paints\VAULT')
    $vault.RegisterTaskDefinition('Meeting Minutes Extractor', $def, 6, $null, $null, 3) | Out-Null
    if (-not $vault.GetTask('Meeting Minutes Extractor')) { throw 'Verify failed' }

    $oldFolder.DeleteTask('Olympic Paints - Meeting Minutes Extractor', 0)
    Write-Host "   migrated and old deleted." -ForegroundColor Green
} catch {
    Write-Host "   FAILED: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Backup remains at $backupDir for manual recovery." -ForegroundColor Yellow
}

# ---------- Summary ----------
Write-Host "`n=== Final tree under \Olympic Paints\ ===" -ForegroundColor Cyan
function Walk($folder, $depth) {
    foreach ($t in $folder.GetTasks(0)) {
        ('  ' * $depth) + $t.Path
    }
    foreach ($sub in $folder.GetFolders(0)) {
        ('  ' * $depth) + "[$($sub.Name)]"
        Walk $sub ($depth + 1)
    }
}
Walk $svc.GetFolder('\Olympic Paints') 0

Write-Host "`nRefresh the manifest:" -ForegroundColor Cyan
Write-Host "  cd $env:USERPROFILE\workspace-dashboard"
Write-Host "  python -m scripts.olympic_platform.build_schedule_manifest"
