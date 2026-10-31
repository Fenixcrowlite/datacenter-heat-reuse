"""Final packaging gate: checks hashes and handoff, no repeated simulation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
manifest_path=sorted((ROOT/'audit').glob('Period_manifest_v46_*.json'))[-1]
manifest=json.loads(manifest_path.read_text());checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for x in manifest['files']:
    p=ROOT/x['path'];check(x['path'],p.is_file() and p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'])
status=json.loads((ROOT/'STATUS_v46.json').read_text());qa=json.loads((ROOT/status['independent_qa']).read_text())
check('status_QA_consistent',status['independent_actual_passed']==qa['actual_passed'] and status['independent_actual_failed']==qa['actual_failed']==0)
check('scope',not status['new_model'] and status['model_version']=='0.42' and status['independent_physical_validation']=='NOT_TESTED')
check('handoff',status['next'] in (ROOT/'MASTER_STAGEBOARD_v46.md').read_text() and status['next'] in (ROOT/'automation/engineering_progress.md').read_text())
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
result=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),version='0.46',manifest=manifest_path.relative_to(ROOT).as_posix(),
    passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks)
path=ROOT/'audit'/('Period_postclose_v46_'+stamp+'.json');path.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=result['passed'],failed=result['failed'],report=path.relative_to(ROOT).as_posix()),indent=2))
assert result['failed']==0
