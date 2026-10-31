"""Independent v34 fixtures: Decimal integration, bisection energy-event times,
analytic quadratic HP source solve. No MATLAB source is imported.
All controls/plant values are engineering assumptions, not paper data.
"""
import csv,json,math
from pathlib import Path
from datetime import datetime,timezone
from stateflow_reference_v30 import heatpump,coefficients,PORTS,HP,scenarios as old_cases
from stateflow_reference_v32 import SEG,dispatch as legacy_dispatch
ROOT=Path(__file__).resolve().parents[1]
SEG34=SEG+['HP_Latch','HP_Age_Start_h','HP_Age_End_h']

def endpoint(e,power,rate,t):
    r,phi,_=coefficients(rate,t)
    return e*r+power*phi

def crossing(e,target,power,rate,horizon):
    """Bracketed inverse independent of production logarithmic event formula."""
    end=endpoint(e,power,rate,horizon)
    if (e-target)*(end-target)>0:return math.inf
    if abs(e-target)<1e-13:return 0.
    lo,hi=0.,horizon
    for _ in range(90):
        mid=(lo+hi)/2;value=endpoint(e,power,rate,mid)
        if (e-target)*(value-target)>0:lo=mid
        else:hi=mid
    return (lo+hi)/2

def dispatch(e,x,p,h,m,c):
    initial=e;state,elapsed=m;time=0.;ss=[]
    while time<p[0]-1e-13:
        reason=0;remaining=p[0]-time
        if abs(e-p[1])<1e-12:e=p[1]
        if abs(e-p[7])<1e-12:e=p[7]
        highrequest=x[3]+p[2];high=heatpump(*x[:3],highrequest,h)
        cycle=p[4]*max(0,high[0]-x[3])>p[6]*p[1]+1e-12
        request=highrequest;values=high
        if state and e==p[1]:
            request=x[3]+min(p[2],p[6]*p[1]/p[4]);values=heatpump(*x[:3],request,h)
            if cycle and elapsed>=c[1]-1e-12:state=0;elapsed=0.;reason=2
            elif not values[0]:state=0;elapsed=0.;reason=1
        elif state and not values[0]:state=0;elapsed=0.;reason=1
        if not state and not reason and e<=c[0]+1e-12 and elapsed>=c[2]-1e-12 and high[0]>0:
            state=1;elapsed=0.;reason=3;request=highrequest;values=high
        if not state:request=0.;values=(0.,0.,0.,math.nan,0)
        q,w,ev,cop,available=values;direct=min(x[3],q)
        qc=min(p[2],max(0,q-direct));qd=min(p[3],max(0,x[3]-direct)) if e>p[7] else 0.
        power=p[4]*qc-qd/p[5];span=remaining;kind=0
        if qc and power>p[6]*p[1]+1e-12:
            t=crossing(e,p[1],power,p[6],remaining)
            if t<=span:span=t;kind=1
        elif qd:
            t=crossing(e,p[7],power,p[6],remaining)
            if t<=span:span=t;kind=2
        if not state and high[0]>0:
            tr=0. if e<=c[0]+1e-12 else crossing(e,c[0],power,p[6],remaining)
            t=max(tr,max(0,c[2]-elapsed))
            if 1e-12<t<span:span=t;kind=3
        elif state and e==p[1] and cycle and elapsed<c[1]-1e-12:
            if c[1]-elapsed<span:span=c[1]-elapsed;kind=4
        assert span>0 and len(ss)<c[3], 'event progress/exhaustion'
        gas=min(p[10],max(0,x[3]-direct-qd));unmet=max(0,x[3]-direct-qd-gas)
        mode=5 if unmet else 4 if gas else 3 if qd else 2 if qc else 1 if direct else 0
        r,phi,beta=coefficients(p[6],span);end=e*r+power*phi
        loss=e*(1-r)+power*beta;lc=(1-p[4])*qc*span;ld=(1/p[5]-1)*qd*span
        supplied=direct+qd+gas;residual=e+(w+ev+gas-supplied)*span-end-loss-lc-ld
        ss.append([mode,span,time,e,end,direct,qc,qd,gas,unmet,q,w,ev,request,cop,x[0]-ev,
                   loss,lc,ld,supplied,residual,p[9]+e/p[8],p[9]+end/p[8],kind,available,
                   state,elapsed,elapsed+span,reason])
        time+=span;elapsed+=span;e=end
        if kind==1:e=p[1]
        elif kind==2:e=p[7]
    integ=lambda i:sum(s[i]*s[1] for s in ss)
    losses=[sum(s[i] for s in ss) for i in (16,17,18)]
    supplied=integ(19)/p[0];residual=initial+integ(11)+integ(12)+integ(8)-supplied*p[0]-e-sum(losses)
    y=[max(s[0] for s in ss)]+[integ(i)/p[0] for i in (5,6,7,8,9)]+[initial*math.exp(-p[6]*p[0]),e]+losses+[
       supplied,residual,p[9]+initial/p[8],p[9]+e/p[8],max(0,initial-p[7]),max(0,e-p[7]),x[3],
       integ(10)/p[0],integ(11)/p[0],integ(12)/p[0],integ(13)/p[0],integ(10)/integ(11) if integ(11) else math.nan,
       int(integ(10)>0),x[0]-integ(12)/p[0]]
    return y,ss,[state,elapsed]

def scenarios():
    cases=old_cases()[:10]
    for a in cases:a.update(c=[8.,.25,.25,64],initial_clock=[1.,0.])
    p=[1.,10.,3.,4.,.9,.8,.1,5.,.2,20.,.5]
    h=[8.,.45,3.5,8.,.3,1.,4.,0.,0.]
    restart=(-3/.8/.1)+(10+3/.8/.1)*math.exp(-.1*.25)
    def add(name,e,inputs,dt=1.,control=None,hp=None,changes=None,clock=None):
        params=p.copy();params[0]=dt
        for k,v in (changes or {}).items():params[k]=v
        cases.append(dict(id=name,initial_energy_MWh=e,p=params,h=hp or h,
             inputs=[[s,35.,75.,d,45.] for s,d in inputs],c=control or [restart,.25,.25,64],initial_clock=clock or [1.,0.]))
    for dt in (4.,2.,1.,.5,.25,.125):
        for family,e in [('fallback',9.9),('initial_capacity',10.)]:
            add(f'{family}_h_{dt:g}',e,[(6.,3.)]*round(4/dt),dt)
        add(f'cutoff_h_{dt:g}',7.,[(0.,3.)]*round(4/dt),dt,control=[8.,.25,1.,64])
    add('physical_off_dwell',7.,[(6.,3.)]*4,.25,control=[8.,.25,.75,64],clock=[0.,0.])
    add('capacity_on_dwell',10.,[(6.,3.)]*4,.5,control=[8.,1.,.25,64],hp=[8,.45,1.2,8,0,1,4,0,0])
    add('source_demand_changes',9.9,[(6,3),(0,3),(6,8),(6,0),(6,3),(0,0)],.5)
    add('source_limited',10.,[(.5,0.)]*4,1.,hp=[8,.45,1.2,8,0,1,4,0,0])
    add('zero_loss_cycles',9.9,[(6,3)]*4,1.,changes={6:0})
    add('small_loss_cycles',9.9,[(6,3)]*4,1.,changes={6:1e-12})
    add('long_off_dwell_cutoff',9.9,[(6,3)]*4,1.,control=[8.,.25,2.,64])
    add('zero_on_dwell',10.,[(6,3)]*4,1.,control=[8.,0.,.25,64])
    add('no_charge_hp_only',3.,[(3,4)]*4,.25,changes={2:0},hp=[8,.45,1.2,8,0,1,4,0,0])
    return cases

def main():
    folder=ROOT/'audit'/('stateflow_spec_v34_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ'))
    folder.mkdir();cases=scenarios();rows=[];segments=[];checks=[]
    for case in cases:
        e=case['initial_energy_MWh'];m=case['initial_clock'];p=case['p']
        for i,x in enumerate(case['inputs']):
            y,ss,end=dispatch(e,x,p,case['h'],m,case['c'])
            row=dict(scenario_id=case['id'],step=i,Time_h=i*p[0],Storage_E_Start_MWh=e,
                     HP_Latch_Start=m[0],HP_Age_Start_h=m[1],HP_Latch_End=end[0],HP_Age_End_h=end[1])
            row.update(zip(PORTS+HP,y));rows.append(row)
            for j,s in enumerate(ss):
                r=dict(scenario_id=case['id'],step=i,segment=j+1,Transition_Reason=s[28]);r.update(zip(SEG34,s));segments.append(r)
                # RK4 separately integrates the physical ODE + standing-loss state.
                a=s[3];loss=0.;step=s[1]/256;power=p[4]*s[6]-s[7]/p[5]
                for _ in range(256):
                    f=lambda a:power-p[6]*a
                    k1=f(a);k2=f(a+step*k1/2);k3=f(a+step*k2/2);k4=f(a+step*k3)
                    loss+=step*p[6]*(a+2*(a+step*k1/2)+2*(a+step*k2/2)+(a+step*k3))/6
                    a+=step*(k1+2*k2+2*k3+k4)/6
                checks.append(dict(name=f'{case["id"]}_{i}_{j}_RK4',passed=abs(a-s[4])<1e-8 and abs(loss-s[16])<1e-8))
            e=y[7];m=end
    spec=dict(version='0.34',evidence_class='independent_specification',cases=cases,slots=64,
              assumptions='MW, MWh, physical hours; uncalibrated hysteresis/dwell fixture values')
    (folder/'cases.json').write_text(json.dumps(spec,indent=2)+'\n')
    for name,data in [('vectors.csv',rows),('segments.csv',segments)]:
        with (folder/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=data[0]);w.writeheader();w.writerows(data)
    # Bisection root and independent RK4 verify derivation, not production output.
    report=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),checks=checks)
    (folder/'equation_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    assert not report['failed'];print(folder.relative_to(ROOT));print(json.dumps({k:report[k] for k in ['passed','failed']}))
if __name__=='__main__':main()
