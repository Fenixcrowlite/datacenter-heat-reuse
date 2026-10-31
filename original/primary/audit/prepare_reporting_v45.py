"""New workspace-only reporting fixtures and immutable baseline inventory."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
out=ROOT/'results'/('reporting_v45_'+stamp);out.mkdir()
paths=set()
for pat in ['STATUS*.json','MASTER_STAGEBOARD*.md','matlab/simulink/*v42.m','matlab/simulink/*.slx',
            'matlab/+dchr/compute_metrics*.m','matlab/+dchr/+components/heat_pump_step_v40.m']:
    paths.update(ROOT.glob(pat))
prior=json.loads((ROOT/'audit/HP_upstream_postclose_manifest_v44_20261010T174231_507192Z.json').read_text())
# Keep v44 sealed release plus all saved model versions and accepted v42 source.
for x in prior['files']:paths.add(ROOT/x['path'])
for folder in (ROOT/'results').glob('reporting_v45_*'):
    if folder==out:continue
    paths.update(p for p in folder.glob('*') if p.is_file())
    paths.update(p for p in (folder/'source_snapshot').glob('*') if p.is_file())
paths.discard(ROOT/'matlab/+dchr/compute_energy_metrics_v45.m')
(out/'preservation.json').write_text(json.dumps([dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)],indent=2)+'\n')
p=[1,10,0,4,1,1,0,5,.2,20,3]
h=[8,.45,1.2,8,0,1,4,0,0]
cases=[]
for name,source,demand,initial,charge,boiler,mode in [
 ('zero_demand',0,0,5,0,3,0),('hp_only',6,4,5,0,3,1),
 ('tes_charge',6,1,5,3,3,2),('tes_discharge',0,2,9,0,3,3),
 ('boiler_limit',0,3,5,0,3,4),('insufficient_heat',0,5,5,0,2,5)]:
    pp=p.copy();pp[2]=charge;pp[10]=boiler
    cases.append(dict(id=name,p=pp,h=h,initial_energy_MWh=initial,inputs=[[source,35,75,demand,45]],expected_mode=mode))
# Independent synthetic reporting ports; two intervals expose ratio vs diagnostic.
cols=['Heat_Demand_MW','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW']
vectors=[dict(id='two_cops_equal_duration',dt=[1,1],ports=[[4,4,0,0,0,0,4,1],[8,8,0,0,0,0,8,4]]),
         dict(id='two_cops_unequal_duration',dt=[.25,2],ports=[[4,4,0,0,0,0,4,1],[8,8,0,0,0,0,8,4]]),
         dict(id='initial_inventory_only',dt=[1,1],ports=[[2,0,0,2,0,0,0,0],[1,0,0,1,0,0,0,0]]),
         dict(id='idle_period',dt=[1,1],ports=[[0]*8,[0]*8])]
spec=dict(version='0.45',model_version='0.42',new_model=False,fixture_class='SYNTHETIC_ENGINEERING_NOT_MEASURED',
          port_columns=cols,cases=cases,reporting_vectors=vectors)
(out/'spec.json').write_text(json.dumps(spec,indent=2)+'\n')
(ROOT/'audit/reporting_current_v45.txt').write_text(str(out.relative_to(ROOT))+'\n')
print('PREPARED='+str(out.relative_to(ROOT)))
