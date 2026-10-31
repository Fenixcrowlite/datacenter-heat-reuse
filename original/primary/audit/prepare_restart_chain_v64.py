from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('restart_chain_v64_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    spec=json.loads((ROOT/'results/capacity_chain_v63_20261011T164447_035544Z/spec.json').read_text())
    spec['cases']=[c for c in spec['cases'] if c['p']['loss_rate_per_h']>0];spec['version']='0.64'
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    files=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in files if 'v64' not in p.name],indent=2)+'\n')
    sources=files+list((ROOT/'audit').glob('*v64.*'))+list((ROOT/'audit').glob('verify_capacity_chain_v63.py'))
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n');print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
