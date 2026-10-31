# Explicit optional setup. Does not start Docker Desktop or any persistent service.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$secretDirectory = Join-Path $PSScriptRoot 'runtime'
$envPath = Join-Path $projectRoot '.env'
if ((Test-Path -LiteralPath $envPath) -or (Test-Path -LiteralPath (Join-Path $secretDirectory 'passwords'))) {
    throw 'Credentials already exist. Preserve them; bootstrap never silently rotates existing credentials.'
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker CLI is not installed. Native SCADA does not need Docker.' }
& docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker daemon is stopped. Start it yourself only if you want the optional stack, then run this script again.' }
New-Item -ItemType Directory -Path $secretDirectory -Force | Out-Null
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls $secretDirectory /inheritance:r /grant:r "${currentUser}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Could not restrict the local secret directory ACL.' }
function New-LocalSecret {
    $secretBytes = New-Object byte[] 32
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($secretBytes) } finally { $generator.Dispose() }
    return [Convert]::ToBase64String($secretBytes)
}
$exporterPassword = New-LocalSecret
$viewerPassword = New-LocalSecret
$grafanaPassword = New-LocalSecret
# Secrets go over stdin, never in the docker process arguments or console output.
$containerScript = @'
set -eu
umask 077
IFS= read -r exporter_password
IFS= read -r viewer_password
mosquitto_passwd -b -c /secrets/passwords scada_exporter "$exporter_password"
mosquitto_passwd -b /secrets/passwords fuxa_viewer "$viewer_password"
chmod 644 /secrets/passwords
'@
($exporterPassword + "`n" + $viewerPassword + "`n") | & docker run --rm -i --cap-drop=ALL --security-opt=no-new-privileges:true --mount "type=bind,source=$secretDirectory,target=/secrets" --entrypoint sh eclipse-mosquitto:2 -c $containerScript
if ($LASTEXITCODE -ne 0) { throw 'Password-file creation failed. No stack was started. Inspect docker/runtime before retrying.' }
$envContent = @"
# LOCAL SECRET: ignored by git; generated for optional simulation export only.
SCADA_URL=http://127.0.0.1:8091
SCADA_MQTT_HOST=127.0.0.1
SCADA_MQTT_PORT=18883
SCADA_MQTT_USERNAME=scada_exporter
SCADA_MQTT_PASSWORD=$exporterPassword
FUXA_MQTT_USERNAME=fuxa_viewer
FUXA_MQTT_PASSWORD=$viewerPassword
"@
[System.IO.File]::WriteAllText($envPath, $envContent, (New-Object System.Text.UTF8Encoding($false)))
& icacls $envPath /inheritance:r /grant:r "${currentUser}:(F)" '*S-1-5-18:(F)' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Could not restrict the .env ACL. Fix its permissions before using the optional bridge.' }
[System.IO.File]::WriteAllText((Join-Path $secretDirectory 'grafana_admin_password'), $grafanaPassword, (New-Object System.Text.UTF8Encoding($false)))
$exporterPassword = $null
$viewerPassword = $null
$grafanaPassword = $null
$envContent = $null
Write-Host 'Local credentials generated in ignored .env and docker/runtime. No persistent service was started.'
Write-Host 'Optional next step, when explicitly wanted: docker compose --profile fuxa up -d'
