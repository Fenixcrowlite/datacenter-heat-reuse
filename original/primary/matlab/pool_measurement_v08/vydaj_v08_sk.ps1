$ErrorActionPreference='Stop'
$root='C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse'
$code=Join-Path $root 'matlab\pool_measurement_v08'
$out=Join-Path $root 'results\pool_measurement_v08'
$vault='C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\pool_500m3\pool_measurement_v08'
$qa=Get-Content (Join-Path $out 'QA_NEZAVISLA_V08_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
$r=Get-Content (Join-Path $out 'vysledky_v08_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
$input=Get-Content (Join-Path $out 'D_REPLAY_INPUT_MANIFEST.json') -Raw -Encoding UTF8|ConvertFrom-Json
if($qa.status -ne 'PASS' -or $qa.checks -ne 91565 -or $r.cases.Count -ne 8 -or $input.scenario_count -ne 8){throw 'QA or manifest incomplete'}
if($r.classification -ne 'D_SYNTHETIC_NO_REAL_SENSOR_MEASUREMENT'){throw 'Provenance mismatch'}
$oldV85=Join-Path $root 'matlab\simulink\DCHR_Electrical_Dispatch_Stateflow_v85.slx'
$oldV07=Join-Path $root 'matlab\pool_redundancy_v07\DC_Bazen_Dvojita_Ochrana_v07_SK.slx'
if((Get-FileHash $oldV85).Hash -ne '2A9DE22C0C55E8C4A87F7B0E0CFE9CD97DB08C991F09D98361B009DE310ADDE7'){throw 'Original v85 changed'}
if((Get-FileHash $oldV07).Hash -ne $qa.models_sha256.'matlab/pool_redundancy_v07/DC_Bazen_Dvojita_Ochrana_v07_SK.slx'.ToUpper()){throw 'Original v07 changed since QA'}
$csv=Get-ChildItem $out -Filter 'sim_v08_*_SK.csv' -File
$pdf=Get-ChildItem $out -Filter 'DC_Bazen_Externe_Merania_v08_*.pdf' -File
if($csv.Count -ne 8 -or $pdf.Count -ne 3){throw 'Outputs missing'}
$releaseStatus=@{status='VERIFIED_SIMULINK_D_REPLAY_INDEPENDENT_QA_PASS';qa_checks=$qa.checks;provenance='D_SYNTHETIC_NOT_FIELD_MEASUREMENT'}
$releaseStatus|ConvertTo-Json -Depth 8|Set-Content (Join-Path $out 'RELEASE_STATUS_v08_SK.json') -Encoding UTF8
$all=@(
@(Join-Path $root 'docs\pool_measurement_v08\Matematika_integracia_merani_v08_SK.md','Matematika_integracia_merani_v08_SK.md'),
@(Join-Path $root 'POOL_MEASUREMENT_V08_HANDOFF_20261023.md','POOL_MEASUREMENT_V08_HANDOFF_20261023.md')
)
# Explicit file pairs: project and stable basename, no source overwrites.
$all=@()
$all+=,@((Join-Path $root 'docs\pool_measurement_v08\Matematika_integracia_merani_v08_SK.md'),'Matematika_integracia_merani_v08_SK.md')
$all+=,@((Join-Path $root 'POOL_MEASUREMENT_V08_HANDOFF_20261023.md'),'POOL_MEASUREMENT_V08_HANDOFF_20261023.md')
foreach($x in @('DC_Bazen_Externe_Merania_v08_SK.slx','vytvor_model_merani_v08_sk.m',
 'bezpecnostne_meranie_externe_v08.txt','oprav_vstup_merani_v08_sk.m',
 'priprav_D_replay_v08.py','spusti_merania_replay_v08_sk.m','qa_nezavisla_v08_sk.py',
 'neistoty_merania_v08_sk.py','grafy_v08_sk.py','vytvor_pdf_v08_3jazyky.py')){
 $all+=,@((Join-Path $code $x),$x)
}
foreach($x in @('vysledky_v08_SK.json','QA_NEZAVISLA_V08_SK.json','NEISTOTY_MERANIA_V08_SK.json',
 'D_REPLAY_INPUT_MANIFEST.json','externe_snimace_v08_SK.png','regresia_tepla_v08_SK.png',
 'DC_Bazen_Externe_Merania_v08_SK.pdf','DC_Bazen_Externe_Merania_v08_EN.pdf',
 'DC_Bazen_Externe_Merania_v08_RU.pdf')){
 $all+=,@((Join-Path $out $x),$x)
}
$count=0
foreach($pair in $all){
 $src=$pair[0];$dst=Join-Path $vault $pair[1]
 if(!(Test-Path $src)){throw "Missing $src"}
 if(Test-Path $dst){throw "Refuse overwrite $dst"}
 Copy-Item -LiteralPath $src -Destination $dst
 if((Get-FileHash $src -Algorithm SHA256).Hash -ne (Get-FileHash $dst -Algorithm SHA256).Hash){throw "Hash mismatch $dst"}
 $count++
}
foreach($sub in @('source_D','staged_D')){
 $s=Join-Path $out $sub;$t=Join-Path $vault $sub
 if(Test-Path $t){throw "Refuse existing data folder $t"}
 Copy-Item -LiteralPath $s -Destination $t -Recurse
 foreach($f in (Get-ChildItem $s -Recurse -File)){
  $rel=$f.FullName.Substring($s.Length+1);$copy=Join-Path $t $rel
  if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash $copy).Hash){throw "D source hash mismatch $rel"}
  $count++
 }
}
$dstCsv=Join-Path $vault 'simulation_csv'
if(Test-Path $dstCsv){throw 'simulation_csv already present'}
New-Item $dstCsv -ItemType Directory|Out-Null
foreach($f in $csv){
 $target=Join-Path $dstCsv $f.Name
 Copy-Item $f.FullName $target
 if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash $target).Hash){throw "CSV hash failed $($f.Name)"}
 $count++
}
$bundle=Join-Path $out 'RELEASE_v08_SK_EN_RU'
if(Test-Path $bundle){throw 'Existing release folder'}
New-Item $bundle -ItemType Directory|Out-Null
Get-ChildItem $vault -File|Copy-Item -Destination $bundle
foreach($sub in @('source_D','staged_D','simulation_csv')){
 Copy-Item (Join-Path $vault $sub) (Join-Path $bundle $sub) -Recurse
}
$manifest=@('RelativePath,SHA256,Bytes')
foreach($item in (Get-ChildItem $bundle -Recurse -File)){
 $relative=$item.FullName.Substring($bundle.Length+1)
 $manifest+=($relative+','+(Get-FileHash $item.FullName -Algorithm SHA256).Hash+','+$item.Length)
}
$manifest|Set-Content (Join-Path $bundle 'SHA256_MANIFEST.csv') -Encoding UTF8
$archive=Join-Path $out 'DC_Bazen_Externe_Merania_v08_SK_EN_RU.zip'
if(Test-Path $archive){throw 'Already exists ZIP'}
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $archive -CompressionLevel Optimal
Write-Output "V08_RELEASE_PASS 8_SIMULINK 91565_QA 3_PDF 8_CSV D_INPUTS_ONLY HASHED=$count SIZE=$((Get-Item $archive).Length)"
Write-Output "ARCHIVE=$archive"
