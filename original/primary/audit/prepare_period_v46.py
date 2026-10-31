"""Workspace-only immutable evidence preparation; no scheduler changes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
folder=ROOT/'results'/('period_v46_'+stamp);folder.mkdir()
paths=set()
for pattern in ['STATUS*.json','MASTER_STAGEBOARD*.md','matlab/**/*.m','matlab/simulink/*.slx','results/*.csv']:
    paths.update(ROOT.glob(pattern))
prior=json.loads((ROOT/'audit/Reporting_manifest_v45_20261010T175357_019581Z.json').read_text())
for x in prior['files']:paths.add(ROOT/x['path'])
for previous in (ROOT/'results').glob('period_v46_*'):
    if previous==folder:continue
    paths.update(p for p in previous.glob('*') if p.is_file())
    paths.update(p for p in (previous/'source_snapshot').rglob('*') if p.is_file())
paths={p for p in paths if p.is_file() and ('v46' not in p.name or p.is_relative_to(ROOT/'results'))}
preservation=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,
                   sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(paths)]
(folder/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
base=json.loads((ROOT/'results/reporting_v45_20261010T175127_627392Z/spec.json').read_text())
cycle=[[0,35,75,0,45],[3,35,75,4,45],[6,35,75,1,45],
       [0,35,75,2,45],[0,35,75,2,45],[0,35,75,5,45]]
spec=dict(version='0.46',model_version='0.42',new_model=False,
          fixture_class='SYNTHETIC_ENGINEERING_NOT_MEASURED',
          six_mode_cases=base['cases'],port_columns=base['port_columns'],
          period=dict(id='saved_v42_48h',p=[1,10,3,4,.95,.9,.01,5,.2,20,2],
                      h=[8,.45,1.2,8,0,1,4,0,0],c=[8,.25,.25,64],
                      initial_energy_MWh=5,initial_clock=[1,0,0,0],inputs=cycle*8),
          annual_boiler_caps_MW=[0,2,20],annual_hours=8760,
          reporting_fixture=dict(dt_h=[.25,2],
                legacy_rows=[[4,4,0,0,0,0,40,1],[8,8,0,0,0,0,80,4]]))
(folder/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
(ROOT/'audit/period_current_v46.txt').write_text(folder.relative_to(ROOT).as_posix()+'\n')
print('PREPARED='+folder.relative_to(ROOT).as_posix())
