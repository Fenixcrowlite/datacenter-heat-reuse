"""Targeted saved-v34 specification. All numerical fixtures are assumptions.

Closed-form dwell bounds plus inherited Decimal/bisection dispatch oracle;
no production MATLAB code is imported. This is a defect audit, not a release.
"""
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from stateflow_reference_v34 import scenarios, dispatch, PORTS, HP, SEG34

ROOT = Path(__file__).resolve().parents[1]


def on_bound(cap, power, rate, dwell):
    if rate == 0:
        return cap-power*dwell
    eq = power/rate
    return eq+(cap-eq)*math.exp(rate*dwell)


def reserve(cut, discharge, eta, rate, remaining):
    if rate == 0:
        return cut+discharge/eta*remaining
    eq = -discharge/(eta*rate)
    return eq+(cut-eq)*math.exp(rate*remaining)


def main():
    folder = ROOT/'audit'/('stateflow_spec_v35_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir()
    cases = scenarios()[:6]
    p = [0.5,10.,3.,4.,.9,.8,.1,5.,.2,20.,.5]
    h = [8.,.45,3.5,8.,.3,1.,4.,0.,0.]
    R = (-37.5)+(10+37.5)*math.exp(-.1*.25)
    families = {
        'demand_step': [(6,3),(6,8),(6,3),(6,0)],
        'source_step': [(6,3),(0,3),(6,3),(6,3)],
        'safe_held': [(6,3)]*4,
    }
    for family, timeline in families.items():
        for dt in (.5,.25,.125):
            q = p.copy();q[0] = dt
            inputs = [[s,35.,75.,d,45.] for s,d in timeline for _ in range(round(.5/dt))]
            cases.append(dict(id=f'{family}_h_{dt:g}',family=family,p=q,h=h,c=[R,.25,.25,64],
                              initial_energy_MWh=9.9,initial_clock=[1.,0.],inputs=inputs))
    q=p.copy();q[0]=.125
    cases.append(dict(id='off_dwell_overload',family='overload',p=q,h=h,c=[R,.25,.25,64],
                      initial_energy_MWh=9.9,initial_clock=[0.,0.],inputs=[[6.,35.,75.,8.,45.]]*4))
    scales = [10.,1e4,1e6,1e9]
    for cap in scales:
        cases.append(dict(id=f'scale_{cap:g}',family='scale',p=[.25,cap,3.,4.,.9,.8,0.,cap/2,cap/50,20.,.5],
                          h=h,c=[.8*cap,.25,.25,64],initial_energy_MWh=.6*cap,
                          initial_clock=[1.,0.],inputs=[[6.,35.,75.,3.,45.]]*2))
    rows=[];segments=[]
    for c in cases:
        e=c['initial_energy_MWh'];m=c['initial_clock']
        for i,x in enumerate(c['inputs']):
            y,ss,end=dispatch(e,x,c['p'],c['h'],m,c['c'])
            row=dict(scenario_id=c['id'],step=i,Time_h=i*c['p'][0],Storage_E_Start_MWh=e,
                     HP_Latch_Start=m[0],HP_Age_Start_h=m[1],HP_Latch_End=end[0],HP_Age_End_h=end[1])
            row.update(zip(PORTS+HP,y));rows.append(row)
            for j,s in enumerate(ss):
                row=dict(scenario_id=c['id'],step=i,segment=j+1)
                row.update(zip(SEG34,s));segments.append(row)
            e=y[7];m=end
    checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    # Separate RK4 verification of both dwell inversions, including zero-loss.
    for rate in (0.,1e-8,.1,.7):
        for dwell in (.05,.25,.75):
            a=on_bound(10,2.7,rate,dwell)
            b=reserve(5,4,.8,rate,dwell)
            for label,e,power,target in [('on',a,2.7,10),('off',b,-5.,5)]:
                dt=dwell/1024
                for _ in range(1024):
                    f=lambda v:power-rate*v
                    k1=f(e);k2=f(e+dt*k1/2);k3=f(e+dt*k2/2);k4=f(e+dt*k3)
                    e+=dt*(k1+2*k2+2*k3+k4)/6
                ck(f'{label}_{rate}_{dwell}_RK4',abs(e-target)<2e-6)
    ck('baseline_on_bound',R <= on_bound(10,2.7,.1,.25))
    ck('max_demand_reserve',R >= reserve(5,4,.8,.1,.25))
    ck('instantaneous_step_overload',8 > 4+.5)
    spec=dict(version='0.35',model_version='0.34',cases=cases,clock_corruption_h=.01,
              guard_age_h=.24,scales=scales,evidence_class='assumed_independent_targeted_specification',
              restart_MWh=R,nominal_on_bound_MWh=on_bound(10,2.7,.1,.25),
              robust_off_reserve_MWh=reserve(5,4,.8,.1,.25))
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n')
    for name,data in [('vectors.csv',rows),('segments.csv',segments)]:
        with (folder/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
    report=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    (folder/'equation_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('SPEC='+str(folder.relative_to(ROOT)));print(json.dumps({k:report[k] for k in ['passed','failed']}))
    assert not report['failed']


if __name__=='__main__':main()
