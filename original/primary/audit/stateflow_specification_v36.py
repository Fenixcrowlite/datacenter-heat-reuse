"""Unified inherited independent fixtures; no production MATLAB imports.

Decimal coefficient/bisection oracle retained at v34, v35 changing-input and
energy-scale counterexamples retained. This generator writes only new v36 specs.
"""
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from stateflow_reference_v34 import scenarios, dispatch, PORTS, HP, SEG34

ROOT=Path(__file__).resolve().parents[1]

def main():
    prior=json.loads((ROOT/'results/stateflow_admissibility_v35_20261010T072819778Z/source_snapshot/spec/cases.json').read_text())
    cases=scenarios()+prior['cases'][6:]
    folder=ROOT/'audit'/('stateflow_spec_v36_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    rows=[];segments=[];checks=[]
    for c in cases:
        e=c['initial_energy_MWh'];m=c['initial_clock'];p=c['p']
        for i,x in enumerate(c['inputs']):
            y,ss,end=dispatch(e,x,p,c['h'],m,c['c'])
            row=dict(scenario_id=c['id'],step=i,Time_h=i*p[0],Storage_E_Start_MWh=e,
                     HP_Latch_Start=m[0],HP_Age_Start_h=m[1],HP_Latch_End=end[0],HP_Age_End_h=end[1])
            row.update(zip(PORTS+HP,y));rows.append(row)
            for j,s in enumerate(ss):
                row=dict(scenario_id=c['id'],step=i,segment=j+1)
                row.update(zip(SEG34,s));segments.append(row)
                # Alternate RK4 physical integration, tolerances in MWh only.
                a=s[3];loss=0.;step=s[1]/1024;power=p[4]*s[6]-s[7]/p[5]
                for _ in range(1024):
                    f=lambda v:power-p[6]*v
                    k1=f(a);k2=f(a+step*k1/2);k3=f(a+step*k2/2);k4=f(a+step*k3)
                    loss+=step*p[6]*(a+2*(a+step*k1/2)+2*(a+step*k2/2)+(a+step*k3))/6
                    a+=step*(k1+2*k2+2*k3+k4)/6
                tol=1e-8+4096*math.ulp(max(1,p[1]))  # RK4 accumulated rounding bound
                checks.append(dict(name=f'{c["id"]}_{i}_{j}_RK4',passed=abs(a-s[4])<=tol and abs(loss-s[16])<=tol))
            e=y[7];m=end
    checks.append(dict(name='unique_scenario_ids',passed=len({c['id'] for c in cases})==len(cases)))
    spec=dict(prior,version='0.36',model_version='0.36',cases=cases,
              evidence_class='assumed_independent_Decimal_bisection_and_RK4_specification',
              physical_time_tolerance_max_h=1e-8)
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
    for name,data in [('vectors.csv',rows),('segments.csv',segments)]:
        with (folder/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
    report=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    (folder/'equation_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('SPEC='+str(folder.relative_to(ROOT)));print(json.dumps({k:report[k] for k in ['passed','failed']}))
    assert not report['failed']

if __name__=='__main__':main()
