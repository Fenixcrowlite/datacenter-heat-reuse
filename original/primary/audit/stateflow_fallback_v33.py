"""Saved-v32 fallback experiment specification; checkpoint v33, no new model.

Inherited independent Decimal/bisection oracle supplies full traces. A second
closed-form recurrence below checks the targeted pulse/cooling mechanism without
calling that oracle. All fixtures/dwell examples are engineering assumptions.
"""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from stateflow_reference_v32 import dispatch, SEG, PORTS, HP

ROOT = Path(__file__).resolve().parents[1]

def stamp(): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, obj): path.write_text(json.dumps(obj, indent=2, allow_nan=True)+'\n', encoding='utf-8')
def csvsave(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=rows[0]);w.writeheader();w.writerows(rows)

def cases():
    families=[('unavailable_tail',9.9,6.,3.,.3,3.5),
              ('unavailable_initial_capacity',10.,6.,3.,.3,3.5),
              ('source_limited_initial_capacity',10.,.5,0.,0.,1.2),
              ('feasible_hold',9.9,6.,3.,.15,1.2),
              ('passive_capacity',10.,0.,0.,0.,1.2)]
    out=[]
    for family,e,source,demand,penalty,copmin in families:
        for dt in (2.,1.,.5,.25,.125):
            out.append(dict(id=f'{family}_h_{dt:g}',family=family,initial_energy_MWh=e,
                p=[dt,10.,3.,4.,.9,.8,.1,5.,.2,20.,.5],
                h=[8.,.45,copmin,8.,penalty,1.,4.,0.,0.],
                inputs=[[source,35.,75.,demand,45.]]*round(4/dt)))
    return out

def pulse_recurrence(e,dt):
    # Independent explicit logarithmic event inverse; no dispatch/event_tank call.
    eq=27.;cap=10.;rate=.1
    hit=math.log((eq-e)/(eq-cap))/rate
    on=min(dt,hit)
    end=eq+(e-eq)*math.exp(-rate*on)
    off=dt-on
    if off>0:end=cap*math.exp(-rate*off)
    return end,on,off

def dwell_example():
    # Proposed OFF service uses TES, unlike v32's capacity tail. Not executed SLX.
    cap=10.;cut=5.;rate=.1;pon=2.7;poff=-3/.8
    ton_min=toff_min=.25
    aon=pon/rate;aoff=poff/rate
    off_upper=aoff+(cap-aoff)*math.exp(-rate*toff_min)
    on_upper=aon+(cap-aon)*math.exp(rate*ton_min)
    restart=min(off_upper,on_upper)
    on=math.log((aon-restart)/(aon-cap))/rate
    off=math.log((cap-aoff)/(restart-aoff))/rate
    return dict(capacity_MWh=cap,cutoff_MWh=cut,on_internal_MW=pon,off_internal_MW=poff,
        assumed_min_on_h=ton_min,assumed_min_off_h=toff_min,
        off_dwell_restart_upper_MWh=off_upper,on_dwell_restart_upper_MWh=on_upper,
        proposed_restart_MWh=restart,on_duration_h=on,off_duration_h=off,
        feasible=cut<restart<cap and on>=ton_min-1e-12 and off>=toff_min-1e-12,
        engineering_example_only=True,executed_stateflow_policy=False)

def generate():
    folder=ROOT/'audit'/f'stateflow_fallback_spec_v33_{stamp()}';folder.mkdir()
    cc=cases();rows=[];segments=[];checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for c in cc:
        e=c['initial_energy_MWh'];independent=e;dt=c['p'][0]
        for i,x in enumerate(c['inputs']):
            y,ss=dispatch(e,x,c['p'],c['h'])
            r=dict(scenario_id=c['id'],step=i,Time_h=i*dt,Storage_E_Start_MWh=e)
            r.update(zip(PORTS+HP,y));rows.append(r)
            for j,s in enumerate(ss):
                r=dict(scenario_id=c['id'],step=i,segment=j+1);r.update(zip(SEG,s));segments.append(r)
            if c['family']=='unavailable_tail':
                independent,on,off=pulse_recurrence(independent,dt)
                ck(f'{c["id"]}_{i}_alternate_energy',abs(y[7]-independent)<1e-10)
                ck(f'{c["id"]}_{i}_alternate_electric',abs(y[19]*dt-6/3.7*on)<1e-10)
                ck(f'{c["id"]}_{i}_alternate_unmet',abs(y[5]*dt-2.5*off)<1e-10)
            if c['family'] in ('source_limited_initial_capacity','passive_capacity'):
                eq=6. if c['family'].startswith('source') else 0.
                independent=eq+(independent-eq)*math.exp(-.1*dt)
                ck(f'{c["id"]}_{i}_alternate_cooling',abs(y[7]-independent)<1e-10)
            ck(f'{c["id"]}_{i}_closure',abs(y[12])<1e-10)
            e=min(c['p'][1],max(0.,y[7]))
    d=dwell_example();ck('dwell_example_feasible',d['feasible'])
    # RK4 validates both ON and proposed OFF trajectory independently of exp/log.
    for power,duration,start,target in [(2.7,d['on_duration_h'],d['proposed_restart_MWh'],10.),
                                          (-3.75,d['off_duration_h'],10.,d['proposed_restart_MWh'])]:
        a=start;step=duration/4000
        for _ in range(4000):
            f=lambda v:power-.1*v
            k1=f(a);k2=f(a+step*k1/2);k3=f(a+step*k2/2);k4=f(a+step*k3)
            a+=step*(k1+2*k2+2*k3+k4)/6
        ck(f'candidate_RK4_{power}',abs(a-target)<1e-10)
    # Monotonic evaporator requirement on admitted COP domain: request reduction
    # can only lose availability at the minimum-load cutoff, not at source cap.
    for penalty in (0.,.15,.3,.6):
        alpha=4*(1-penalty);beta=4*penalty/8
        for q in (1.,3.,4.111111111111111,6.,8.):
            cop=alpha+beta*q
            if cop>=1.2:ck(f'source_requirement_monotone_{penalty}_{q}',1-alpha/cop**2>0)
    save(folder/'cases.json',dict(checkpoint_version='0.33',model_version='0.32',cases=cc,
        comparison_ids=[],evidence_class='independent_engineering_specification'))
    csvsave(folder/'vectors.csv',rows);csvsave(folder/'segments.csv',segments)
    save(folder/'dwell_example.json',d)
    save(folder/'equation_qa.json',dict(passed=sum(v['passed'] for v in checks),
        failed=sum(not v['passed'] for v in checks),checks=checks))
    prior=['Stateflow_manifest_v32_20261010T023036_007737Z.json',
           'TES_event_manifest_v31_20261009T214244_178000Z.json',
           'Stateflow_manifest_v30_20261009T213038_443584Z.json',
           'Stateflow_fault_manifest_v29_20261009T204014_224631Z.json']
    items={item['path']:item for m in prior for item in json.loads((ROOT/'audit'/m).read_text())['files']}
    save(folder/'preservation.json',list(items.values()))
    print(json.dumps(dict(spec_directory=str(folder.relative_to(ROOT)),scenarios=len(cc),intervals=len(rows),
        equation_passed=sum(v['passed'] for v in checks),equation_failed=sum(not v['passed'] for v in checks))))
    return int(any(not v['passed'] for v in checks))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['generate']);a=p.parse_args()
    raise SystemExit(generate())
