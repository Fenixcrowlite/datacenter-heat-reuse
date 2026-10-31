[CmdletBinding()]
param(
    [ValidateRange(1024,65535)][int]$Port = 8091,
    [string]$Python = 'C:\Python314\python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$scriptPath = Join-Path $projectRoot 'scada_server.py'
$runtimePath = Join-Path $projectRoot 'runtime'
$identityPath = Join-Path $runtimePath 'server.json'
if (Test-Path -LiteralPath (Join-Path $projectRoot 'STOP')) {
    throw 'Persisted STOP exists. Start refused; STOP is never removed by this script. Inspect it and explicitly remove it yourself only when simulation replay is authorized.'
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Python executable not found. Set -Python to an installed Python 3.14 executable.' }
if (-not (Test-Path -LiteralPath $scriptPath -PathType Leaf)) { throw 'scada_server.py is missing.' }
New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
if (Test-Path -LiteralPath $identityPath) {
    try {
        $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
        $existingPid = [int]$identity.pid
        $existing = Get-CimInstance Win32_Process -Filter "ProcessId = $existingPid" -ErrorAction SilentlyContinue
        if ($existing -and $existing.CommandLine -and $existing.CommandLine.Contains($scriptPath)) {
            throw 'A SCADA-owned process already exists. Use its recorded local port or stop_scada.ps1; duplicate launch refused.'
        }
    } catch {
        if ($_.Exception.Message -like '*duplicate launch refused*') { throw }
        Write-Warning 'Previous identity record is stale or unreadable; the server will still enforce exclusive port binding.'
    }
}
$launchArguments = @('-u', ('"' + $scriptPath + '"'))
if ($PSBoundParameters.ContainsKey('Port')) { $launchArguments += @('--port', [string]$Port) }
$process = Start-Process -FilePath $Python -ArgumentList $launchArguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimePath 'stdout.log') -RedirectStandardError (Join-Path $runtimePath 'stderr.log')
$deadline = [DateTime]::UtcNow.AddSeconds(8)
while ([DateTime]::UtcNow -lt $deadline) {
    Start-Sleep -Milliseconds 250
    $process.Refresh()
    if ($process.HasExited) { throw 'SCADA exited during startup. Inspect runtime/scada.log and runtime/stderr.log; no other process was stopped.' }
    try {
        $identity = Get-Content -LiteralPath $identityPath -Raw | ConvertFrom-Json
        if ([int]$identity.pid -ne $process.Id) { continue }
        $readyPort = [int]$identity.port
        if ($readyPort -lt 1024 -or $readyPort -gt 65535) { continue }
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$readyPort/api/health" -TimeoutSec 1
        if ($health.instance_id -eq $identity.instance_id -and [int]$health.pid -eq $process.Id) {
            Write-Host "SCADA ready: http://127.0.0.1:$readyPort/ | LOCAL SIMULATION ONLY | D_SYNTHETIC"
            Write-Host 'Stop safely: .\stop_scada.ps1 (creates persistent STOP).'
            exit 0
        }
    } catch { }
}
throw 'Readiness was not confirmed within 8 seconds. Inspect runtime logs. The script did not kill any process.'
