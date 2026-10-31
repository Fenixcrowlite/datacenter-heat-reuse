# Safe startup of local synthetic MATLAB v04 bridge. Never removes STOP.
$ErrorActionPreference='Stop'
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$scada=Split-Path -Parent $here
if((Test-Path (Join-Path $scada 'STOP')) -or (Test-Path (Join-Path $here 'STOP'))){throw 'STOP detected; no startup. Only owner may inspect and clear it manually.'}
$py='C:\Python314\python.exe';$script=Join-Path $here 'live_bridge.py'
if(!(Test-Path $py) -or !(Test-Path $script)){throw 'Python or bridge missing'}
$listen=Get-NetTCPConnection -State Listen -LocalPort 8094 -ErrorAction SilentlyContinue
if($listen){
 try{$h=Invoke-RestMethod 'http://127.0.0.1:8094/api/health' -TimeoutSec 3;if($h.ok){'Bridge already responding: http://127.0.0.1:8094/';return}}catch{}
 throw 'Port 8094 occupied by an unverified process: refusing to interfere'
}
$out=Join-Path $here 'bridge_stdout.log';$err=Join-Path $here 'bridge_stderr.log'
$p=Start-Process -FilePath $py -ArgumentList @('"' + $script + '"') -WorkingDirectory $here -PassThru -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
Start-Sleep -Seconds 2
try{$h=Invoke-RestMethod 'http://127.0.0.1:8094/api/health' -TimeoutSec 3
 if(!$h.ok){throw 'Health not healthy'}}catch{throw "Bridge not ready (PID $($p.Id)): $($_.Exception.Message)"}
"VERIFIED bridge PID $($p.Id): http://127.0.0.1:8094/"
