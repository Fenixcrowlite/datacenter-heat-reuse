"""Original v72 witnesses plus saved-v71 regressions, additive seals."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=json.loads((ROOT/'results/earliest_admissibility_v72_20261012T030907_237961Z/spec.json').read_text())
    b=json.loads((ROOT/'results/earliest_dispatch_v71_20261012T030016_337397Z/spec.json').read_text())
    cases=copy.deepcopy(a['cases']);ids={c['id'] for c in cases}
    for c in b['cases']:
        if c['id'] not in ids:c=copy.deepcopy(c);c['family']='prior_v71';cases.append(c)
    for c in cases:
        c['expected_accept']=c['id'] not in ['disable_before_dwell','segment_budget_exhaustion']
        c['expected_guard']='v73 ON dwell not certified' if c['id']=='disable_before_dwell' else 'v73 event segment budget' if c['id']=='segment_budget_exhaustion' else ''
    for c in b['faults']:
        c=copy.deepcopy(c);c.update(family='runtime_control',expected_accept=False)
        c['expected_guard']=c['expected_guard'].replace('v71','v73');cases.append(c)
    cases=[{k:c[k] for k in ['id','p','input','family','expected_accept','expected_guard']} for c in cases]
    folder=ROOT/'results'/('earliest_repair_v73_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    (folder/'spec.json').write_text(json.dumps(dict(version='0.73',saved_model_version='0.73',cases=cases),indent=2)+'\n')
    paths=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in paths if 'v73' not in p.name],indent=2)+'\n')
    paths=[p for p in (ROOT/'audit').glob('*v73*') if p.is_file()]+[p for p in (ROOT/'matlab').rglob('*v73*') if p.is_file()]
    manifest=[]
    for src in paths:
        rel=src.relative_to(ROOT).as_posix();dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest.append(dict(path=rel,sha256=sha(src)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
