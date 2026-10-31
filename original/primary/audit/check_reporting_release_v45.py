"""Read-only final package checks; no numeric rerun or artifact mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
manifest_path=sorted((ROOT/'audit').glob('Reporting_manifest_v45_*.json'))[-1]
manifest=json.loads(manifest_path.read_text());checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for x in manifest['files']:
    p=ROOT/x['path'];check(x['path'],p.is_file() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256'])
s=json.loads((ROOT/'STATUS_v45.json').read_text())
check('saved_model_hash',sha(ROOT/s['saved_model'])==s['model_sha256'])
check('scoped_success',s['harness_failed']==s['independent_actual_failed']==s['reviewer_selfchecks_failed']==0)
check('new_model_not_claimed',not s['new_model'] and s['model_executed_this_run'])
check('legacy_migration_still_open',s['new_api_defect_repaired'] and not s['legacy_consumers_repaired'])
check('physical_validation_not_claimed',s['independent_physical_validation']=='NOT_TESTED' and not s['primary_article_replication'])
check('QA_link', (ROOT/s['independent_qa']).is_file())
check('progress_handoff','v45 finite-backup delivery and heating-COP report repair' in (ROOT/'automation/engineering_progress.md').read_text(encoding='utf-8'))
check('acceptance_checkpoint','Energy-reporting checkpoint' in (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').read_text(encoding='utf-8'))
summary=dict(version='0.45',timestamp_utc=datetime.now(timezone.utc).isoformat(),
             passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),
             manifest=str(manifest_path.relative_to(ROOT)),manifest_sha256=sha(manifest_path),
             checker_sha256=sha(Path(__file__)),checks=checks)
path=ROOT/'audit'/('Reporting_postclose_v45_'+stamp+'.json');assert not path.exists()
path.write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='checks'},indent=2));print('PACKAGE_REPORT='+str(path.relative_to(ROOT)))
assert summary['failed']==0
