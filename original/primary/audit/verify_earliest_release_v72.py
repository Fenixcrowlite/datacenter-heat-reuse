"""Final immutable evidence/checkpoint/ledger verification, no simulation rerun."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for r in json.loads((folder/'evidence_manifest.json').read_text()):check('evidence_'+r['path'],sha(folder/r['path'])==r['sha256'])
    for manifest in ['source_hashes.json','preservation.json','reviewer_sources.json','closure_source_hashes.json']:
        for r in json.loads((folder/manifest).read_text()):check(manifest+'_'+r['path'],sha(ROOT/r['path'])==r['sha256'])
    for r in json.loads((folder/'closure.json').read_text())['checkpoint_hashes']:check('checkpoint_'+r['path'],sha(ROOT/r['path'])==r['sha256'])
    status=json.loads((ROOT/'STATUS_v72.json').read_text());check('status_twins',status==json.loads((ROOT/'STATUS_stateflow_v72.json').read_text()))
    check('four_OPEN',len(status['open_defect_classes'])==4 and not status['new_model'] and not status['corrected_model_accepted'])
    for name in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
        check('ledger_'+name,b'v72' in (ROOT/name).read_bytes() and status['next_actionable_task'].encode() in (ROOT/name).read_bytes() if 'STATEFLOW' not in name else b'checkpoint v72' in (ROOT/name).read_bytes())
    failed=[c for c in checks if not c['passed']];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    result=dict(version='0.72',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,summary=dict(passed=len(checks)-len(failed),failed=len(failed)),verification_source_sha256=sha(Path(__file__)))
    (folder/f'release_verification_v72_{stamp}.json').write_text(json.dumps(result,indent=2)+'\n')
    (folder/f'release_verification_v72_{stamp}.log').write_text(json.dumps(dict(summary=result['summary'],failed=failed),indent=2)+'\n')
    print(json.dumps(dict(summary=result['summary'],failed=failed)));return int(bool(failed))
if __name__=='__main__':sys.exit(main())
