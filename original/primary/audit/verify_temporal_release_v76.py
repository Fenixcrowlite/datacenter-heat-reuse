"""Final seal verification: no simulation rerun, no changes to sealed evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');checks=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for manifest,base in [('evidence_seal.json',folder),('checkpoint_hashes.json',ROOT),('preservation.json',ROOT),('source_hashes.json',ROOT),('closure_source_hashes.json',ROOT)]:
        for e in json.loads((folder/manifest).read_text()):check(manifest+':'+e['path'],sha(base/e['path'])==e['sha256'])
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledger_prefix:'+e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    check('STATUS_twins',(ROOT/'STATUS_v76.json').read_bytes()==(ROOT/'STATUS_stateflow_v76.json').read_bytes())
    status=json.loads((ROOT/'STATUS_v76.json').read_text());check('saved_model',sha(ROOT/status['saved_model'])==status['model_sha256'])
    qa=json.loads((ROOT/status['independent_qa']).read_text());check('QA_success',qa['summary']['failed']==0 and all(c['passed'] for c in qa['reviewer_selfchecks']))
    ts=datetime.now(timezone.utc);out=dict(timestamp_utc=ts.isoformat(),checks=checks,summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    for suffix in ['json','log']:
        with (folder/('release_verification_v76_'+ts.strftime('%Y%m%dT%H%M%S_%fZ')+'.'+suffix)).open('x',encoding='utf-8') as f:json.dump(out if suffix=='json' else dict(summary=out['summary'],failed=[c for c in checks if not c['passed']]),f,indent=2)
    print(json.dumps(out['summary']));return int(out['summary']['failed']>0)
if __name__=='__main__':sys.exit(main())
