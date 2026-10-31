$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:8094'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$scada = Split-Path $root -Parent
if ((Test-Path (Join-Path $root 'STOP')) -or (Test-Path (Join-Path $scada 'STOP'))) { throw 'STOP active' }
$status = Invoke-RestMethod "$base/api/status" -TimeoutSec 5
if ($status.job.state -ne 'done') { throw 'No completed v04 job' }
$job = [string]$status.job.id
$token = [string]$status.csrf_token
if ($job.Length -ne 32 -or $token.Length -lt 32) { throw 'Invalid status' }
$hist = Invoke-RestMethod "$base/api/visited" -TimeoutSec 5
if ($hist.metadata.not_v08_native_historian -ne $true -or $hist.metadata.derived_quality -ne 'D_DERIVED') { throw 'Historian provenance mismatch' }
$before = @($hist.rows).Count
function Post-Test($body, $extraHeaders) {
  $h = @{'X-Live-Token' = $token}
  if ($extraHeaders) {foreach ($key in $extraHeaders.Keys) {$h[$key] = $extraHeaders[$key]}}
  Invoke-WebRequest -Uri "$base/api/visit" -Method POST -ContentType 'application/json' -Headers $h -Body ($body | ConvertTo-Json -Compress) -SkipHttpErrorCheck -TimeoutSec 5
}
$bad = Post-Test @{id=$job;sample_index=80} @{'X-Live-Token'='incorrect'}
if ($bad.StatusCode -ne 400) {throw "Bad token accepted ($($bad.StatusCode))"}
$bad = Post-Test @{id=('f'*32);sample_index=80} $null
if ($bad.StatusCode -ne 409) {throw "Wrong job accepted ($($bad.StatusCode))"}
$bad = Post-Test @{id=$job;sample_index=672} $null
if ($bad.StatusCode -ne 400) {throw "Invalid sample accepted ($($bad.StatusCode))"}
$bad = Post-Test @{id=$job;sample_index=$true} $null
if ($bad.StatusCode -ne 400) {throw "Boolean sample accepted ($($bad.StatusCode))"}
$bad = Post-Test @{id=$job;sample_index=80} @{'Origin'='http://evil.invalid'}
if ($bad.StatusCode -ne 400) {throw "Cross-origin request accepted ($($bad.StatusCode))"}
$ok = Post-Test @{id=$job;sample_index=80} $null
if ($ok.StatusCode -ne 200) {throw "Valid write HTTP $($ok.StatusCode)"}
$first = $ok.Content | ConvertFrom-Json
$ok2 = Post-Test @{id=$job;sample_index=80} $null
if ($ok2.StatusCode -ne 200) {throw 'Duplicate visit rejected'}
$second = $ok2.Content | ConvertFrom-Json
if ($second.added -ne $false) {throw 'Duplicate write created another row'}
$after = Invoke-RestMethod "$base/api/visited" -TimeoutSec 5
$found = @($after.rows | Where-Object {$_.sample_index -eq 80})
if ($found.Count -ne 1 -or $after.job_id -ne $job -or $after.metadata.hardware_enabled -ne $false) { throw 'Persisted history integrity/provenance error' }
$report = [ordered]@{
  status='VERIFIED'
  timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')
  job_id=$job
  before=$before
  after=@($after.rows).Count
  sample_80_C=$found[0].T_pool_C
  csrf_negative='PASS'
  cross_origin_negative='PASS'
  invalid_id_negative='PASS'
  invalid_index_negative='PASS'
  boolean_index_negative='PASS'
  valid_write='PASS'
  duplicate_dedupe='PASS'
  provenance='D_SYNTHETIC / D_DERIVED, distinct from v08'
  protected_token_not_logged=$true
}
$report | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $root 'runtime\QA_V04_HISTORIAN_HTTP_20261026.json') -Encoding utf8
$report | ConvertTo-Json -Depth 4
