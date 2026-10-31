$ErrorActionPreference='Stop'
$root='C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse'
$code=Join-Path $root 'matlab\pool_safety_v05'
$data=Join-Path $root 'results\pool_safety_v05'
$vault='C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\pool_500m3\pool_safety_v05'
$old=Join-Path $root 'matlab\simulink\DCHR_Electrical_Dispatch_Stateflow_v85.slx'
$hash=(Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash
if($hash -ne '2A9DE22C0C55E8C4A87F7B0E0CFE9CD97DB08C991F09D98361B009DE310ADDE7'){throw 'Original v85 hash changed'}
$j=Get-Content (Join-Path $data 'resultaty_v05_SK.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$q=Get-Content (Join-Path $data 'QA_V05_SK.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($j.scenarios.Count -ne 7 -or $q.status -ne 'PASS' -or $q.checks -ne 32928){throw 'QA acceptance failed'}
$items=@(
@((Join-Path $root 'docs\pool_safety_v05\Bezpecnost_a_poruchy_bazena_v05_SK.md'),'Bezpecnost_a_poruchy_bazena_v05_SK.md'),
@((Join-Path $root 'POOL_SAFETY_V05_HANDOFF_20261023.md'),'POOL_SAFETY_V05_HANDOFF_20261023.md'),
@((Join-Path $code 'DC_Bazen_Bezpecnost_v05_SK.slx'),'DC_Bazen_Bezpecnost_v05_SK.slx'),
@((Join-Path $code 'vytvor_model_bezpecnost_v05_sk.m'),'vytvor_model_bezpecnost_v05_sk.m'),
@((Join-Path $code 'spusti_poruchy_v05_sk.m'),'spusti_poruchy_v05_sk.m'),
@((Join-Path $code 'pool_safety_gate_v05.txt'),'pool_safety_gate_v05.txt'),
@((Join-Path $code 'QA_v05_sk.py'),'QA_v05_sk.py'),
@((Join-Path $code 'grafy_v05_sk.py'),'grafy_v05_sk.py'),
@((Join-Path $data 'resultaty_v05_SK.json'),'resultaty_v05_SK.json'),
@((Join-Path $data 'QA_V05_SK.json'),'QA_V05_SK.json'),
@((Join-Path $data 'interlock_timeline_v05_SK.png'),'interlock_timeline_v05_SK.png'),
@((Join-Path $data 'teplota_poruchy_v05_SK.png'),'teplota_poruchy_v05_SK.png'),
@((Join-Path $data 'Bezpecnost_bazena_v05_SK.pdf'),'Bezpecnost_bazena_v05_SK.pdf'),
@((Join-Path $data 'Bezpecnost_bazena_v05_EN.pdf'),'Bezpecnost_bazena_v05_EN.pdf'),
@((Join-Path $data 'Bezpecnost_bazena_v05_RU.pdf'),'Bezpecnost_bazena_v05_RU.pdf'))
foreach($pair in $items){
 $src=$pair[0];$dest=Join-Path $vault $pair[1]
 if(!(Test-Path -LiteralPath $src)){throw "Missing source: $src"}
 if(Test-Path -LiteralPath $dest){throw "Do not overwrite vault: $dest"}
 Copy-Item -LiteralPath $src -Destination $dest
 if((Get-FileHash $src).Hash -ne (Get-FileHash $dest).Hash){throw "Vault SHA mismatch: $dest"}
}
$csvDest=Join-Path $vault 'scenare_csv'
New-Item -Path $csvDest -ItemType Directory -Force|Out-Null
$csv=Get-ChildItem -LiteralPath $data -Filter 'scenar_*_SK.csv' -File
if($csv.Count -ne 7){throw 'Missing CSV series'}
foreach($file in $csv){
 Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $csvDest $file.Name)
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $csvDest $file.Name)).Hash){throw "CSV hash: $file"}
}
$bundle=Join-Path $data 'RELEASE_v05'
if(Test-Path $bundle){throw 'Bundle already exists'}
New-Item -Path $bundle -ItemType Directory -Force|Out-Null
Get-ChildItem -LiteralPath $vault -File | Copy-Item -Destination $bundle
New-Item -ItemType Directory -Path (Join-Path $bundle 'scenare_csv')|Out-Null
Get-ChildItem -LiteralPath $csvDest -File|Copy-Item -Destination (Join-Path $bundle 'scenare_csv')
$manifest=@('RelativePath,SHA256,Bytes')
Get-ChildItem $bundle -Recurse -File |ForEach-Object{
 $rel=$_.FullName.Substring($bundle.Length+1)
 $manifest+=($rel+','+(Get-FileHash $_.FullName).Hash+','+$_.Length)
}
$manifest|Set-Content -LiteralPath (Join-Path $bundle 'SHA256_MANIFEST.csv') -Encoding UTF8
$zip=Join-Path $data 'DC_Bazen_Safety_v05_SK_EN_RU.zip'
if(Test-Path $zip){throw 'Archive exists'}
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $zip -CompressionLevel Optimal
Write-Output "RELEASE_PASS 7 SIM 32928 QA 3 PDF v85 UNCHANGED CSV=$($csv.Count) ZIP=$zip SIZE=$((Get-Item $zip).Length)"
