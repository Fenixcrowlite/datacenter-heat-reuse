"""Independent Decimal/bisection TES event oracle, numerical QA and specs.

No production-code imports. Inherited v30 oracle is used only for saved-model
expectations by the separate artifact reviewer, never for event equations.
"""
import csv
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
NAMES=['charge_avg_MW','discharge_avg_MW','passive_MWh','next_MWh','standing_MWh',
       'charge_loss_MWh','discharge_loss_MWh','start_C','next_C','usable_start_MWh',
       'usable_next_MWh','full_charge_MW','full_discharge_MW','event_time_h','event_kind',
       'tail_charge_MW','tail_discharge_MW','event_energy_MWh','charge_MWh','discharge_MWh']

def event_tank(a,charge,discharge,p):
    """Root-find a monotone trajectory numerically in Decimal; no log formula."""
    with localcontext() as ctx:
        ctx.prec=60
        dt,cap,cl,dl,ec,ed,rate,cut,c,ta=map(lambda v:Decimal(str(v)),p[:10])
        a,qc,qd=map(lambda v:Decimal(str(v)),(a,charge,discharge))
        assert dt>0 and cap>=0 and cl>=0 and dl>=0 and 0<ec<=1 and 0<ed<=1
        assert rate>=0 and 0<=cut<=cap and c>0 and ta>Decimal('-273.15')
        assert 0<=a<=cap and qc>=0 and qd>=0 and (not qc or not qd)
        qc=min(qc,cl);qd=min(qd,dl) if a>cut else Decimal(0)
        power=ec*qc-qd/ed
        def endpoint(start,power,t):
            r=(-rate*t).exp();phi=t if not rate else (1-r)/rate
            return start*r+power*phi
        trial=endpoint(a,power,dt);kind=0;tailc=Decimal(0);taild=Decimal(0)
        if qc and power>rate*cap and trial>=cap: kind=1;boundary=cap;tailc=rate*cap/ec
        elif qd and trial<=cut:kind=2;boundary=cut
        t=dt
        if kind:
            lo=Decimal(0);hi=dt
            for _ in range(210):
                mid=(lo+hi)/2;state=endpoint(a,power,mid)
                before=state<boundary if kind==1 else state>boundary
                if before:lo=mid
                else:hi=mid
            t=(lo+hi)/2
        ea=endpoint(a,power,t);loss1=a+power*t-ea;tail=dt-t
        if kind==1:end=cap;loss2=rate*cap*tail;ea=cap
        elif kind==2:end=endpoint(cut,Decimal(0),tail);loss2=cut-end;ea=cut
        else:end=ea;loss2=Decimal(0)
        ce=qc*t+tailc*tail;de=qd*t+taild*tail
        values=[ce/dt,de/dt,endpoint(a,Decimal(0),dt),end,loss1+loss2,
                (1-ec)*ce,(1/ed-1)*de,ta+a/c,ta+end/c,max(0,a-cut),max(0,end-cut),
                qc,qd,t,kind,tailc,taild,ea,ce,de]
        return [float(v) for v in values]

def service(z,dt,demand,boiler):
    t=z[13];rest=dt-t
    g1=min(boiler,max(0,demand-z[12]));g2=min(boiler,max(0,demand-z[16]))
    u1=max(0,demand-z[12]-g1);u2=max(0,demand-z[16]-g2)
    return g1*t+g2*rest,u1*t+u2*rest

def component_cases():
    base=[2.,10.,3.,4.,.9,.8,.1,5.,.2,20.]
    cases=[]
    def add(name,a,qc,qd,updates=None):
        p=base.copy()
        for i,v in (updates or {}).items():p[i]=v
        cases.append(dict(id=name,a=a,charge=qc,discharge=qd,p=p))
    add('near_cutoff',5.2,0,1)
    add('finite_backup_tradeoff',7,0,1)
    add('capacity_hit',9,3,0)
    add('initial_capacity',10,3,0)
    add('initial_cutoff',5,0,4)
    add('below_cutoff',4,0,4)
    add('zero_capacity',0,3,0,{1:0.,7:0.})
    add('zero_cutoff',2,0,4,{7:0.})
    add('zero_rate_charge',9,3,0,{6:0.})
    add('zero_rate_discharge',7,0,4,{6:0.})
    add('tiny_rate_charge',9,3,0,{6:1e-12})
    add('tiny_rate_discharge',7,0,4,{6:1e-12})
    add('unreachable_capacity',9,3,0,{6:1.})
    add('capacity_equilibrium',9,3,0,{6:.27})
    add('capacity_cools',10,1,0,{6:1.})
    add('high_rate_discharge',9,0,4,{6:20.})
    add('above_charge_limit',5,100,0)
    add('above_discharge_limit',9,0,100)
    add('passive',8,0,0)
    add('no_event_charge',0,1,0)
    add('no_event_discharge',10,0,.1)
    rng=random.Random(31026)
    for i in range(120):
        p=[rng.uniform(.05,4.),rng.uniform(.1,20.),rng.uniform(0,6),rng.uniform(0,6),
           rng.uniform(.2,1),rng.uniform(.2,1),rng.choice([0.,1e-12,rng.uniform(.01,3)]),0.,.2,20.]
        p[7]=rng.uniform(0,p[1]);a=rng.uniform(0,p[1]);q=rng.uniform(0,10)
        cases.append(dict(id=f'random_{i:03d}',a=a,charge=q if i%2 else 0.,
                          discharge=0. if i%2 else q,p=p))
    return cases

def comparison_cases():
    # Held source-limited COP4 produces 3 MW condenser potential for charging.
    base=[2.,10.,3.,4.,.9,.8,.1,5.,.2,20.,.5]
    h=[8.,.45,1.2,8.,0.,1.,4.,0.,0.]
    families=[('capacity',9.,2.25,0.,3.,0.,{}),
              ('cutoff',7.,0.,1.,0.,1.,{}),
              ('near_cutoff',5.2,0.,1.,0.,1.,{}),
              ('no_bound_charge',0.,.75,0.,1.,0.,{}),
              ('no_bound_discharge',10.,0.,.1,0.,.1,{}),
              ('passive_crossing',5.2,0.,0.,0.,0.,{}),
              ('zero_rate_cutoff',7.,0.,1.,0.,1.,{6:0.}),
              ('high_rate_cutoff',5.2,0.,1.,0.,1.,{6:1.}),
              ('hp_only',0.,.75,1.,0.,0.,{2:0.}),
              ('backup_only',0.,0.,.5,0.,.5,{})]
    cases=[]
    for family,a,source,demand,qc,qd,updates in families:
        for dt in (2.,1.,.5,.25,.125):
            p=base.copy();p[0]=dt
            for i,v in updates.items():p[i]=v
            cases.append(dict(id=f'{family}_dt_{str(dt).replace(".","p")}',family=family,
                              initial_energy_MWh=a,p=p,h=h,charge_request_MW=qc,
                              discharge_request_MW=qd,hp_direct_MW=1. if family=='hp_only' else 0.,
                              inputs=[[source,35.,75.,demand,45.]]*round(2/dt)))
    return cases

def rk4_segments(case,z):
    p=case['p'];dt,_,_,_,ec,ed,rate,_,c,ta=p[:10]
    temperature=ta+case['a']/c;ambient_loss=0.
    for span,qc,qd in [(z[13],z[11],z[12]),(dt-z[13],z[15],z[16])]:
        if span==0:continue
        n=max(1024,math.ceil(span*rate*1024));step=span/n;power=ec*qc-qd/ed
        def rhs(temp):return (power-rate*c*(temp-ta))/c
        for _ in range(n):
            k1=rhs(temperature);t2=temperature+step*k1/2;k2=rhs(t2)
            t3=temperature+step*k2/2;k3=rhs(t3);t4=temperature+step*k3;k4=rhs(t4)
            ambient_loss+=step*rate*c*((temperature-ta)+2*(t2-ta)+2*(t3-ta)+(t4-ta))/6
            temperature+=step*(k1+2*k2+2*k3+k4)/6
    return c*(temperature-ta),ambient_loss

def equation_qa(cases):
    checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for case in cases:
        p=case['p'];a=case['a'];z=event_tank(a,case['charge'],case['discharge'],p)
        end,loss=rk4_segments(case,z)
        ck(case['id']+'_independent_RK4',abs(end-z[3])<2e-9 and abs(loss-z[4])<2e-9)
        ck(case['id']+'_external_first_law',abs(a+z[18]-z[19]-z[3]-sum(z[4:7]))<2e-12)
        divided=a;totals=[0.]*5;small=p.copy();small[0]/=4
        for _ in range(4):
            part=event_tank(divided,case['charge'],case['discharge'],small)
            divided=part[3]
            for j,index in enumerate([18,19,4,5,6]):totals[j]+=part[index]
        ck(case['id']+'_semigroup',abs(divided-z[3])<2e-12 and
           all(abs(total-z[index])<2e-12 for total,index in zip(totals,[18,19,4,5,6])))
        ck(case['id']+'_event_bounds',0<=z[3]<=p[1]+1e-12 and 0<=z[13]<=p[0] and
           (not z[14] or abs(z[17]-p[1 if z[14]==1 else 7])<2e-12) and
           z[0]<=p[2]+1e-12 and z[1]<=p[3]+1e-12 and z[0]*z[1]==0)
    # Explicit examples prevent plausible but false backup-from-average logic.
    c=next(c for c in cases if c['id']=='finite_backup_tradeoff');z=event_tank(c['a'],0,1,c['p'])
    g,u=service(z,2,1,.5);average_unmet=max(0,1-z[1]-.5)*2
    ck('segment_backup_is_not_average_backup',u>average_unmet+.1 and abs(z[19]+g+u-2)<1e-12)
    # SI conversion of pulse duration/energy, no scenario value attributed to a paper.
    si_duration=(7*3.6e9-5*3.6e9)/(1e6/.8)
    zero=event_tank(7,0,1,[2,10,3,4,.9,.8,0,5,.2,20])
    ck('SI_time_and_energy_units',abs(si_duration/3600-zero[13])<1e-12 and
       abs(si_duration*1e6/3.6e9-zero[19])<1e-12)
    return checks

def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'audit'/f'TES_event_spec_v31_{stamp}';folder.mkdir()
    cases=component_cases();comparisons=comparison_cases();checks=equation_qa(cases)
    spec=dict(checkpoint_version='0.31',model_release='0.30',evidence_class='independent_event_spec',
              component_cases=cases,comparison_cases=comparisons)
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n')
    rows=[]
    for case in cases:
        row={'id':case['id']};row.update(zip(NAMES,event_tank(case['a'],case['charge'],case['discharge'],case['p'])));rows.append(row)
    with (folder/'component_vectors.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    report=dict(timestamp_utc=stamp,checks=checks,passed=sum(c['passed'] for c in checks),
                failed=sum(not c['passed'] for c in checks),evidence_class='independent_reduced_equation_QA',
                oracle_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                measured_validation=False,article_replication=False)
    (folder/'equation_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(spec_directory=str(folder.relative_to(ROOT)),component_cases=len(cases),
                          saved_model_scenarios=len(comparisons),equation_passed=report['passed'],equation_failed=report['failed'])))
    return int(report['failed']>0)

if __name__=='__main__':raise SystemExit(main())
