from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=ROOT/'results'/('capacity_chain_v63_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'));folder.mkdir()
    spec=json.loads((ROOT/'results/charge_memory_v62_20261011T163230_944524Z/spec.json').read_text());spec['version']='0.63'
    for c in spec['cases']:
        c['p']['loss_rate_per_h']=0.01 if c['p']['loss_rate_per_h'] else 0.
        c['id']=c['id'].replace('loss0.05','loss0.01')
    for loss in [0.,.01]:
        c=copy.deepcopy(spec['cases'][0]);c['id']=f'unit_eta_zero_aux_loss{loss}'
        c['p']['eta_charge']=1.;c['p']['loss_rate_per_h']=loss;c['s']['aux_per_compressor']=0.;spec['cases'].append(c)
    (folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
    prior=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    (folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in prior if 'v63' not in p.name],indent=2)+'\n')
    manifest=[]
    for p in prior+list((ROOT/'audit').glob('*v63.*')):
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    (folder/'source_hashes.json').write_text(json.dumps(manifest,indent=2)+'\n');print(folder.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
