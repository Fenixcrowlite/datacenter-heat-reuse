"""Preserve baselines and prepare versioned synthetic v48 local evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil
ROOT=Path(__file__).resolve().parents[1]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
folder=ROOT/'results'/('annual_dispatch_v48_'+stamp);folder.mkdir()
paths=set()
prior=ROOT/'results/hp_annual_v47_20261010T181354_797146Z/preservation.json'
paths.update(ROOT/x['path'] for x in json.loads(prior.read_text()))
paths.update(ROOT/x['path'] for x in json.loads((ROOT/'audit/HP_annual_manifest_v47_20261010T181651_034709Z.json').read_text())['files'])
for pattern in ['STATUS*.json','MASTER_STAGEBOARD*.md','matlab/**/*.m','matlab/simulink/*.slx']:
    paths.update(ROOT.glob(pattern))
(folder/'preservation.json').write_text(json.dumps([dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,
    sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths) if p.is_file() and 'v48' not in p.name],indent=2)+'\n')
base=json.loads((ROOT/'results/period_v46_20261010T180131_369483Z/spec.json').read_text())
spec=dict(version='0.48',model_version='0.42',new_model=False,evidence_class='SYNTHETIC_ENGINEERING_NOT_MEASURED',
    six_mode_cases=base['six_mode_cases'],period=base['period'],boiler_caps_MW=[0,2,20],
    fixtures=[dict(id='matched_source_limited',source_MW=1,demand_MW=20,penalty=.08,cop_min=2.2),
        dict(id='matched_zero_penalty',source_MW=6,demand_MW=20,penalty=0,cop_min=2.2),
        dict(id='matched_cutoff',source_MW=1,demand_MW=.1,penalty=.08,cop_min=4.1)])
(folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
for p in list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*v48*'))+[ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx']:
    if p.is_file():
        target=folder/'source_snapshot'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
print(folder.relative_to(ROOT).as_posix())
