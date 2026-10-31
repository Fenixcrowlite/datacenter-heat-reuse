from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('charge_events_v59_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir();old=json.loads((ROOT/'results/charge_enclosure_v58_20261011T113732_506828Z/spec.json').read_text())
    cases=old['cases'];base=copy.deepcopy(cases[0]);base['id']='simultaneous_branch_hot';base['s']['hot_capacity_MW_per_K']=.5;cases.append(base)
    base=copy.deepcopy(cases[0]);base['id']='stationary_exact';base['E']=4.;base['p']['eta_charge']=1.;base['p']['loss_rate_per_h']=.25;cases.append(base)
    (folder/'spec.json').write_text(json.dumps(dict(version='0.59',cases=cases),indent=2)+'\n')
    sf=folder/'stateflow';sf.mkdir();shutil.copy2(ROOT/'results/stateflow_finite_v57_20261011T112552_825681Z/spec.json',sf/'spec.json')
    previous=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    previous=[p for p in previous if 'v59' not in p.name]
    preservation=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in previous]
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list((ROOT/'audit').glob('*v59.*'))+[ROOT/'audit/verify_charge_enclosure_v58.py',ROOT/'audit/verify_stateflow_finite_v57.py']
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    for target in [folder,sf]:
        (target/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
        (target/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copytree(folder/'source_snapshot',sf/'source_snapshot')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
