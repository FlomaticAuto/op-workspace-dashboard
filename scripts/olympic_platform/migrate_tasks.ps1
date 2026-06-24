<#
.SYNOPSIS
    Migrate Olympic-related scheduled tasks into \Olympic Paints\<AGENT>\,
    wrapping each action with run_job.py.

.PARAMETER DryRun
    Default. Prints the migration plan without changing Task Scheduler.

.PARAMETER Apply
    Performs the migration. Backs up each task's XML first.

.PARAMETER OnlyAgent
    Limit migration to a single agent (e.g. PULSE). Useful for phased rollout.
#>
[CmdletBinding(DefaultParameterSetName = 'DryRun')]
param(
    [Parameter(ParameterSetName = 'DryRun')]  [switch]$DryRun = $true,
    [Parameter(ParameterSetName = 'Apply')]   [switch]$Apply,
    [string]$OnlyAgent
)

$ErrorActionPreference = 'Stop'

# ---------- Config ----------
$WrapperPath  = '$env:USERPROFILE\workspace-dashboard\scripts\olympic_platform\run_job.py'
$MappingPath  = '$env:USERPROFILE\workspace-dashboard\scripts\olympic_platform\agent_mapping.json'
$BackupRoot   = '$env:USERPROFILE\.claude\heartbeats\_migration-backups'
$InScopePaths = @(
    'OneDrive\1.Projects\1.Olympic Paints',
    'workspace-dashboard',
    'olympic-paints-'
)

# ---------- Helpers ----------
function Get-AgentForCommand {
    param([string]$CommandText)
    $mapping = Get-Content $MappingPath -Raw | ConvertFrom-Json
    $lower   = $CommandText.ToLower()
    foreach ($rule in $mapping.rules) {
        if ($lower.Contains($rule.pattern.ToLower())) {
            return $rule.agent
        }
    }
    return $mapping.fallback_agent
}

function ConvertTo-JobId {
    param([string]$TaskName)
    $slug = $TaskName.ToLower()
    $slug = $slug -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    return $slug
}

function Test-InScope {
    param([string]$CommandText)
    foreach ($p in $InScopePaths) {
        if ($CommandText -like "*$p*") { return $true }
    }
    return $false
}

# ---------- Walk every task in the tree ----------
$svc = New-Object -ComObject Schedule.Service
$svc.Connect()

function Walk-Folder {
    param($Folder, [System.Collections.Generic.List[object]]$Acc)
    foreach ($t in $Folder.GetTasks(0)) { $Acc.Add($t) }
    foreach ($sub in $Folder.GetFolders(0)) { Walk-Folder -Folder $sub -Acc $Acc }
}
$all = New-Object System.Collections.Generic.List[object]
Walk-Folder -Folder $svc.GetFolder('\') -Acc $all

# ---------- Build the plan ----------
$plan = @()
foreach ($task in $all) {
    if ($task.Path -like '\Microsoft\*') { continue }
    if ($task.Path -like '\Olympic Paints\*') { continue }  # already migrated

    $def = $task.Definition
    if ($def.Actions.Count -eq 0) { continue }

    $action = $def.Actions.Item(1)
    $cmdText = "$($action.Path) $($action.Arguments)"
    if (-not (Test-InScope $cmdText)) { continue }

    $agent = Get-AgentForCommand $cmdText
    if ($OnlyAgent -and ($agent -ne $OnlyAgent)) { continue }

    $name   = Split-Path $task.Path -Leaf
    $jobId  = ConvertTo-JobId -TaskName $name

    $plan += [pscustomobject]@{
        OldPath = $task.Path
        NewPath = "\Olympic Paints\$agent\$name"
        Agent   = $agent
        JobId   = $jobId
        Action  = $cmdText
    }
}

# ---------- Print or apply ----------
if ($plan.Count -eq 0) {
    Write-Host 'No in-scope tasks found.' -ForegroundColor Yellow
    return
}

Write-Host ("Migration plan: {0} task(s)" -f $plan.Count) -ForegroundColor Cyan
$plan | Format-Table OldPath, NewPath, Agent, JobId -AutoSize

if (-not $Apply) {
    Write-Host 'Dry run only. Re-run with -Apply to migrate.' -ForegroundColor Green
    return
}

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupDir = Join-Path $BackupRoot $timestamp
New-Item -ItemType Directory -Force $backupDir | Out-Null
Write-Host "Backups -> $backupDir" -ForegroundColor Cyan

# Ensure \Olympic Paints\<AGENT> folders exist
$opRoot = $svc.GetFolder('\')
try { $opRoot.CreateFolder('Olympic Paints') | Out-Null } catch {}
$op = $svc.GetFolder('\Olympic Paints')
foreach ($agent in ($plan | Select-Object -ExpandProperty Agent -Unique)) {
    try { $op.CreateFolder($agent) | Out-Null } catch {}
}

$migrated = @()
$failed   = @()
$skipped  = @()

foreach ($item in $plan) {
    Write-Host ("=> {0}  ->  {1}" -f $item.OldPath, $item.NewPath) -ForegroundColor Yellow

    try {
        # 1. Resolve old task and back up XML
        $oldFolderPath = Split-Path $item.OldPath -Parent
        if ([string]::IsNullOrEmpty($oldFolderPath)) { $oldFolderPath = '\' }
        $oldFolder = $svc.GetFolder($oldFolderPath)
        $oldName   = Split-Path $item.OldPath -Leaf
        $oldTask   = $oldFolder.GetTask($oldName)

        $safeName  = ($oldName -replace '[\\/:*?"<>|]', '_')
        $xmlPath   = Join-Path $backupDir "$safeName.xml"
        schtasks /Query /TN $item.OldPath.TrimStart('\') /XML | Out-File -Encoding utf8 $xmlPath
        if ($LASTEXITCODE -ne 0) {
            throw "schtasks /Query failed (exit $LASTEXITCODE) for $($item.OldPath); backup not written"
        }
        # Sidecar with exact original name so restore_tasks.ps1 can recover it
        # losslessly (filename sanitization can drop characters).
        [IO.File]::WriteAllText(
            (Join-Path $backupDir "$safeName.name.txt"),
            $oldName,
            [System.Text.Encoding]::UTF8
        )

        # 2. Clone definition and rewrite the action
        $oldDef  = $oldTask.Definition
        $newDef  = $svc.NewTask(0)
        $newDef.RegistrationInfo.Description = $oldDef.RegistrationInfo.Description
        $newDef.Principal.UserId   = $oldDef.Principal.UserId
        $newDef.Principal.LogonType = $oldDef.Principal.LogonType
        $newDef.Principal.RunLevel  = $oldDef.Principal.RunLevel
        $newDef.Settings.Enabled    = $oldDef.Settings.Enabled
        $newDef.Settings.MultipleInstances = $oldDef.Settings.MultipleInstances
        $newDef.Settings.StartWhenAvailable = $oldDef.Settings.StartWhenAvailable
        $newDef.Settings.StopIfGoingOnBatteries = $oldDef.Settings.StopIfGoingOnBatteries
        $newDef.Settings.DisallowStartIfOnBatteries = $oldDef.Settings.DisallowStartIfOnBatteries

        # Trigger types: 2=daily, 3=weekly, 4=monthly, 5=monthly-day-of-week.
        # Copy type-specific fields so cadence is preserved exactly.
        foreach ($t in $oldDef.Triggers) {
            $clone = $newDef.Triggers.Create($t.Type)
            $clone.StartBoundary = $t.StartBoundary
            $clone.Enabled       = $t.Enabled
            if ($t.Repetition) {
                $clone.Repetition.Interval = $t.Repetition.Interval
                $clone.Repetition.Duration = $t.Repetition.Duration
            }
            switch ($t.Type) {
                2 { $clone.DaysInterval = $t.DaysInterval }                                    # daily
                3 { $clone.DaysOfWeek = $t.DaysOfWeek; $clone.WeeksInterval = $t.WeeksInterval } # weekly
                4 { $clone.MonthsOfYear = $t.MonthsOfYear; $clone.DaysOfMonth = $t.DaysOfMonth } # monthly
                5 {
                    $clone.MonthsOfYear  = $t.MonthsOfYear
                    $clone.WeeksOfMonth  = $t.WeeksOfMonth
                    $clone.DaysOfWeek    = $t.DaysOfWeek
                }
            }
            try { if ($null -ne $t.RandomDelay) { $clone.RandomDelay = $t.RandomDelay } } catch {}
        }

        $oldAction = $oldDef.Actions.Item(1)
        $origPath  = $oldAction.Path
        $origArgs  = $oldAction.Arguments
        $origWd    = $oldAction.WorkingDirectory

        # Guard rail: embedded double-quotes in $origArgs would break the
        # rewritten Arguments string. The migration is reversible (see backup),
        # but we skip rather than produce a malformed task.
        if ($origArgs -and ($origArgs.Contains('"'))) {
            $skipped += [pscustomobject]@{
                OldPath = $item.OldPath
                Reason  = "Original Arguments contain embedded quotes; rewrite would be malformed. Migrate manually."
            }
            Write-Host '   SKIPPED: embedded quotes in original Arguments.' -ForegroundColor Magenta
            continue
        }

        $newAction = $newDef.Actions.Create(0)
        $newAction.Path = 'python'
        $newAction.Arguments = "`"$WrapperPath`" $($item.JobId) --agent $($item.Agent) -- `"$origPath`" $origArgs"
        $newAction.WorkingDirectory = $origWd

        # 3. Register at new path
        $targetFolder = $svc.GetFolder("\Olympic Paints\$($item.Agent)")
        $targetFolder.RegisterTaskDefinition(
            $oldName,
            $newDef,
            6,        # TASK_CREATE_OR_UPDATE
            $null, $null, 3
        ) | Out-Null

        # 4. Verify
        $verify = $targetFolder.GetTask($oldName)
        if (-not $verify) {
            throw "Verification failed: new task not found at $($item.NewPath)"
        }

        # 5. Delete old (only after the new task is verified registered)
        $oldFolder.DeleteTask($oldName, 0)
        Write-Host '   migrated.' -ForegroundColor Green
        $migrated += $item.OldPath
    }
    catch {
        $failed += [pscustomobject]@{
            OldPath = $item.OldPath
            Error   = $_.Exception.Message
        }
        Write-Host ("   FAILED: {0}" -f $_.Exception.Message) -ForegroundColor Red
        # Continue with the next task; partial-batch state is recoverable via the backup dir.
    }
}

Write-Host ("Migrated: {0}   Skipped: {1}   Failed: {2}   Backups: {3}" -f $migrated.Count, $skipped.Count, $failed.Count, $backupDir) -ForegroundColor Cyan
if ($skipped.Count -gt 0) {
    Write-Host "Skipped tasks:" -ForegroundColor Magenta
    $skipped | Format-Table OldPath, Reason -AutoSize -Wrap
}
if ($failed.Count -gt 0) {
    Write-Host "Failed tasks:" -ForegroundColor Red
    $failed | Format-Table OldPath, Error -AutoSize -Wrap
    Write-Host ("To roll back this batch: powershell -File restore_tasks.ps1 -BackupDir '{0}' -Apply" -f $backupDir) -ForegroundColor Yellow
    exit 1
}
