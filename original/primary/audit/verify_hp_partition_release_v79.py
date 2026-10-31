"""Release hashes and append-only preservation; distinct from numeric QA."""
from datetime import datetime,timezone
import hashlib,json,sys
from hp_partition_v79 import ROOT,sha,dump,stamp
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for e in json.loads((folder/'evidence_seal.json').read_text()):check('sealed_'+e['path'],sha(folder/e['path'])==e['sha256'])
for e in json.loads((folder/'checkpoint_hashes.json').read_text()):check('checkpoint_'+e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'closure_snapshot'/e['path'])==e['sha256'])
for e in json.loads((folder/'preservation.json').read_text()):check('preserved_'+e['path'],sha(ROOT/e['path'])==e['sha256'])
for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledger_'+e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
check('status_twins',(ROOT/'STATUS_v79.json').read_bytes()==(ROOT/'STATUS_stateflow_v79.json').read_bytes())
check('stageboard_twins',(ROOT/'MASTER_STAGEBOARD_v79.md').read_bytes()==(ROOT/'MASTER_STAGEBOARD_stateflow_v79.md').read_bytes())
r=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
name='release_QA_v79_'+stamp();dump(folder/(name+'.json'),r);dump(folder/(name+'.log'),dict(summary=r['summary'],failed=[c for c in checks if not c['passed']]))
print(json.dumps(r['summary']));sys.exit(int(r['summary']['failed']>0))
