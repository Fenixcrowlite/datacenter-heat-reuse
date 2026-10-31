"""Verify packaged evidence remains sealed after documentation handoff."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/Path(sys.argv[1]);manifest=json.loads(path.read_text());checks=[]
for a in manifest['files']:
    p=ROOT/a['path'];ok=p.is_file() and p.stat().st_size==a['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
    checks.append(dict(path=a['path'],passed=ok))
status=json.loads((ROOT/'STATUS_v47.json').read_text())
checks.append(dict(path='authoritative_scope',passed=status['harness_failed']==status['independent_actual_failed']==0 and not status['new_model'] and status['defect_status']=='OPEN_ANNUAL_V13_NONMAXIMAL_HP_DISPATCH'))
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
report=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),manifest=path.relative_to(ROOT).as_posix(),passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),checks=checks)
out=ROOT/'audit'/('HP_annual_postclose_v47_'+stamp+'.json');assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n')
print(f'POSTCLOSE passed={report["passed"]} failed={report["failed"]} evidence={out.relative_to(ROOT).as_posix()}')
if report['failed']:raise SystemExit(1)
