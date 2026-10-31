"""Varied TES domain and invalid input checks; algebraic tests only."""
import json, random, math
from pathlib import Path
from dispatch_reference_v16 import StorageParameters, DispatchParameters, dispatch_step, storage_step
rng=random.Random(18009)
errors=[]; worst=0.; cases=0
for i in range(1500):
    dt=rng.choice([0.05,0.25,1.,4.,8.,rng.uniform(.01,8)])
    cap=rng.choice([0.,rng.uniform(.01,120)])
    s=StorageParameters(capacity_MWh=cap,charge_limit_MW=rng.uniform(0,25),
        discharge_limit_MW=rng.uniform(0,25),eta_charge=rng.uniform(.25,1),
        eta_discharge=rng.uniform(.25,1),loss_fraction_per_h=rng.uniform(0,.11))
    p=DispatchParameters(storage=s,boiler_capacity_MW=rng.uniform(0,30),dt_h=dt)
    e=rng.choice([0.,cap,rng.uniform(0,cap)])
    source=rng.uniform(0,30); demand=rng.uniform(0,45)
    tc=rng.uniform(-5,45)
    try:
        x=dispatch_step(source,tc,tc+rng.uniform(8,70),demand,e,p)
        residual=((x.HP_Source_Used_MW+x.HP_Electric_MW+x.Gas_Heat_MW-
          x.Supplied_Heat_MW)*dt+e-x.Storage_E_Next_MWh-
          x.Storage_Standing_Loss_MWh-x.Storage_Charge_Loss_MWh-
          x.Storage_Discharge_Loss_MWh)
        worst=max(worst,abs(residual)); cases+=1
        assert abs(residual)<2e-10*max(1,cap,(source+demand)*dt)
        assert abs(demand-x.Supplied_Heat_MW-x.Unmet_Heat_MW)<1e-8
        assert 0<=x.Storage_E_Next_MWh<=cap
        assert not(x.Storage_Charge_MW>0 and x.Storage_Discharge_MW>0)
        assert 0<=x.Gas_Heat_MW<=p.boiler_capacity_MW+1e-10
    except Exception as ex: errors.append([i,str(ex)])
invalid=[
 lambda: StorageParameters(eta_charge=0),
 lambda: StorageParameters(eta_discharge=1.1),
 lambda: StorageParameters(capacity_MWh=-1),
 lambda: StorageParameters(charge_limit_MW=-1),
 lambda: StorageParameters(loss_fraction_per_h=-1),
 lambda: DispatchParameters(dt_h=0),
 lambda: DispatchParameters(storage=StorageParameters(loss_fraction_per_h=.6),dt_h=2),
 lambda: storage_step(51,0,0,StorageParameters(),1),
 lambda: storage_step(10,1,1,StorageParameters(),1),
 lambda: dispatch_step(-1,10,40,5,0),
 lambda: dispatch_step(1,10,40,-1,0),
 lambda: dispatch_step(1,20,20,5,0),
 lambda: dispatch_step(float('nan'),10,40,5,0)]
rejected=0
for j,f in enumerate(invalid):
    try: f(); errors.append(['invalid-'+str(j),'not rejected'])
    except ValueError: rejected+=1
    except Exception as ex: errors.append(['invalid-'+str(j),repr(ex)])
report={'scope':'Python algebraic/constraints only, not primary-paper or physical validation',
'seed':18009,'cases':cases,'invalid_rejected':rejected,'invalid_total':len(invalid),
'max_abs_energy_residual_MWh':worst,'errors':errors}
out=Path(__file__).with_name('dispatch_properties_v18.json')
if out.exists():
    assert json.loads(out.read_text(encoding='utf8')) == report, 'existing v18 evidence differs'
else:
    out.write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
raise SystemExit(bool(errors))
