param([Parameter(Mandatory=$true)][string]$Folder)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$targetFolder=(Resolve-Path -LiteralPath $Folder).Path
$allowedRoot=Join-Path $projectRoot 'results'
if (-not $targetFolder.StartsWith($allowedRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Evidence must stay in workspace/results.' }
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logPath=Join-Path $targetFolder "matlab_${stamp}.log"
$command="addpath('matlab');run_charge_record_v61('$Folder');run_stateflow_finite_v57('$Folder/stateflow');"
$ErrorActionPreference='Continue'
& 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe' -batch $command 2>&1 | Tee-Object -FilePath $logPath
$matlabExit=$LASTEXITCODE
$ErrorActionPreference='Stop'
$receipt=@{timestamp_utc=(Get-Date).ToUniversalTime().ToString('o');command=$command;exit_code=$matlabExit;log_path=$logPath;evidence_class='OBSERVED_LOCAL_MATLAB_BATCH';scope='Correlated charge record and saved v57 Stateflow'} | ConvertTo-Json
$receipt | Set-Content -LiteralPath (Join-Path $targetFolder "execution_${stamp}.json") -Encoding utf8
$receipt | Set-Content -LiteralPath (Join-Path $targetFolder "stateflow/execution_${stamp}.json") -Encoding utf8
exit $matlabExit

