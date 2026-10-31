$ErrorActionPreference='Stop'
$project=$PSScriptRoot
$root=Split-Path -Parent $project
$release=Join-Path $project 'release'
$bundle=Join-Path $release 'DC_SCADA_v09_PACKAGE'
$zip=Join-Path $release 'DC_SCADA_v09_SIMULATION_SK_RU.zip'
$vault='C:\Users\Lysda\Documents\Bimba\02_PROJECTS\02_Automation\DataCenter_Heat_Reuse\SCADA_v09'
if(Test-Path $bundle){throw 'Refuse existing release bundle'}
if(Test-Path $zip){throw 'Refuse existing zip'}
if(Test-Path $vault){throw 'Refuse existing vault folder'}
$qa=Get-Content (Join-Path $root 'results\pool_measurement_v08\QA_NEZAVISLA_V08_SK.json') -Raw -Encoding UTF8|ConvertFrom-Json
if($qa.status -ne 'PASS' -or $qa.checks -ne 91565 -or $qa.cases.Count -ne 8){throw 'Upstream QA not verified'}
$health=Invoke-RestMethod 'http://127.0.0.1:8091/api/health' -TimeoutSec 3
if(!$health.ok -or $health.metadata.source_class -ne 'D_SYNTHETIC'){throw 'SCADA not live'}
$files=@(
 'scada_server.py','mqtt_bridge.py','start_scada.ps1','stop_scada.ps1',
 'README_RU.md','ARCHITECTURE_SK.md','TEST_PLAN.md','CODEX_RESULT.md',
 'CODEX_TASK.md','docker-compose.yml','.gitignore',
 'web\index.html','web\styles.css','web\app.js','tests\test_server.py',
 'docker\acl','docker\mosquitto.conf','docker\bootstrap.ps1','docker\start_mqtt_bridge.ps1')
New-Item $bundle -ItemType Directory -Force|Out-Null
$count=0
foreach($name in $files){
 $src=Join-Path $project $name
 if(!(Test-Path $src -PathType Leaf)){throw "Missing $src"}
 $target=Join-Path $bundle $name
 New-Item (Split-Path -Parent $target) -ItemType Directory -Force|Out-Null
 Copy-Item -LiteralPath $src -Destination $target
 if((Get-FileHash $src).Hash -ne (Get-FileHash $target).Hash){throw "Hash mismatch $name"}
 $count++
}
$handoff=Join-Path $root 'SCADA_V09_HANDOFF_20261023.md'
if(!(Test-Path $handoff)){throw 'Missing handoff'}
Copy-Item $handoff (Join-Path $bundle 'SCADA_V09_HANDOFF_20261023.md')
$from=Join-Path $root 'results\pool_measurement_v08'
$to=Join-Path $bundle 'data\v08'
New-Item $to -ItemType Directory -Force | Out-Null
$csv=Get-ChildItem $from -File -Filter 'sim_v08_*_SK.csv'
if($csv.Count -ne 8){throw 'Missing scenario CSV'}
foreach($f in $csv){
 $target=Join-Path $to $f.Name
 Copy-Item -LiteralPath $f.FullName -Destination $target
 if((Get-FileHash $f.FullName).Hash -ne (Get-FileHash $target).Hash){throw "Source CSV hash mismatch"}
 $count++
}
Copy-Item (Join-Path $from 'QA_NEZAVISLA_V08_SK.json') (Join-Path $to 'QA_NEZAVISLA_V08_SK.json')
$photos=Join-Path $bundle 'QA_BROWSER'
New-Item $photos -ItemType Directory | Out-Null
foreach($n in @('QA_HMI_1600x940.png','QA_HMI_TABLET_920x1200.png')){
 $file=Join-Path $project "runtime\$n"
 if(!(Test-Path $file)){throw "Missing browser QA screenshot $n"}
 Copy-Item $file (Join-Path $photos $n)
}
New-Item $vault -ItemType Directory | Out-Null
foreach($n in @('README_RU.md','ARCHITECTURE_SK.md','TEST_PLAN.md','CODEX_RESULT.md')){
 Copy-Item (Join-Path $project $n) (Join-Path $vault $n)
}
Copy-Item $handoff (Join-Path $vault 'SCADA_V09_HANDOFF_20261023.md')
foreach($n in @('QA_HMI_1600x940.png','QA_HMI_TABLET_920x1200.png')){
 Copy-Item (Join-Path $photos $n) (Join-Path $vault $n)
}
$manifest=@('RelativePath,SHA256,Bytes')
foreach($f in Get-ChildItem -LiteralPath $bundle -File -Recurse){
 $relative=$f.FullName.Substring($bundle.Length+1)
 $manifest+=($relative+','+(Get-FileHash $f.FullName -Algorithm SHA256).Hash+','+$f.Length)
}
$manifest|Set-Content (Join-Path $bundle 'SHA256_MANIFEST.csv') -Encoding UTF8
Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $zip -CompressionLevel Optimal
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z=[IO.Compression.ZipFile]::OpenRead($zip);$entries=$z.Entries.Count;$z.Dispose()
if($entries -lt 25 -or (Get-Item $zip).Length -lt 100000){throw 'Zip QA failed'}
Copy-Item $zip (Join-Path $vault (Split-Path $zip -Leaf))
Write-Output "SCADA_RELEASE_PASS copies_SHA256=$count datasets=$($csv.Count) entries=$entries zip_bytes=$((Get-Item $zip).Length)"
Write-Output "ZIP=$zip"
Write-Output "VAULT=$vault"
