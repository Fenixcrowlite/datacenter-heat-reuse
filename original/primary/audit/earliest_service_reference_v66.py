"""Independent high-precision engineering comparator, not a Stateflow model.

Exact binary inputs; maximum admissible constant HP charge/discharge, thermal
stop/cutoff/restart roots and OFF dwell. Fixed held demand/source schedules.
No production components imported. Used only on explicit repeated fixtures.
"""
from decimal import Decimal as D
from fractions import Fraction as F
from verify_capacity_chain_v63 import dec
from verify_interval_dispatch_v65 import storage

def compare(cfg, inputs):
    p=list(map(F,cfg[35:]));C,Ta,Tmax,cutT,restart,lam,etaC,etaD,cmax,dmax,nom,sourceIn,glide,evap,fc,H,app,cond,delivery,directapp,aux,minON,minOFF,bmax,stopT=p
    assert lam>0
    E=dec(F(inputs[0][9]));on=int(inputs[0][10]);age=dec(F(inputs[0][11]));initial=E
    cut=dec(C*(cutT-Ta));stop=dec(C*(stopT-Ta));restartE=dec(C*(restart-Ta))
    clock=D(0);ports={k:D(0) for k in ['heat','delivered','boiler','unmet','standing','charge_loss','discharge_loss']};events=[];samples=[]
    def root(target,B):
        eq=dec(B/lam)
        if E==target:return D(0)
        ratio=(target-eq)/(E-eq)
        return -ratio.ln()/dec(lam) if 0<ratio<1 else D('Infinity')
    for tick,u in enumerate(inputs):
        assert u[0]==1 and u[5] in [0,6] and u[6] in [0,20]
        remaining=dec(F(u[4]));demand=F(u[5]);source=F(u[6]);chargeEnable=int(u[8]);enable=int(u[7])
        Te=sourceIn-glide-evap;a=fc*(Te+F(273.15));floor=delivery+directapp
        hpLimit=min(nom,H*app,source*glide*(1+(floor+cond-Te)/a))
        for iteration in range(20):
            if remaining==0:break
            # Exact event policy. Zero source/sink and thermal stop override ON dwell.
            candidate=min(cmax,hpLimit) if chargeEnable else F(0)
            if on and (not candidate or E>=stop):
                on=0;age=D(0);events.append(dict(time=str(clock),kind='OFF',tick=tick))
            if not on and enable and candidate and E<=restartE and age>=dec(minOFF):
                on=1;age=D(0);events.append(dict(time=str(clock),kind='ON',tick=tick))
            charge=candidate if on else F(0)
            dis=min(demand,dmax) if not charge and E>cut else F(0)
            boiler=min(bmax,demand-dis);unmet=demand-dis-boiler
            B=etaC*charge-dis/etaD
            candidates=[(remaining,'sample_end')]
            if charge:candidates.append((root(stop,B),'thermal_stop'))
            elif dis:candidates.append((root(cut,B),'cutoff'))
            elif not on and enable and candidate:
                thermal=D(0) if E<=restartE else root(restartE,F(0))
                wait=max(D(0),dec(minOFF)-age)
                candidates.append((max(thermal,wait),'restart_ready'))
            duration,event=min(candidates,key=lambda v:v[0])
            assert duration>0, (tick,event,E,age)
            finite=sorted(v[0] for v in candidates if v[0].is_finite())
            if len(finite)>1 and finite[0]!=finite[1]:
                # Refuse numerically unresolved root/sample ordering in this comparator.
                assert finite[1]-finite[0]>D('1e-90')*max(D(1),abs(clock))
            endpoint,integ=storage(E,B,lam,duration)
            ports['heat']+=dec(charge)*duration;ports['delivered']+=dec(dis+boiler)*duration
            ports['boiler']+=dec(boiler)*duration;ports['unmet']+=dec(unmet)*duration
            ports['standing']+=dec(lam)*integ;ports['charge_loss']+=dec((1-etaC)*charge)*duration
            ports['discharge_loss']+=dec((1/etaD-1)*dis)*duration
            E=endpoint;clock+=duration;age+=duration;remaining-=duration
            if event=='thermal_stop':
                E=stop;on=0;age=D(0);events.append(dict(time=str(clock),kind='thermal_stop_OFF',tick=tick))
            elif event=='cutoff':E=cut;events.append(dict(time=str(clock),kind='cutoff',tick=tick))
            elif event=='restart_ready':
                # Physical dwell boundary is exact here; the endpoint is checked.
                assert E<=restartE+D('1e-100') and age>=dec(minOFF)-D('1e-100')
                if E>restartE:E=restartE
                if age<dec(minOFF):age=dec(minOFF)
                on=1;age=D(0);events.append(dict(time=str(clock),kind='ON',tick=tick))
        else:raise AssertionError('Comparator event budget exhausted')
        assert remaining==0 and E>=0
        samples.append(dict(tick=tick,inventory=str(E),clock=str(clock),latch=on))
    law=initial+ports['heat']+ports['boiler']-ports['delivered']-E-ports['standing']-ports['charge_loss']-ports['discharge_loss']
    assert abs(law)<D('1e-95')*max(D(1),initial)
    return dict(ports={k:str(v) for k,v in ports.items()},final_inventory=str(E),first_law=str(law),events=events,samples=samples)
