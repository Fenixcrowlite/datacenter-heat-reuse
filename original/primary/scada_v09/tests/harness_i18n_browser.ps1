[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$chrome='C:\Program Files\Google\Chrome\Application\chrome.exe'
if(!(Test-Path $chrome)){throw 'Google Chrome unavailable for browser acceptance'}
$out=Join-Path $root 'runtime\i18n_qa'
New-Item -ItemType Directory -Path $out -Force|Out-Null
$expect=@{
 ru=@('Мнемосхема','Тепловой контур','СИМУЛЯЦИЯ','Температура бассейна','Сравнение сценариев');
 sk=@('Synoptická schéma','Tepelný okruh','SIMULÁCIA','Teplota bazéna','Porovnanie scenárov');
 en=@('Synoptic view','Thermal circuit','SIMULATION','Pool temperature','Scenario comparison')
}
foreach($lang in @('ru','sk','en')){
 $profile=Join-Path $out "profile_$lang"
 $html=Join-Path $out "QA_$lang.html"
 $screenshot=Join-Path $out "QA_$lang.png"
 # Read only the local verified SCADA. No external URLs, no PLC interaction.
 $url="http://127.0.0.1:8091/?lang=$lang"
 $args=@('--headless=new','--disable-gpu','--disable-extensions','--no-first-run',
    '--disable-background-networking',"--user-data-dir=$profile",
    '--window-size=1600,950','--virtual-time-budget=4100',"--screenshot=$screenshot",
    '--dump-dom',$url)
 $captured=& $chrome @args 2>&1
 $raw=($captured|Out-String)
 $start=$raw.IndexOf('<!DOCTYPE html>')
 if($start -lt 0){$start=$raw.IndexOf('<html')}
 if($start -lt 0){throw "Browser DOM missing in $lang"}
 $raw=$raw.Substring($start)
 [System.IO.File]::WriteAllText($html,$raw,(New-Object System.Text.UTF8Encoding($false)))
 foreach($needle in $expect[$lang]){
  if(!$raw.Contains($needle)){throw "$lang browser missing expected label: $needle"}
 }
 if(!$raw.Contains('D_SYNTHETIC') -or !$raw.Contains('language-select') -or !$raw.Contains('hardware-lock')){throw "$lang no safety and language marker"}
 if(!(Test-Path $screenshot) -or (Get-Item $screenshot).Length -lt 40000){throw "$lang screenshot missing"}
 Write-Output "I18N_BROWSER_PASS lang=$lang screenshot_bytes=$((Get-Item $screenshot).Length) HTML_chars=$($raw.Length)"
}
Write-Output 'I18N_BROWSER_3_LANGUAGES_PASS'
