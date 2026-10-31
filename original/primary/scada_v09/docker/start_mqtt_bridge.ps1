# Foreground only, on explicit user invocation. No service or autostart is installed.
[CmdletBinding()]
param([string]$Python = 'C:\Python314\python.exe')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path -LiteralPath (Join-Path $projectRoot 'STOP')) { throw 'Persisted STOP exists. MQTT export is disabled.' }
$envPath = Join-Path $projectRoot '.env'
if (-not (Test-Path -LiteralPath $envPath)) { throw 'Optional .env is missing. Run docker/bootstrap.ps1 explicitly or set environment credentials and invoke mqtt_bridge.py directly.' }
$allowed = @('SCADA_URL','SCADA_MQTT_HOST','SCADA_MQTT_PORT','SCADA_MQTT_USERNAME','SCADA_MQTT_PASSWORD')
$priorValues = @{}
try {
    foreach ($line in [System.IO.File]::ReadAllLines($envPath)) {
        if ($line -match '^([A-Z_]+)=(.*)$' -and $allowed -contains $Matches[1]) {
            $name = $Matches[1]
            $priorValues[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
            [Environment]::SetEnvironmentVariable($name, $Matches[2], 'Process')
        }
    }
    & $Python (Join-Path $projectRoot 'mqtt_bridge.py')
    $bridgeExit = $LASTEXITCODE
} finally {
    foreach ($name in $priorValues.Keys) { [Environment]::SetEnvironmentVariable($name, $priorValues[$name], 'Process') }
}
exit $bridgeExit
