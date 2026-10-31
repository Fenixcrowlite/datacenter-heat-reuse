"""Independent v30 numerical oracle and equation QA; no MATLAB imports.

Scenario constants are engineering assumptions. Decimal exponential and
independent temperature RK4 checks avoid importing the production TES kernel.
"""
from decimal import Decimal, localcontext
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import math
import random

ROOT = Path(__file__).resolve().parents[1]
PORTS = ['Mode','HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW',
         'Gas_Heat_MW','Unmet_Heat_MW','Storage_E_After_Loss_MWh',
         'Storage_E_Next_MWh','Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh',
         'Storage_Discharge_Loss_MWh','Supplied_Heat_MW','System_Balance_Residual_MWh',
         'Storage_T_Start_C','Storage_T_Next_C','Storage_Usable_Start_MWh',
         'Storage_Usable_Next_MWh']
HP = ['Heat_Demand_MW','HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW',
      'HP_Request_MW','COP','HP_Available','Source_Unused_MW']

def coefficients(rate, dt):
    with localcontext() as ctx:
        ctx.prec = 60
        k, h = Decimal(str(rate)), Decimal(str(dt))
        r = (-k*h).exp()
        phi = h if not k else (1-r)/k
        return float(r), float(phi), float(h-phi)

def tank(a, charge, discharge, p):
    dt, cap, cl, dl, ec, ed, rate, cut, c, ta, _ = p
    r, phi, beta = coefficients(rate, dt)
    cb = max(0., (cap-a*r)/(phi*ec))
    db = max(0., (a*r-cut)*ed/phi)
    qc, qd = min(charge, cl, cb), min(discharge, dl, db)
    power = ec*qc-qd/ed
    end = a*r+power*phi
    return qc, qd, a*r, end, a*(1-r)+power*beta, (1-ec)*qc*dt, (1/ed-1)*qd*dt

def heatpump(source, tc, th, request, h):
    cap, efficiency, low, high, penalty, backend, c0, c1, c2 = h
    nominal = min(high, efficiency*(th+273.15)/(th-tc) if backend == 0
                  else c0+c1*(th-tc)+c2*(th-tc)**2)
    if not source or not request or not cap or nominal < low:
        return 0., 0., 0., math.nan, 0
    intercept, slope = nominal*(1-penalty), nominal*penalty/cap
    upper = min(request, cap)
    lower = max(0., (low-intercept)/slope) if slope else 0.
    def evaporator(q):
        return q-q/(intercept+slope*q) if q else 0.
    if lower > upper or evaporator(lower) > source:
        return 0., 0., 0., math.nan, 0
    q = upper
    if evaporator(q) > source:
        if not slope:
            q = source*intercept/(intercept-1)
        else:
            # Analytic positive root, distinct from production 80-step bisection.
            b = intercept-1-source*slope
            disc = math.sqrt(b*b+4*slope*source*intercept)
            q = (2*source*intercept/(disc+b) if b >= 0
                 else (disc-b)/(2*slope))
    cop = intercept+slope*q
    return q, q/cop, q-q/cop, cop, 1

def dispatch(a, x, p, h):
    source, tc, th, demand, _ = x
    _, _, _, _, ec, _, _, _, c, ta, boiler = p
    r, phi, _ = coefficients(p[6], p[0])
    request = demand+min(p[2], max(0., (p[1]-a*r)/(phi*ec)))
    q, w, qe, cop, available = heatpump(source, tc, th, request, h)
    direct = min(demand, q)
    qc, qd, passive, end, loss, lc, ld = tank(a, max(0., q-direct), max(0., demand-direct), p)
    gas = min(boiler, max(0., demand-direct-qd))
    unmet = max(0., demand-direct-qd-gas)
    mode = 5 if unmet else 4 if gas else 3 if qd else 2 if qc else 1 if direct else 0
    supplied = direct+qd+gas
    residual = (qe+w+gas)*p[0]+a-supplied*p[0]-end-loss-lc-ld
    y = [mode,direct,qc,qd,gas,unmet,passive,end,loss,lc,ld,supplied,residual,
         ta+a/c,ta+end/c,max(0.,a-p[7]),max(0.,end-p[7])]
    u = [demand,q,w,qe,request,cop,available,max(0.,source-qe)]
    return y, u

def scenarios():
    base = [1.,10.,3.,4.,.9,.8,.1,5.,.2,20.,2.]
    hp = [8.,.45,1.2,8.,0.,1.,4.,0.,0.]
    cases = []
    def add(name, a, series, changes=None, h=None):
        p = base.copy()
        for i, val in (changes or {}).items(): p[i] = val
        cases.append(dict(id=name, initial_energy_MWh=a, p=p, h=h or hp,
                          inputs=[[s,35.,75.,d,45.] for s,d in series]))
    add('zero_demand',0,[(0,0)]*2)
    add('hp_only',3,[(3,4)]*2,{2:0})
    add('tes_charge',0,[(6,0)]*3)
    add('tes_discharge',9,[(0,1)]*2)
    add('boiler_limit',0,[(0,2)]*2)
    add('insufficient_heat',0,[(0,5)]*2)
    add('cutoff_endpoint',7,[(0,4)]*3)
    add('passive_cutoff_crossing',5.2,[(0,0),(0,1)])
    add('capacity_endpoint',9.9,[(6,0)]*3)
    add('mode_sequence',6,[(3,4),(6,0),(0,1),(0,4),(0,8),(0,0),(6,0)])
    add('high_rate',9,[(0,1),(6,0)],{6:2.})
    add('zero_rate',9,[(0,2),(6,0)],{6:0.})
    add('small_rate',9,[(0,1),(6,0)],{6:1e-12})
    add('zero_capacity',0,[(3,4),(0,5)],{1:0.,7:0.})
    for x in cases[-1]['inputs']: x[4] = 20.
    add('part_load_carnot',9,[(.2,4),(3,4),(0,1)],h=[8.,.45,1.2,8.,.15,0.,4.,0.,0.])
    for dt in (2.,1.,.5,.25):
        n = round(2/dt)
        # Cutoff is ambient for controlled integration comparisons, delivery20 C.
        for action, a, sd in [('charge',0.,(1.5,0.)),('discharge',10.,(0.,.5))]:
            add(f'partition_{action}_{dt:g}',a,[sd]*n,{0:dt,6:.2,7:0.,10:0.})
            for x in cases[-1]['inputs']: x[4] = 20.
    return cases

def equation_checks():
    checks = []
    def check(name, passed, **detail): checks.append(dict(name=name,passed=bool(passed),**detail))
    # RK4 in temperature, integrated ambient loss independently as a second state.
    rng = random.Random(30026)
    for i in range(120):
        p = [rng.uniform(.1,2),10.,3.,4.,.9,.8,rng.uniform(0,.8),5.,.2,20.,2.]
        a = rng.uniform(0,10)
        st = tank(a, rng.uniform(0,4) if i%2 else 0, rng.uniform(0,4) if not i%2 else 0,p)
        qc,qd,_,end,loss,lc,ld = st
        power = p[4]*qc-qd/p[5]; temperature = 20+a/.2; integrated=0.
        steps=1024; step=p[0]/steps
        def deriv(t): return (power-p[6]*.2*(t-20))/.2
        for _ in range(steps):
            k1=deriv(temperature); k2=deriv(temperature+step*k1/2)
            k3=deriv(temperature+step*k2/2); k4=deriv(temperature+step*k3)
            integrated+=step*p[6]*.2*((temperature-20)+2*(temperature+step*k1/2-20)+
                          2*(temperature+step*k2/2-20)+(temperature+step*k3-20))/6
            temperature+=step*(k1+2*k2+2*k3+k4)/6
        check(f'RK4_temperature_loss_{i}',abs(end-.2*(temperature-20))<2e-10 and abs(loss-integrated)<2e-10)
        check(f'port_closure_{i}',abs(a+(qc-qd)*p[0]-end-loss-lc-ld)<2e-12)
        # ODE trajectory is monotonic for fixed P; endpoints suffice for bounds.
        check(f'cutoff_capacity_{i}',0<=end<=10+1e-12 and (not qd or min(a,end)>=5-1e-12))
    check('ambient_offset_counterexample',(5.2*math.exp(-.1)-5)<0<(5.2-5)*math.exp(-.1))
    r,phi,beta=coefficients(1e-12,1.)
    check('small_rate_coefficients',phi>0 and beta>0 and abs(beta-5e-13)<1e-24)
    for power in (1.8,-.625):
        r,phi,_=coefficients(.2,2); whole=8*r+power*phi
        r1,p1,_=coefficients(.2,.5); divided=8
        for _ in range(4): divided=divided*r1+power*p1
        check(f'constant_power_semigroup_{power}',abs(whole-divided)<1e-13)
    return checks

def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder=ROOT/'audit'/f'stateflow_spec_v30_{stamp}'; folder.mkdir()
    cases=scenarios(); rows=[]
    for case in cases:
        a=case['initial_energy_MWh']
        for i,x in enumerate(case['inputs']):
            y,u=dispatch(a,x,case['p'],case['h'])
            row=dict(scenario_id=case['id'],step=i,Time_h=i*case['p'][0],Storage_E_Start_MWh=a)
            row.update({f'expected_{k}':v for k,v in zip(PORTS,y)})
            row.update({f'expected_{k}':v for k,v in zip(HP,u)})
            rows.append(row); a=y[7]
    (folder/'cases.json').write_text(json.dumps(dict(version='0.30',evidence_class='independent_scenario_specification',cases=cases),indent=2)+'\n')
    with (folder/'vectors.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    checks=equation_checks()
    report=dict(timestamp_utc=stamp,passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),
                checks=checks,qualifier='Reduced-equation QA; all scenario data assumed, no measured physical validation.',
                oracle_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'equation_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(spec_directory=str(folder.relative_to(ROOT)),scenarios=len(cases),intervals=len(rows),
                          passed=report['passed'],failed=report['failed'])))
    return int(report['failed']>0)

if __name__=='__main__': raise SystemExit(main())
