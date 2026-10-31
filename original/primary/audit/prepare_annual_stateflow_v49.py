"""Additive synthetic adapter spec and immutable preservation/source evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[1]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
folder=ROOT/'results'/('annual_stateflow_v49_'+stamp);folder.mkdir()
paths=set()
status=json.loads((ROOT/'STATUS_v48.json').read_text())
prior=ROOT/status['result_directory']/'preservation.json'
paths.update(ROOT/x['path'] for x in json.loads(prior.read_text()))
manifest=sorted((ROOT/'audit').glob('Annual_dispatch_manifest_v48_*.json'))[-1]
paths.update(ROOT/x['path'] for x in json.loads(manifest.read_text())['files'])
for pattern in ['STATUS*.json','MASTER_STAGEBOARD*.md','matlab/**/*.m','matlab/simulink/*.slx']:
    paths.update(ROOT.glob(pattern))
def info(p):return dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(folder/'preservation.json').write_text(json.dumps([info(p) for p in sorted(paths) if p.is_file() and 'v49' not in p.name],indent=2)+'\n')
base=json.loads((ROOT/status['result_directory']/'spec.json').read_text())
period=json.loads((ROOT/'results/period_v46_20261010T180131_369483Z/spec.json').read_text())
import math
spec=dict(version='0.49',model_version='0.42',new_model=False,evidence_class='SYNTHETIC_ENGINEERING_NOT_MEASURED',
    six_mode_cases=base['six_mode_cases'],port_columns=period['port_columns'],
    policy=dict(ambient_C=20.,max_temperature_C=85.,delivery_cutoff_C=80.,restart_energy_MWh=48.,
        min_on_h=.25,min_off_h=.25,continuous_loss_rate_per_h=-math.log1p(-1e-4),
        condenser_policy='fixed',condenser_C=85.,initial_clock=[1.,0.,0.,0.]),
    boundary_note='Fixed 85C condenser is an explicit new synthetic lift boundary. Delivery retains weather-dependent DH supply. Paired v48 holds the same 85C condenser, with loss-first TES and no cutoff/dwell; differences are joint policy effects, not numerical error.')
(folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
files=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*v49*'))+[ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx']
for p in files:
    if p.is_file():
        dest=folder/'source_snapshot'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
print(folder.relative_to(ROOT).as_posix())
