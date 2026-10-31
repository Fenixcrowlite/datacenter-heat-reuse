param([Parameter(Mandatory=$true)][string]$Command)
# Local test launcher only; no agent runner/scheduler changes.
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$stamp=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$logPath="automation/logs/reporting_v45_${stamp}.log"
$receiptPath="audit/Reporting_execution_v45_${stamp}.json"
$ErrorActionPreference='Continue'
& 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe' -batch $Command 2>&1 | Tee-Object -FilePath $logPath
$matlabExit=$LASTEXITCODE
$ErrorActionPreference='Stop'
@{timestamp_utc=(Get-Date).ToUniversalTime().ToString('o');command=$Command;exit_code=$matlabExit;log_path=$logPath;evidence_class='observed_matlab_batch_receipt'} | ConvertTo-Json | Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Output "RECEIPT=$receiptPath"
exit $matlabExit
