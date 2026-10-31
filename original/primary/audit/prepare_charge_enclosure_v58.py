from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('charge_enclosure_v58_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir();old=json.loads((ROOT/'results/charge_regimes_v56_20261011T111230_427402Z/spec.json').read_text())
    cases=[v for v in old['cases'] if v['expected']=='ACCEPT']
    # All 10 regimes, all three loss rates; deterministic broader cases.
    chosen=cases[:37]+cases[37:57]
    (folder/'spec.json').write_text(json.dumps(dict(version='0.58',cases=chosen),indent=2)+'\n')
    sf=folder/'stateflow';sf.mkdir()
    shutil.copy2(ROOT/'results/stateflow_finite_v57_20261011T112552_825681Z/spec.json',sf/'spec.json')
    previous=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    previous=[p for p in previous if 'v58' not in p.name]
    preservation=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in previous]
    for target in [folder,sf]: (target/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list((ROOT/'audit').glob('*v58.*'))+[ROOT/'audit/verify_stateflow_finite_v57.py']
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Existing v57 reviewer expects a complete nested snapshot.
    shutil.copytree(folder/'source_snapshot',sf/'source_snapshot')
    (sf/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
