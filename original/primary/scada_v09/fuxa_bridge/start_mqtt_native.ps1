# Start owned, local D_SYNTHETIC MQTT broker/publisher. No Docker or PLC.
$ErrorActionPreference='Stop'
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
if((Test-Path (Join-Path $here 'STOP')) -or (Test-Path (Join-Path $here '..\STOP'))){throw 'STOP active; manual review required'}
if(Get-NetTCPConnection -State Listen -LocalPort 18883 -ErrorAction SilentlyContinue){throw 'MQTT port already occupied, refuse duplicate'}
$node='C:\Program Files\nodejs\node.exe'
if(!(Test-Path $node)){throw 'Node.js missing'}
$secrets=Join-Path $here 'runtime\secrets.json'
if(Test-Path $secrets){
 $user=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
 & icacls $secrets /inheritance:r /grant:r "${user}:(F)" '*S-1-5-18:(F)' '*S-1-5-32-544:(F)' | Out-Null
 if($LASTEXITCODE -ne 0){throw 'Cannot protect local credentials'}
}
$out=Join-Path $here 'runtime\mqtt_stdout.log';$err=Join-Path $here 'runtime\mqtt_stderr.log'
$p=Start-Process -FilePath $node -ArgumentList @('"' + (Join-Path $here 'run_stack.cjs') + '"') -WorkingDirectory $here -PassThru -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
Start-Sleep -Seconds 2
if(!(Get-NetTCPConnection -State Listen -LocalPort 18883 -ErrorAction SilentlyContinue)){throw "MQTT failed, inspect logs. PID $($p.Id)"}
[IO.File]::WriteAllText((Join-Path $here 'runtime\mqtt_pid.json'),("{""pid"":"+$p.Id+"}"))
"MQTT loopback READY, PID $($p.Id); retained data are synthetic."
