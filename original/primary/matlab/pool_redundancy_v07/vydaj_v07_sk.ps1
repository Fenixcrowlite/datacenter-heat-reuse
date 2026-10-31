$ErrorActionPreference='Stop'
$root='C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse'
$code=Join-Path $root 'matlab\pool_redundancy_v07'
$out=Join-Path $root 'results\pool_redundancy_v07'
$vault='C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\pool_500m3\pool_redundancy_v07'
$qa=Get-Content (Join-Path $out 'QA_NEZAVISLA_V07_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
$summary=Get-Content (Join-Path $out 'vysledky_v07_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
if($qa.status -ne 'PASS' -or $qa.checks -ne 129251 -or $summary.cases.Count -ne 8){throw 'QA gate rejects v07 release'}
$expectedV85='2A9DE22C0C55E8C4A87F7B0E0CFE9CD97DB08C991F09D98361B009DE310ADDE7'
$v85=Join-Path $root 'matlab\simulink\DCHR_Electrical_Dispatch_Stateflow_v85.slx'
if((Get-FileHash $v85 -Algorithm SHA256).Hash -ne $expectedV85){throw 'Original v85 changed'}
$cases=Get-ChildItem $out -Filter 'scenar_*_SK.csv' -File
$pdfs=Get-ChildItem $out -Filter 'DC_Bazen_Dvojita_Ochrana_v07_*.pdf' -File
if($cases.Count -ne 8 -or $pdfs.Count -ne 3){throw 'CSV or PDFs missing'}
$summary.status='VERIFIED_SIMULINK_SYNTHETIC_V07_INDEPENDENT_QA_PASS'
$summary|ConvertTo-Json -Depth 25|Set-Content (Join-Path $out 'vysledky_v07_SK.json') -Encoding UTF8
$inputs=@(
@((Join-Path $root 'docs\pool_redundancy_v07\Matematika_redundancia_a_bilancie_v07_SK.md'),'Matematika_redundancia_a_bilancie_v07_SK.md'),
@((Join-Path $root 'docs\pool_redundancy_v07\Import_skutocnych_merani_SK.md'),'Import_skutocnych_merani_SK.md'),
@((Join-Path $root 'POOL_REDUNDANCY_V07_HANDOFF_20261023.md'),'POOL_REDUNDANCY_V07_HANDOFF_20261023.md'),
@((Join-Path $code 'DC_Bazen_Dvojita_Ochrana_v07_SK.slx'),'DC_Bazen_Dvojita_Ochrana_v07_SK.slx'),
@((Join-Path $code 'vytvor_model_v07_sk.m'),'vytvor_model_v07_sk.m'),
@((Join-Path $code 'spusti_scenare_v07_sk.m'),'spusti_scenare_v07_sk.m'),
@((Join-Path $code 'uprava_zataze_IT_v07.txt'),'uprava_zataze_IT_v07.txt'),
@((Join-Path $code 'fyzikalne_ochrany_v07.txt'),'fyzikalne_ochrany_v07.txt'),
@((Join-Path $code 'qa_nezavisla_v07_sk.py'),'qa_nezavisla_v07_sk.py'),
@((Join-Path $code 'grafy_v07_sk.py'),'grafy_v07_sk.py'),
@((Join-Path $code 'vytvor_pdf_v07_3jazyky.py'),'vytvor_pdf_v07_3jazyky.py'),
@((Join-Path $code 'kontrola_vstupnych_merani_v07.py'),'kontrola_vstupnych_merani_v07.py'),
@((Join-Path $code 'test_schema_merani_v07.py'),'test_schema_merani_v07.py'),
@((Join-Path $code 'merania_15min_SABLONA.csv'),'merania_15min_SABLONA.csv'),
@((Join-Path $code 'metadane_merania_SABLONA.json'),'metadane_merania_SABLONA.json'),
@((Join-Path $out 'vysledky_v07_SK.json'),'vysledky_v07_SK.json'),
@((Join-Path $out 'QA_NEZAVISLA_V07_SK.json'),'QA_NEZAVISLA_V07_SK.json'),
@((Join-Path $out 'ventily_a_redundancia_v07_SK.png'),'ventily_a_redundancia_v07_SK.png'),
@((Join-Path $out 'IT_riziko_v07_SK.png'),'IT_riziko_v07_SK.png'),
@((Join-Path $out 'DC_Bazen_Dvojita_Ochrana_v07_SK.pdf'),'DC_Bazen_Dvojita_Ochrana_v07_SK.pdf'),
@((Join-Path $out 'DC_Bazen_Dvojita_Ochrana_v07_EN.pdf'),'DC_Bazen_Dvojita_Ochrana_v07_EN.pdf'),
@((Join-Path $out 'DC_Bazen_Dvojita_Ochrana_v07_RU.pdf'),'DC_Bazen_Dvojita_Ochrana_v07_RU.pdf'))
foreach($a in $inputs){
 $source=$a[0];$destination=Join-Path $vault $a[1]
 if(-not(Test-Path -LiteralPath $source)){throw "Missing: $source"}
 if(Test-Path -LiteralPath $destination){throw "Refuse existing: $destination"}
 Copy-Item -LiteralPath $source -Destination $destination
 if((Get-FileHash $source).Hash -ne (Get-FileHash $destination).Hash){throw "Vault hash mismatch: $destination"}
}
$csvdest=Join-Path $vault 'scenare_csv'
New-Item $csvdest -ItemType Directory|Out-Null
foreach($file in $cases){
 $dst=Join-Path $csvdest $file.Name
 Copy-Item -LiteralPath $file.FullName -Destination $dst
 if((Get-FileHash $file.FullName).Hash -ne (Get-FileHash $dst).Hash){throw "CSV SHA-256 mismatch"}
}
$bundle=Join-Path $out 'Release_v07_SK_EN_RU'
if(Test-Path $bundle){throw 'Release dir exists'}
New-Item $bundle -ItemType Directory|Out-Null
Get-ChildItem $vault -File|Copy-Item -Destination $bundle
New-Item (Join-Path $bundle 'scenare_csv') -ItemType Directory|Out-Null
Get-ChildItem $csvdest -File|Copy-Item -Destination (Join-Path $bundle 'scenare_csv')
$manifest=@('RelativePath,SHA256,Bytes')
Get-ChildItem $bundle -File -Recurse|ForEach-Object{
 $rel=$_.FullName.Substring($bundle.Length+1)
 $manifest+=($rel+','+(Get-FileHash $_.FullName -Algorithm SHA256).Hash+','+$_.Length)
}
$manifest|Set-Content (Join-Path $bundle 'SHA256_MANIFEST.csv') -Encoding UTF8
$zip=Join-Path $out 'DC_Bazen_v07_SK_EN_RU.zip'
if(Test-Path $zip){throw 'Release zip exists'}
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $zip -CompressionLevel Optimal
Write-Output "V07_RELEASE_PASS 8_SIMULINK 129251_QA 3_PDF 8_CSV SYNTHETIC_D ZIP=$zip BYTES=$((Get-Item $zip).Length)"
Write-Output "VAULT=$vault"
