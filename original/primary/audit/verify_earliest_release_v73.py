"""Read-only final evidence/checkpoint verification; additive QA logs only."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    closure=json.loads((folder/'closure.json').read_text())
    for r in closure['evidence_hashes']:check('evidence_'+r['path'],sha(folder/r['path'])==r['sha256'])
    for r in closure['checkpoint_hashes']:check('checkpoint_'+r['path'],sha(ROOT/r['path'])==r['sha256'])
    for manifest in ['source_hashes.json','preservation.json','reviewer_sources.json','closure_source_hashes.json']:
        for r in json.loads((folder/manifest).read_text()):check(manifest+'_'+r['path'],sha(ROOT/r['path'])==r['sha256'])
    status=json.loads((ROOT/'STATUS_v73.json').read_text())
    check('status_twins',status==json.loads((ROOT/'STATUS_stateflow_v73.json').read_text()))
    check('accepted_scope',status['new_model'] and status['corrected_model_accepted'] and status['model_executed_this_run'] and status['matlab_failed']==status['independent_failed']==0 and not status['primary_article_replication'] and status['independent_physical_validation']=='NOT_TESTED')
    for name in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
        data=(ROOT/name).read_bytes();check('ledger_'+name,status['timestamp_utc'].encode() in data and b'v73r2' in data)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');failed=[v for v in checks if not v['passed']]
    result=dict(version='0.73',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,summary=dict(passed=len(checks)-len(failed),failed=len(failed)))
    (folder/f'release_verification_v73_{stamp}.json').write_text(json.dumps(result,indent=2)+'\n')
    (folder/f'release_verification_v73_{stamp}.log').write_text(json.dumps(dict(summary=result['summary'],failed=failed),indent=2)+'\n')
    print(json.dumps(dict(summary=result['summary'],failed=failed)));return int(bool(failed))

if __name__=='__main__':sys.exit(main())
