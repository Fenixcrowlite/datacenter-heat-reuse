$ErrorActionPreference='Stop'
$root='C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse'
$code=Join-Path $root 'matlab\pool_failure_v06'
$out=Join-Path $root 'results\pool_failure_v06'
$vault='C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\pool_500m3\pool_failure_v06'
$orig=Join-Path $root 'matlab\simulink\DCHR_Electrical_Dispatch_Stateflow_v85.slx'
$sha=(Get-FileHash $orig -Algorithm SHA256).Hash
if($sha -ne '2A9DE22C0C55E8C4A87F7B0E0CFE9CD97DB08C991F09D98361B009DE310ADDE7'){
 throw 'Original v85 was modified: abort release'
}
$qa=Get-Content (Join-Path $out 'QA_NEZAVISLA_V06_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
$sc=Get-Content (Join-Path $out 'vysledky_v06_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
if($qa.status -ne 'PASS' -or $qa.test_assertions -ne 84801 -or $sc.scenarios.Count -ne 7){throw 'Incomplete QA'}
if((Get-ChildItem $out -Filter 'scenar_*_SK.csv').Count -ne 7){throw 'Missing scenario CSV'}
# Mark status only after independent QA passed.
$sc.status='VERIFIED_SIMULINK_SYNTHETIC_V06_INDEPENDENT_QA_PASS'
$sc|ConvertTo-Json -Depth 25|Set-Content (Join-Path $out 'vysledky_v06_SK.json') -Encoding UTF8
$files=@(
@((Join-Path $root 'docs\pool_failure_v06\Matematika_a_fyzikalne_poruchy_v06_SK.md'),'Matematika_a_fyzikalne_poruchy_v06_SK.md'),
@((Join-Path $root 'POOL_FAILURE_V06_HANDOFF_20261023.md'),'POOL_FAILURE_V06_HANDOFF_20261023.md'),
@((Join-Path $code 'DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx'),'DC_Bazen_Fyzikalne_Poruchy_v06_SK.slx'),
@((Join-Path $code 'vytvor_model_v06_sk.m'),'vytvor_model_v06_sk.m'),
@((Join-Path $code 'spusti_poruchove_scenare_v06_sk.m'),'spusti_poruchove_scenare_v06_sk.m'),
@((Join-Path $code 'bezpecnostne_meranie_v06.txt'),'bezpecnostne_meranie_v06.txt'),
@((Join-Path $code 'fyzikalne_poruchy_v06.txt'),'fyzikalne_poruchy_v06.txt'),
@((Join-Path $code 'qa_v06_sk.py'),'qa_v06_sk.py'),
@((Join-Path $code 'grafy_v06_sk.py'),'grafy_v06_sk.py'),
@((Join-Path $code 'vytvor_pdf_v06_sk_en_ru.py'),'vytvor_pdf_v06_sk_en_ru.py'),
@((Join-Path $out 'vysledky_v06_SK.json'),'vysledky_v06_SK.json'),
@((Join-Path $out 'QA_NEZAVISLA_V06_SK.json'),'QA_NEZAVISLA_V06_SK.json'),
@((Join-Path $out 'povel_vs_prietok_v06_SK.png'),'povel_vs_prietok_v06_SK.png'),
@((Join-Path $out 'teplota_IT_riziko_v06_SK.png'),'teplota_IT_riziko_v06_SK.png'),
@((Join-Path $out 'DC_Bazen_Fyzikalne_Poruchy_v06_SK.pdf'),'DC_Bazen_Fyzikalne_Poruchy_v06_SK.pdf'),
@((Join-Path $out 'DC_Bazen_Fyzikalne_Poruchy_v06_EN.pdf'),'DC_Bazen_Fyzikalne_Poruchy_v06_EN.pdf'),
@((Join-Path $out 'DC_Bazen_Fyzikalne_Poruchy_v06_RU.pdf'),'DC_Bazen_Fyzikalne_Poruchy_v06_RU.pdf'))
foreach($a in $files){
 $src=$a[0];$dst=Join-Path $vault $a[1]
 if(-not(Test-Path -LiteralPath $src)){throw "Missing: $src"}
 if(Test-Path -LiteralPath $dst){throw "Refusing overwrite: $dst"}
 Copy-Item -LiteralPath $src -Destination $dst
 if((Get-FileHash $src).Hash -ne (Get-FileHash $dst).Hash){throw "Hash mismatch: $dst"}
}
$csvDir=Join-Path $vault 'scenare_csv'
New-Item -ItemType Directory $csvDir -Force|Out-Null
$csv=Get-ChildItem $out -Filter 'scenar_*_SK.csv'
foreach($item in $csv){
 $dst=Join-Path $csvDir $item.Name
 if(Test-Path $dst){throw 'Existing scenario'}
 Copy-Item -LiteralPath $item.FullName -Destination $dst
 if((Get-FileHash $item.FullName).Hash -ne (Get-FileHash $dst).Hash){throw "CSV hash: $dst"}
}
$bundle=Join-Path $out 'Release_v06_SK_EN_RU'
if(Test-Path $bundle){throw 'Release folder already exists'}
New-Item -ItemType Directory $bundle -Force|Out-Null
Get-ChildItem $vault -File|Copy-Item -Destination $bundle
New-Item -ItemType Directory (Join-Path $bundle 'scenare_csv')|Out-Null
Get-ChildItem $csvDir -File|Copy-Item -Destination (Join-Path $bundle 'scenare_csv')
$manifest=@('Path,SHA256,Bytes')
Get-ChildItem $bundle -Recurse -File|ForEach-Object{
 $rel=$_.FullName.Substring($bundle.Length+1)
 $manifest+=($rel+','+(Get-FileHash $_.FullName).Hash+','+$_.Length)
}
$manifest|Set-Content (Join-Path $bundle 'SHA256_MANIFEST.csv') -Encoding UTF8
$zip=Join-Path $out 'DC_Bazen_v06_SK_EN_RU.zip'
if(Test-Path $zip){throw 'ZIP exists'}
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $zip -CompressionLevel Optimal
Write-Output "V06_RELEASE_PASS 7_SCENARIOS 84801_ASSERTIONS 3_PDF HASH_CHECKED SIZE=$((Get-Item $zip).Length) ZIP=$zip"
Write-Output "VAULT=$vault"
