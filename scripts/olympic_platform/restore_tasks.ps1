<#
.SYNOPSIS
    Restore scheduled tasks from a migration backup directory.
    Use this only to roll back a migration.

.PARAMETER BackupDir
    Required. The timestamped folder under
    C:\Users\quint\.claude\heartbeats\_migration-backups\
#>
param(
    [Parameter(Mandatory = $true)] [string]$BackupDir,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $BackupDir)) {
    throw "Backup directory not found: $BackupDir"
}

$xmls = Get-ChildItem -Path $BackupDir -Filter *.xml
if ($xmls.Count -eq 0) { throw 'No .xml backups in that directory.' }

Write-Host ("Found {0} backed-up task XML files." -f $xmls.Count) -ForegroundColor Cyan
$xmls | ForEach-Object { Write-Host "  $($_.Name)" }

if (-not $Apply) {
    Write-Host 'Dry run only. Re-run with -Apply to restore.' -ForegroundColor Green
    return
}

foreach ($xml in $xmls) {
    # Prefer the .name.txt sidecar written by migrate_tasks.ps1 — it carries the
    # exact original task name including any characters that were sanitized out
    # of the XML filename. Fall back to the legacy underscore→space heuristic
    # for backups produced before the sidecar was introduced.
    $sidecar = Join-Path $xml.DirectoryName ([IO.Path]::GetFileNameWithoutExtension($xml.Name) + '.name.txt')
    if (Test-Path $sidecar) {
        $name = (Get-Content -Path $sidecar -Raw -Encoding UTF8).Trim()
    } else {
        $name = [IO.Path]::GetFileNameWithoutExtension($xml.Name)
        $name = $name -replace '_', ' '
        Write-Host ("  no sidecar for {0}; using heuristic name '{1}'" -f $xml.Name, $name) -ForegroundColor Yellow
    }
    Write-Host "Restoring '$name'..." -ForegroundColor Yellow
    schtasks /Create /XML $xml.FullName /TN $name /F
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("  schtasks /Create failed (exit {0}) for '{1}'" -f $LASTEXITCODE, $name) -ForegroundColor Red
    }
}
Write-Host 'Restore complete.' -ForegroundColor Cyan
