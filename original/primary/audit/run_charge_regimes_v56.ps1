param([Parameter(Mandatory=$true)][string]$Folder)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logPath=Join-Path $Folder "matlab_${stamp}.log"
$command="addpath('matlab');run_charge_regimes_v56('$Folder');"
$ErrorActionPreference='Continue'
& 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe' -batch $command 2>&1 | Tee-Object -FilePath $logPath
$matlabExit=$LASTEXITCODE
$ErrorActionPreference='Stop'
@{timestamp_utc=(Get-Date).ToUniversalTime().ToString('o');command=$command;exit_code=$matlabExit;log_path=$logPath} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Folder "execution_${stamp}.json") -Encoding utf8
exit $matlabExit
