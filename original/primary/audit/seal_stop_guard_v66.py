"""Seal the actual saved-model and QA sources before independent review."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
assert not (folder/'source_hashes.json').exists()
paths=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
paths+=list((ROOT/'audit').glob('*v66.*'))+[ROOT/'audit'/name for name in ['verify_interval_dispatch_v65.py','verify_restart_chain_v64.py','verify_capacity_chain_v63.py']]
manifest=[]
for p in sorted(set(paths)):
    dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('SEALED',len(manifest),'files')
