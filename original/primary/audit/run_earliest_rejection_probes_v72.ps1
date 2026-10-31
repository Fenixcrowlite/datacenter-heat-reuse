param([Parameter(Mandatory=$true)][string]$Folder)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$targetFolder=(Resolve-Path -LiteralPath $Folder).Path
if (-not $targetFolder.StartsWith((Join-Path $projectRoot 'results')+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Evidence must stay in project/results.' }
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logPath=Join-Path $targetFolder "diagnostic_matlab_${stamp}.log"
$command="addpath('matlab');run_earliest_rejection_probes_v72('$Folder');"
$ErrorActionPreference='Continue'
& 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe' -batch $command 2>&1 | Tee-Object -FilePath $logPath
$matlabExit=$LASTEXITCODE
$ErrorActionPreference='Stop'
@{timestamp_utc=(Get-Date).ToUniversalTime().ToString('o');command=$command;exit_code=$matlabExit;log_path=$logPath;evidence_class='INSTRUMENTED_HOST_REPLAY_ONLY_NOT_STATEFLOW'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $targetFolder "diagnostic_execution_${stamp}.json") -Encoding utf8
exit $matlabExit
