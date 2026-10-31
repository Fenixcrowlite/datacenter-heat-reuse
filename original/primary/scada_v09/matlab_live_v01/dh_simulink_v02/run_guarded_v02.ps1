# Safe MATLAB batch launcher. No STOP removal or unrelated PID termination.
[CmdletBinding()]
param([int]$RequiredFreeRamMB = 7168, [int]$TimeoutSeconds = 420)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$live = Split-Path -Parent $here
$scada = Split-Path -Parent $live
$base = Join-Path $scada '..\matlab\pool_feedback_v04\DC_Bazen_Uzavreta_Regulacia_v04_SK.slx'
$expected = '0D9A59466A0284CA6BB61D6756222DCCAFC2AC7AA683AE41DE35CE6D72F94EE0'
$mat = 'C:\Program Files\MATLAB\R2026a\bin\matlab.exe'
$source = Join-Path $here 'build_and_run_dh_v02.m'
$log = Join-Path $here 'guarded_batch.log'
if ((Test-Path (Join-Path $scada 'STOP')) -or (Test-Path (Join-Path $live 'STOP'))) {throw 'STOP active: refusing to run'}
if (!(Test-Path $source) -or !(Test-Path $mat)) {throw 'Missing own MATLAB source or executable'}
if (!(Test-Path $base) -or (Get-FileHash $base -Algorithm SHA256).Hash -ne $expected) {throw 'Base model SHA256 mismatch'}
$ram = [int][math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
if ($ram -lt $RequiredFreeRamMB) {
    Write-Output "BLOCKED_RAM: $ram MB available; requires at least $RequiredFreeRamMB MB."
    exit 3
}
if (Test-Path (Join-Path $here 'runtime\run_20261025\release.json')) {throw 'Release already exists; refusing overwrite'}
$scriptArg = "run('" + ($source.Replace('\', '/')) + "')"
Write-Output "START_OWNED_MATLAB free_ram_mb=$ram"
$p = Start-Process -FilePath $mat -ArgumentList @('-batch', ('"' + $scriptArg + '"')) -WorkingDirectory $here -WindowStyle Hidden -PassThru -RedirectStandardOutput $log -RedirectStandardError (Join-Path $here 'guarded_batch_stderr.log')
$start = Get-Date
while (!$p.HasExited) {
    Start-Sleep -Seconds 2
    $p.Refresh()
    $current = [int][math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
    if ((Test-Path (Join-Path $scada 'STOP')) -or
        (Test-Path (Join-Path $live 'STOP')) -or
        ((Get-Date) - $start).TotalSeconds -gt $TimeoutSeconds -or $current -lt 256) {
        $owned = Get-CimInstance Win32_Process | Where-Object {
            $_.ParentProcessId -eq $p.Id -and $_.CommandLine -like '*build_and_run_dh_v02.m*'
        }
        foreach ($child in $owned) {Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue}
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        throw 'Owned batch was stopped (STOP, timeout, or critical memory); inspect logs'
    }
}
if ($p.ExitCode -ne 0) {throw "MATLAB batch failed ($($p.ExitCode)); inspect guarded_batch.log"}
if (!(Test-Path (Join-Path $here 'runtime\run_20261025\release.json'))) {throw 'MATLAB finished but no verified release exists'}
Write-Output 'SIMULINK_DH_V02_RELEASE_READY'
