"""Seal completed packaging artifacts after console logs have closed."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'audit/Stateflow_clock_manifest_v42_20261010T131054_029975Z.json'
post=ROOT/'audit/Stateflow_clock_postclose_v42_20261010T131100_414465Z.json'
report=json.loads(post.read_text());assert report['failed']==0
for f in json.loads(manifest.read_text())['files']:
    p=ROOT/f['path'];assert p.stat().st_size==f['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256']
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
    f.write('\nFinal v42 packaging: 183 PASS / 0 FAIL; 168 release artifacts retain hashes/sizes. '
            'Evidence: audit/Stateflow_clock_postclose_v42_20261010T131100_414465Z.json. '
            'Completed finalizer/post-close logs and reports sealed separately. No numerical/model '
            'artifacts changed after executed QA. Run complete; next task is primary equipment traceability.\n')
paths=[manifest,post,Path(__file__).resolve()]
paths.extend((ROOT/'automation/logs').glob('stateflow_repair_finalize_*.log'))
paths.extend((ROOT/'automation/logs').glob('stateflow_repair_postclose_*.log'))
stamp=datetime.now(timezone.utc);p=ROOT/'audit'/('Stateflow_clock_postclose_manifest_v42_'+stamp.strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
entries=[dict(path=x.relative_to(ROOT).as_posix(),bytes=x.stat().st_size,sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in sorted(set(paths))]
p.write_text(json.dumps(dict(version='0.42',timestamp_utc=stamp.isoformat(),files=entries),indent=2)+'\n')
print('POSTCLOSE_MANIFEST='+p.relative_to(ROOT).as_posix());print('PACKAGING_ARTIFACTS='+str(len(entries)))
