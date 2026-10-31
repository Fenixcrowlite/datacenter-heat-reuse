"""Independent v32 specification: Decimal event roots and analytic HP root.

Imports independent Python v30/v31 oracles only; no MATLAB production code.
All scenario values are engineering assumptions, not article measurements.
"""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from stateflow_reference_v30 import heatpump, coefficients, PORTS, HP, scenarios as v30_scenarios
from TES_event_reference_v31 import event_tank, equation_qa, component_cases

ROOT=Path(__file__).resolve().parents[1]
SEG=['Mode','Duration_h','Offset_h','Energy_Start_MWh','Energy_Next_MWh',
     'HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW',
     'Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW','HP_Request_MW',
     'COP','Source_Unused_MW','Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh',
     'Storage_Discharge_Loss_MWh','Supplied_Heat_MW','System_Balance_Residual_MWh',
     'Storage_T_Start_C','Storage_T_Next_C','Event_Kind','HP_Available']

def segment(a,span,offset,x,p,h,request,qc,qd,kind,hp_values=None):
    source,tc,th,demand,_=x
    q,w,ev,cop,available=hp_values or heatpump(source,tc,th,request,h)
    if span==0:
        q=w=ev=qc=qd=request=0.;cop=math.nan;available=0
    direct=min(demand,q) if span else 0.
    gas=min(p[10],max(0.,demand-direct-qd)) if span else 0.
    unmet=max(0.,demand-direct-qd-gas) if span else 0.
    mode=5 if unmet else 4 if gas else 3 if qd else 2 if qc else 1 if direct else 0
    r,phi,beta=coefficients(p[6],span)
    power=p[4]*qc-qd/p[5];end=a*r+power*phi
    loss=a*(1-r)+power*beta;lc=(1-p[4])*qc*span;ld=(1/p[5]-1)*qd*span
    supplied=direct+qd+gas
    residual=a+(w+ev+gas-supplied)*span-end-loss-lc-ld
    return [mode,span,offset,a,end,direct,qc,qd,gas,unmet,q,w,ev,request,cop,
            max(0,source-ev),loss,lc,ld,supplied,residual,p[9]+a/p[8],p[9]+end/p[8],kind,available]

def dispatch(a,x,p,h):
    # Numerical contract: recognize the exact capacity state to 64 binary ulps.
    # Decimal root finding otherwise promotes float port roundoff into events.
    if abs(a-p[1])<=64*math.ulp(max(1.,p[1])):a=p[1]
    request=x[3]+p[2]
    if a==p[1]:request=x[3]+min(p[2],p[6]*p[1]/p[4])
    hp=heatpump(x[0],x[1],x[2],request,h)
    direct=min(x[3],hp[0]);qc=min(p[2],max(0.,hp[0]-direct))
    qd=min(p[3],max(0.,x[3]-direct)) if a>p[7] else 0.
    event=event_tank(a,qc,qd,p);span=event[13];kind=event[14]
    if a==p[1] and not qd and abs(p[4]*qc-p[6]*p[1])<=64*math.ulp(max(1.,p[6]*p[1])):
        span=p[0];kind=0;event[3]=a
    s1=segment(a,span,0.,x,p,h,request,qc,qd,kind,hp)
    tail=p[0]-span
    if kind and tail>0:
        a2=event[17];r2=request
        if kind==1:r2=x[3]+min(p[2],p[6]*p[1]/p[4])
        hp2=heatpump(x[0],x[1],x[2],r2,h)
        qc2=min(p[2],max(0.,hp2[0]-min(x[3],hp2[0])))
        s2=segment(a2,tail,span,x,p,h,r2,qc2,0.,kind,hp2)
    else:s2=segment(event[3],0.,span,x,p,h,0.,0.,0.,kind)
    dt=p[0]
    integ=lambda i:sum(s[i]*s[1] for s in (s1,s2))
    losses=[s1[i]+s2[i] for i in (16,17,18)]
    supplied=integ(19)/dt;end=s2[4]
    residual=a+integ(11)+integ(12)+integ(8)-supplied*dt-end-sum(losses)
    mode=max(s[0] for s in (s1,s2) if s[1]>0)
    y=[mode]+[integ(i)/dt for i in (5,6,7,8,9)]+[a*math.exp(-p[6]*dt),end]+losses+[
        supplied,residual,p[9]+a/p[8],p[9]+end/p[8],max(0,a-p[7]),max(0,end-p[7])]
    w=integ(11);q=integ(10)
    u=[x[3],q/dt,w/dt,integ(12)/dt,integ(13)/dt,q/w if w else math.nan,
       int(q>0),x[0]-integ(12)/dt]
    return y+u,[s1,s2]

def scenarios():
    cases=v30_scenarios()[:15]
    base=[2.,10.,3.,4.,.9,.8,.1,5.,.2,20.,.5]
    hp=[8.,.45,1.2,8.,.15,1.,4.,0.,0.]
    def add(name,a,source,demand,dt=2.,changes=None,h=None,n=1):
        p=base.copy();p[0]=dt
        for i,v in (changes or {}).items():p[i]=v
        cases.append(dict(id=name,initial_energy_MWh=a,p=p,h=h or hp,
                          inputs=[[source,35.,75.,demand,45.]]*n))
    add('finite_backup_tradeoff',7.,0.,1.,h=[8,.45,1.2,8,0,1,4,0,0])
    add('capacity_nonlinear_COP',9.,6.,1.,n=2)
    add('initial_capacity_hold',10.,6.,1.,n=2)
    add('capacity_tail_HP_unavailable',9.9,6.,3.,h=[8,.45,3.5,8,.3,1,4,0,0],n=2)
    add('source_limited_hold',9.,.5,0.,n=2)
    add('source_limited_COP',9.,.2,4.,n=2)
    add('zero_capacity_charge_disabled',0.,6.,0.,changes={1:0.,7:0.})
    cases[-1]['inputs']=[[6.,35.,75.,0.,20.]]
    for family,a,source,demand in [('capacity',9.,6.,1.),('cutoff',7.,0.,1.),
                                 ('near_cutoff',5.2,0.,1.),('hp_only',0.,.75,1.),('idle',5.2,0.,0.)]:
        for dt in (2.,1.,.5,.25,.125):
            add(f'{family}_h_{dt:g}',a,source,demand,dt,changes={2:0.} if family=='hp_only' else {},n=round(2/dt))
    rng=random.Random(32026)
    for i in range(18):
        add(f'random_{i:02d}',rng.uniform(0,10),rng.uniform(0,6),rng.uniform(0,8),
            rng.uniform(.05,2),changes={6:rng.choice([0,1e-12,.1,1.])},n=2)
    return cases

def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'audit'/f'stateflow_spec_v32_{stamp}';folder.mkdir()
    cases=scenarios();rows=[];segments=[]
    for c in cases:
        a=c['initial_energy_MWh']
        for i,x in enumerate(c['inputs']):
            y,ss=dispatch(a,x,c['p'],c['h'])
            row=dict(scenario_id=c['id'],step=i,Time_h=i*c['p'][0],Storage_E_Start_MWh=a)
            row.update(zip(PORTS+HP,y));rows.append(row)
            for k,s in enumerate(ss):
                r=dict(scenario_id=c['id'],step=i,segment=k+1)
                r.update(zip(SEG,s));segments.append(r)
            a=min(c['p'][1],max(0.,y[7]))
    faults=['negative_source','negative_demand','delivery_above_cutoff','condenser_below_max',
            'negative_rate','cutoff_above_capacity','zero_heat_capacity','negative_boiler',
            'invalid_efficiency','invalid_backend','invalid_lift','above_capacity_state','dt_mismatch']
    mutations=['segment_wrong_mode','segment_false_COP','segment_unallocated_HP',
               'segment_excess_backup','segment_false_next_energy','segment_false_duration',
               'segment_false_event_offset','segment_false_loss']
    spec=dict(version='0.32',evidence_class='independent_specification',cases=cases,
              domain_faults=faults,monitor_faults=mutations,comparison_ids=[c['id'] for c in cases[:6]]+[
              'finite_backup_tradeoff','capacity_nonlinear_COP','source_limited_COP'])
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n')
    for name,data in [('vectors.csv',rows),('segments.csv',segments)]:
        with (folder/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
    # Independently RK4-verifies inherited Decimal event solution, not production.
    checks=equation_qa(component_cases())
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for c in cases:
        a=c['initial_energy_MWh']
        for i,x in enumerate(c['inputs']):
            y,ss=dispatch(a,x,c['p'],c['h'])
            ck(f'{c["id"]}_{i}_segment_service',all(abs(x[3]-s[5]-s[7]-s[8]-s[9])<1e-10 for s in ss if s[1]>0))
            ck(f'{c["id"]}_{i}_system_first_law',abs(y[12])<1e-10 and all(abs(s[20])<1e-10 for s in ss))
            ck(f'{c["id"]}_{i}_segment_HP',all(s[10]==0 or abs(s[10]-s[11]-s[12])<1e-10 for s in ss))
            a=min(c['p'][1],max(0.,y[7]))
    c=next(c for c in cases if c['id']=='finite_backup_tradeoff');y,ss=dispatch(7,c['inputs'][0],c['p'],c['h'])
    wrong=max(0,1-y[3]-.5)*2
    ck('finite_backup_average_arithmetic_rejected',y[5]*2>wrong+.1)
    c=next(c for c in cases if c['id']=='capacity_nonlinear_COP');y,ss=dispatch(9,c['inputs'][0],c['p'],c['h'])
    average_q=y[18];nominal=4.;wrong_cop=nominal*(1-.15+.15*average_q/8)
    ck('nonlinear_electricity_not_recomputed_from_average',abs(y[19]-average_q/wrong_cop)>1e-3 and ss[1][1]>0)
    previous=ROOT/'audit/TES_event_manifest_v31_20261009T214244_178000Z.json'
    preservation=json.loads(previous.read_text())['files']
    (folder/'preservation.json').write_text(json.dumps(preservation,indent=2)+'\n')
    report=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),
                checks=checks,physical_validation=False,article_replication=False)
    (folder/'equation_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(spec_directory=str(folder.relative_to(ROOT)),scenarios=len(cases),
                          intervals=len(rows),equation_passed=report['passed'],equation_failed=report['failed'])))
    return int(report['failed']>0)

if __name__=='__main__':raise SystemExit(main())
