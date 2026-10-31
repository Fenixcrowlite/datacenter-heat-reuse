[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$scriptPath = Join-Path $projectRoot 'scada_server.py'
$stopPath = Join-Path $projectRoot 'STOP'
$identityPath = Join-Path $projectRoot 'runtime\server.json'
# This persisted flag is authoritative even if HTTP or process inspection fails.
if (-not (Test-Path -LiteralPath $stopPath)) {
    [System.IO.File]::WriteAllText($stopPath, ('Operator STOP ' + [DateTime]::UtcNow.ToString('o')), (New-Object System.Text.UTF8Encoding($false)))
}
if (-not (Test-Path -LiteralPath $identityPath)) {
    Write-Host 'STOP persisted. No owned SCADA identity record exists; no process was terminated.'
    exit 0
}
try {
    $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
    $serverPid = [int]$identity.pid
    $serverPort = [int]$identity.port
    if ($serverPid -le 0 -or $serverPort -lt 1024 -or $serverPort -gt 65535 -or -not $identity.instance_id) { throw 'Invalid SCADA identity record.' }
    $owned = Get-CimInstance Win32_Process -Filter "ProcessId = $serverPid" -ErrorAction Stop
    if (-not $owned -or -not $owned.CommandLine -or -not $owned.CommandLine.Contains($scriptPath)) { throw 'Recorded PID is not a verified SCADA-owned process.' }
    $base = "http://127.0.0.1:$serverPort"
    $health = Invoke-RestMethod -Uri "$base/api/health" -TimeoutSec 2
    if ($health.instance_id -ne $identity.instance_id -or [int]$health.pid -ne $serverPid) { throw 'Local HTTP identity does not match the SCADA process.' }
    $status = Invoke-RestMethod -Uri "$base/api/status" -TimeoutSec 2
    $token = $status.csrf_token
    if (-not $token -and $status.status) { $token = $status.status.csrf_token }
    if (-not $token) { throw 'Local simulation CSRF token unavailable.' }
    Invoke-RestMethod -Uri "$base/api/control" -Method Post -ContentType 'application/json' -Headers @{'X-SCADA-Token'=$token; 'Origin'=$base} -Body '{"action":"shutdown"}' -TimeoutSec 3 | Out-Null
    $token = $null
    Write-Host 'STOP persisted; graceful shutdown requested from verified local SCADA. No forced process termination was used.'
} catch {
    Write-Warning ('STOP persisted. Graceful shutdown could not be verified: ' + $_.Exception.Message)
    Write-Host 'Replay must remain paused by STOP. No process was killed; unrelated services were untouched.'
}
