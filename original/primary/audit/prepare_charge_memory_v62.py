from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('charge_memory_v62_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    prior=ROOT/'results/charge_record_v61_20261011T162123_136887Z/spec.json'
    spec=json.loads(prior.read_text());spec['version']='0.62'
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    previous=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    sources=previous+list((ROOT/'audit').glob('*v62.*'))
    preservation=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in previous if 'v62' not in p.name]
    (folder/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    manifest=[]
    for p in sources:
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n');print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
