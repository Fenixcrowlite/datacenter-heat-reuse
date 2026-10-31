$ErrorActionPreference = 'Stop'
$Source = 'C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse'
$Destination = 'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse'

New-Item -ItemType Directory -Force -Path $Destination | Out-Null

# Add/update project files, but do not delete extra files from OneDrive.
robocopy $Source $Destination /E /XO /FFT /R:2 /W:1 /XD '.git' '__pycache__' /XF '*.asv' '*.autosave' | Out-Host
$code = $LASTEXITCODE
if ($code -ge 8) { throw "Robocopy failed with exit code $code" }
Write-Host "Synced to $Destination (robocopy code $code)"
