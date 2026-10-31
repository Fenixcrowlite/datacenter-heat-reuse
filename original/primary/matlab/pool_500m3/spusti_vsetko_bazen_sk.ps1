# Spustenie kompletneho dodatku bazena, bez zasahu do modelov DCHR v85/v86.
param([switch]$BezMatlabu)
$ErrorActionPreference='Stop'
$priecinok=Split-Path -Parent $MyInvocation.MyCommand.Path
$projekt=Split-Path -Parent (Split-Path -Parent $priecinok)
$vysledky=Join-Path $projekt 'results\pool_500m3_v01'
$obsidian='C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\pool_500m3'
$matlab='C:\Program Files\MATLAB\R2026a\bin\matlab.exe'
New-Item -ItemType Directory -Force $vysledky | Out-Null
New-Item -ItemType Directory -Force $obsidian | Out-Null
python (Join-Path $priecinok 'pool_calc_report_sk.py')
if ($LASTEXITCODE -ne 0) { throw 'Zlyhal referencny vypocet v Pythone.' }
if (-not $BezMatlabu) {
    $a=(Join-Path $priecinok 'spusti_simulaciu_bazena_sk.m').Replace('\','/')
    & $matlab -batch "run('$a')" *>&1 | Tee-Object (Join-Path $vysledky 'matlab_spustenie.log')
    if ($LASTEXITCODE -ne 0) { throw 'Zlyhala prva simulacia MATLAB.' }
    $b=(Join-Path $priecinok 'spusti_scenare_bazena_sk.m').Replace('\','/')
    & $matlab -batch "run('$b')" *>&1 | Tee-Object (Join-Path $vysledky 'matlab_scenare.log')
    if ($LASTEXITCODE -ne 0) { throw 'Zlyhali dalsie scenare Simulink.' }
}
if (-not (Test-Path (Join-Path $vysledky 'simulink_scenare_SK.json'))) {
    throw 'Chybaju validovane Simulink vysledky pre rozsirovanie PDF.'
}
python (Join-Path $priecinok 'rozsir_technicke_pdf_sk.py')
if ($LASTEXITCODE -ne 0) { throw 'Zlyhalo rozsirenie PDF.' }
Copy-Item (Join-Path $projekt 'docs\pool_500m3\*.md') $obsidian -Force
Copy-Item (Join-Path $vysledky 'Bazen_500m3_*.pdf') $obsidian -Force
Copy-Item (Join-Path $vysledky 'simulink_*_SK.png') $obsidian -Force
Copy-Item (Join-Path $vysledky 'priebeh_teploty_simulink_SK.png') $obsidian -Force
Copy-Item (Join-Path $vysledky 'vysledky_bazen_500m3.json') $obsidian -Force
foreach($lang in @('SK','EN','RU')){
    $a=(Get-FileHash (Join-Path $vysledky "Bazen_500m3_$lang.pdf")).Hash
    $b=(Get-FileHash (Join-Path $obsidian "Bazen_500m3_$lang.pdf")).Hash
    if($a -ne $b){throw "Nesuhlasi hash PDF: $lang"}
}
Write-Host 'HOTOVO: kompletna simulacia, 3x PDF, Obsidian a hashe.' -ForegroundColor Green
