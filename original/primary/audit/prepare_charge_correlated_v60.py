from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('charge_correlated_v60_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    old=json.loads((ROOT/'results/charge_events_v59_20261011T115206_526064Z/spec.json').read_text())
    base=next(x for x in old['cases'] if x['id']=='simultaneous_branch_hot');cases=[]
    for j in range(9):
        c=copy.deepcopy(base);c['id']=['persistent_tie','lossy_tie','triple_nameplate','triple_TES','unique_request','near_event','low_inventory','interval_clock','different_capacity'][j]
        c['post_h']=.4;c['clock0']=[.125,.125]
        if j==1:c['p']['loss_rate_per_h']=.05
        if j==2:c['s']['hp_capacity_MW']=1.
        if j==3:c['p']['charge_limit_MW']=1.
        if j==4:c['s']['hot_capacity_MW_per_K']=20.
        if j==5:c['E']=4.9
        if j==6:c['E']=.1
        if j==7:c['clock0']=[.125,.126]
        if j==8:c['p']['heat_capacity_MWh_per_K']=.3
        # Incoming strict unique-limiter API deliberately rejects nameplate/TES ties.
        # Exercise those through a separate exact post-event coefficient test later.
        if j in (2,3):continue
        cases.append(c)
    (folder/'spec.json').write_text(json.dumps(dict(version='0.60',cases=cases),indent=2)+'\n')
    sf=folder/'stateflow';sf.mkdir();shutil.copy2(ROOT/'results/stateflow_finite_v57_20261011T112552_825681Z/spec.json',sf/'spec.json')
    previous=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    previous=[p for p in previous if 'v60' not in p.name]
    preservation=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in previous]
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list((ROOT/'audit').glob('*v60.*'))+[ROOT/'audit/verify_stateflow_finite_v57.py']
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    for target in [folder,sf]:
        (target/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n');(target/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    shutil.copytree(folder/'source_snapshot',sf/'source_snapshot')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
