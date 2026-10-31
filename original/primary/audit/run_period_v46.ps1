param([Parameter(Mandatory=$true)][string]$Command)
# Local MATLAB test launcher, unrelated to the agent runner.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logPath="automation/logs/period_v46_${stamp}.log"
$receiptPath="audit/Period_execution_v46_${stamp}.json"
$ErrorActionPreference='Continue'
& 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe' -batch $Command 2>&1 | Tee-Object -FilePath $logPath
$matlabExit=$LASTEXITCODE
$ErrorActionPreference='Stop'
@{timestamp_utc=(Get-Date).ToUniversalTime().ToString('o');command=$Command;exit_code=$matlabExit;log_path=$logPath;evidence_class='observed_matlab_batch_receipt'} | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output "RECEIPT=$receiptPath"
exit $matlabExit
