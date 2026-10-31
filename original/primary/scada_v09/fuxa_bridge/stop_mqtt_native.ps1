# Set persistent STOP, wait for own worker to shutdown, never kill foreign ports.
$ErrorActionPreference='Stop'
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$flag=Join-Path $here 'STOP'
if(!(Test-Path $flag)){[IO.File]::WriteAllText($flag,"Owner STOP "+[DateTime]::UtcNow.ToString('o'))}
$idfile=Join-Path $here 'runtime\mqtt_pid.json'
if(!(Test-Path $idfile)){'STOP set, no PID record';return}
$info=Get-Content $idfile -Raw|ConvertFrom-Json
$p=Get-CimInstance Win32_Process -Filter "ProcessId=$($info.pid)" -ErrorAction SilentlyContinue
if(!$p){'STOP set, MQTT stopped';return}
$script=Join-Path $here 'run_stack.cjs'
if($p.Name -ne 'node.exe' -or $p.CommandLine -notlike ('*'+$script+'*')){throw 'STOP set but PID has foreign owner, no kill'}
Start-Sleep -Seconds 3
$p=Get-CimInstance Win32_Process -Filter "ProcessId=$($info.pid)" -ErrorAction SilentlyContinue
if($p){throw 'STOP set; owned runtime did not terminate automatically. Manual inspection required.'}
'STOP set; MQTT exited cleanly.'
