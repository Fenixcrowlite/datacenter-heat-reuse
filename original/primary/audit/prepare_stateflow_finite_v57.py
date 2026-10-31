from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil

ROOT = Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder = ROOT/'results'/('stateflow_finite_v57_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    previous = list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    previous = [p for p in previous if 'v57' not in p.name]
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in previous],indent=2)+'\n')
    spec = json.loads((ROOT/'results/finite_interface_v53_20261011T062818_250661Z/spec.json').read_text())
    spec.update(version='0.57', model_version='0.57', new_model=True,
                scope='COMPILED_FINITE_WATER_BOUNDARY_HELD_PER_MACRO_NOT_CONTINUOUS_TANK_COUPLING')
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    sources = list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list((ROOT/'audit').glob('*v57.*'))
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
