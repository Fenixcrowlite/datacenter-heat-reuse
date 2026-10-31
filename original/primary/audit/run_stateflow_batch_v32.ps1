param([Parameter(Mandatory=$true)][string]$Operation,[string]$SpecDirectory='')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logPath="automation/logs/stateflow_${Operation}_v32_console_${stamp}.log"
$receiptPath="audit/Stateflow_execution_v32_${Operation}_${stamp}.json"
$command="addpath('audit'); run_stateflow_v32_batch('$Operation','$SpecDirectory')"
$ErrorActionPreference='Continue'
& 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe' -batch $command 2>&1 | Tee-Object -FilePath $logPath
$matlabExit=$LASTEXITCODE
$ErrorActionPreference='Stop'
@{timestamp_utc=(Get-Date).ToUniversalTime().ToString('o');command=$command;exit_code=$matlabExit;log_path=$logPath;evidence_class='observed_matlab_batch_receipt'} | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output "RECEIPT=$receiptPath"
exit $matlabExit
