from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('charge_record_v61_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    old=json.loads((ROOT/'results/charge_events_v59_20261011T115206_526064Z/spec.json').read_text())
    base=next(c for c in old['cases'] if c['id']=='simultaneous_branch_hot');cases=[]
    for C in [.2,.3,.125]:
        for loss in [0.,.05]:
            for hot in [.5,.75]:
                c=copy.deepcopy(base);c['id']=f'C{C}_loss{loss}_hot{hot}';c['p']['heat_capacity_MWh_per_K']=C
                c['E']=15*C;c['p']['loss_rate_per_h']=loss;c['s']['hot_capacity_MW_per_K']=hot
                c['age']=[.2,.21];c['expected_ties']=2 if hot==.5 else 1;cases.append(c)
    (folder/'spec.json').write_text(json.dumps(dict(version='0.61',cases=cases),indent=2)+'\n')
    sf=folder/'stateflow';sf.mkdir();shutil.copy2(ROOT/'results/stateflow_finite_v57_20261011T112552_825681Z/spec.json',sf/'spec.json')
    previous=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    preservation=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in previous if 'v61' not in p.name]
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list((ROOT/'audit').glob('*v61.*'))+[ROOT/'audit/verify_stateflow_finite_v57.py']
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    for target in [folder,sf]:
        (target/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n');(target/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copytree(folder/'source_snapshot',sf/'source_snapshot');print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()

