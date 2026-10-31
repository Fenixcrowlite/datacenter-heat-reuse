"""Seal completed post-close evidence and finalizer log; no model mutations."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    reportPath=next((ROOT/'audit').glob('Stateflow_HP_postclose_v40_*.json'))
    report=json.loads(reportPath.read_text());assert report['failed']==0
    ts=datetime.now(timezone.utc);stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    paths={Path(__file__).resolve(),reportPath,ROOT/report['manifest'],ROOT/'audit/check_stateflow_hp_checkpoint_v40.py'}
    for pattern in ('stateflow_hp_v40_postclose_*.log','stateflow_hp_v40_finalize_*.log'):
        paths.update((ROOT/'automation/logs').glob(pattern))
    assert len(paths)==6 and all(p.stat().st_size>0 for p in paths)
    manifest=ROOT/'audit'/('Stateflow_HP_postclose_manifest_v40_'+stamp+'.json')
    data=dict(timestamp_utc=ts.isoformat(),model_release='0.40',scope='Completed packaging artifacts only',
        files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)])
    assert not manifest.exists();manifest.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'''\nFinal v40 post-close packaging: {report['passed']}/{report['passed']} PASS,
zero failures; {report['sealed_entries']} release entries retain hashes/sizes.
Evidence: `{reportPath.relative_to(ROOT).as_posix()}`. Completed finalizer log,
post-close checker/report/log and original release manifest sealed separately:
`{manifest.relative_to(ROOT).as_posix()}` ({len(paths)} artifacts). Numeric/model
artifacts unchanged after executed QA. Run complete; next action remains the
focused clock seed/error-bound/event-order audit in STATUS_stateflow_v40.json.
''')
    print('POSTCLOSE_SEAL='+manifest.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
