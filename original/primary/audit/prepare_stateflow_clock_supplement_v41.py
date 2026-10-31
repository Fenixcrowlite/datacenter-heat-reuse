"""One missing BACKUP simulation; reuse completed audit, no broad rerun."""
from pathlib import Path
from datetime import datetime,timezone
import copy,json
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'audit/stateflow_clock_spec_v41_20261010T125621_525409Z'
spec=json.loads((source/'cases.json').read_text());case=copy.deepcopy(spec['cases'][1])
case.update(id='dedicated_backup',inputs=[[0.,35.,75.,1.,45.]])
case['p'][10]=2.
spec['cases']=[case];spec['supplement_for']='results/stateflow_clock_v41_20261010T125630995Z'
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
folder=ROOT/'audit'/('stateflow_clock_spec_v41_'+stamp);folder.mkdir()
(folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n')
(folder/'preservation.json').write_bytes((source/'preservation.json').read_bytes())
print('SPEC='+folder.relative_to(ROOT).as_posix())
