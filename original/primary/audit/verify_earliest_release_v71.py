"""Final read-only release verification, saving only additive QA evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    closure=json.loads((folder/'closure.json').read_text());checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for item in closure['evidence_hashes']:check('evidence_'+item['path'],sha(folder/item['path'])==item['sha256'])
    for item in closure['checkpoint_hashes']:check('checkpoint_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
    for name in ['preservation.json','source_hashes.json','closure_source_hashes.json']:
        for item in json.loads((folder/name).read_text()):
            check(name+'_'+item['path'],sha(ROOT/item['path'])==item['sha256'])
            if 'source_hashes' in name:
                directory='closure_source_snapshot' if name.startswith('closure') else 'source_snapshot'
                check('snapshot_'+item['path'],sha(folder/directory/item['path'])==item['sha256'])
    status=json.loads((ROOT/'STATUS_v71.json').read_text());check('status_twins',(ROOT/'STATUS_v71.json').read_bytes()==(ROOT/'STATUS_stateflow_v71.json').read_bytes())
    for name in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
        data=(ROOT/name).read_bytes();check('ledger_'+name,status['timestamp_utc'].encode() in data and b'v71' in data)
    check('implementation_scope',status['model_executed_this_run'] and status['matlab_failed']==status['independent_failed']==status['handoff_failed']==0 and not status['primary_article_replication'] and status['independent_physical_validation']=='NOT_TESTED')
    result=dict(version='0.71',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,summary=dict(passed=sum(v['passed'] for v in checks),failed=sum(not v['passed'] for v in checks)))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');out=folder/f'release_verification_v71_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(verification=out.relative_to(ROOT).as_posix(),summary=result['summary'],failed=[v for v in checks if not v['passed']])))
    return int(result['summary']['failed']>0)
if __name__=='__main__':sys.exit(main())
