# Only stop own synthetic bridge; persist local STOP for outstanding MATLAB job.
$ErrorActionPreference='Stop'
$here=Split-Path -Parent $MyInvocation.MyCommand.Path
$marker=Join-Path $here 'STOP'
if(!(Test-Path $marker)){[IO.File]::WriteAllText($marker,"Local MATLAB bridge STOP at "+[DateTime]::UtcNow.ToString('o'))}
$identity=Join-Path $here 'runtime\server.json'
if(!(Test-Path $identity)){'STOP set. No identity file found.';return}
$info=Get-Content $identity -Raw | ConvertFrom-Json
$p=Get-CimInstance Win32_Process -Filter "ProcessId=$($info.pid)" -ErrorAction SilentlyContinue
$expected=[IO.Path]::GetFullPath((Join-Path $here 'live_bridge.py'))
if(!$p){'STOP set. Bridge not running.';return}
if($p.Name -notin @('python.exe','pythonw.exe') -or $p.CommandLine -notlike ('*'+$expected+'*')){throw "STOP set; PID belongs to another process. Manual review required."}
# Running MATLAB job will observe this marker and terminate only its own subprocess.
Start-Sleep -Seconds 2
Stop-Process -Id $p.ProcessId -ErrorAction Stop
"STOP set; owned bridge PID $($info.pid) terminated. STOP not auto-cleared."
