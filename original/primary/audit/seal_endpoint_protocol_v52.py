"""Seal the accepted local evidence and verify it without rerunning physics."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def info(p):return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
    status=json.loads((ROOT/'STATUS_stateflow_v52.json').read_text());folder=ROOT/status['result_directory']
    qa=json.loads((ROOT/status['independent_qa']).read_text());assert qa['actual_failed']==qa['reviewer_selfchecks_failed']==0
    with zipfile.ZipFile(ROOT/status['saved_model']) as z:assert z.testzip() is None
    paths={p for p in folder.rglob('*') if p.is_file() and not ({'local_build','diagnostic_build','__pycache__'} & set(p.parts))}
    for pattern in ('matlab/**/*v52*','audit/*v52*','STATUS*v52.json','MASTER_STAGEBOARD*v52.md','STATUS_v51.json','MASTER_STAGEBOARD_v51.md'):
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    paths.update([ROOT/'automation/engineering_progress.md',ROOT/'automation/STATEFLOW_ACCEPTANCE.md'])
    entries=[info(p) for p in sorted(paths)]
    prior=json.loads((folder/'preservation.json').read_text());prior_bad=[e['path'] for e in prior if info(ROOT/e['path'])!=e]
    assert not prior_bad,prior_bad[:10]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');manifest=ROOT/'audit'/('Endpoint_protocol_manifest_v52_'+stamp+'.json')
    manifest.write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),status='ACCEPTED_SCOPED_IMPLEMENTATION',files=entries),indent=2)+'\n')
    bad=[e['path'] for e in entries if info(ROOT/e['path'])!=e];assert not bad,bad
    receipt=ROOT/'audit'/('Endpoint_protocol_postclose_v52_'+stamp+'.json')
    receipt.write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),manifest=manifest.relative_to(ROOT).as_posix(),release_files=len(entries),preserved_artifacts=len(prior),passed=len(entries)+len(prior)+3,failed=0,model_sha256=info(ROOT/status['saved_model'])['sha256']),indent=2)+'\n')
    print(receipt.relative_to(ROOT).as_posix());print('POSTCLOSE_V52 PASS',len(entries)+len(prior)+3,'FAIL 0')
if __name__=='__main__':main()
