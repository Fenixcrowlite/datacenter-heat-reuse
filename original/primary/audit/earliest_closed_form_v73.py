"""Algorithmically independent original-MAT event trajectory QA.

No production MATLAB or production Taylor/bisection code is called. Binary64
operands become exact Fractions; event times and source integrals use Decimal
closed exponential/log solutions at 120/160 digits. This is same-agent QA,
not independent personnel or measured physical validation.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, struct, sys, zipfile
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
INF=D('Infinity')
def dec(v):
    if isinstance(v,D):return v
    v=F(v);return D(v.numerator)/D(v.denominator)
def contains(box,v):return dec(box[0])<=v<=dec(box[1])
def rows(v):return [v] if isinstance(v[0],(int,float)) else v
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def storage(E,B,lam,t):
    if lam==0:return E+B*t,E*t+B*t*t/2
    eq=B/lam;ex=(-lam*t).exp()
    return eq+(E-eq)*ex,eq*t+(E-eq)*(1-ex)/lam
def root(E,B,lam,target,direction):
    if (direction==1 and E>=target) or (direction==-1 and E<=target):return D(0)
    if lam==0:
        if B==0:return INF
        r=(target-E)/B;return r if r>0 else INF
    eq=B/lam
    if E==eq:return INF
    ratio=(target-eq)/(E-eq)
    return -ratio.ln()/lam if 0<ratio<1 else INF
def source_integral(E,B,lam,t,q,p):
    if q==0:return D(0)
    C,Ta=p[0],p[1];Te=p[11]-p[12]-p[13];a=p[14]*(Te+dec(273.15));floor=p[18]+p[19]
    switch=C*(floor-Ta-p[16]);end,_=storage(E,B,lam,t)
    spans=[D(0),t]
    if min(E,end)<switch<max(E,end):spans.insert(1,root(E,B,lam,switch,1 if end>E else -1))
    result=D(0)
    for lo,hi in zip(spans,spans[1:]):
        duration=hi-lo;initial,_=storage(E,B,lam,lo);middle,_=storage(E,B,lam,(lo+hi)/2)
        if middle<=switch:result+=q*a*duration/(a+floor+p[17]-Te);continue
        l0=Ta+p[16]+p[17]-Te
        if lam==0:
            denom=a+l0+initial/C;slope=B/C
            value=duration/denom if slope==0 else ((denom+slope*duration)/denom).ln()/slope
        else:
            eq=B/lam;K=a+l0+eq/C;R=(initial-eq)/C
            if K==0:value=((lam*duration).exp()-1)/(lam*R)
            else:value=duration/K+((K+R*(-lam*duration).exp())/(K+R)).ln()/(lam*K)
        result+=q*a*value
    return result

def analyze(run):
    checks=[];numeric=[]
    def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    pf=list(map(F,run['p']));p=list(map(dec,pf));uu=rows(run['input']);tr=rows(run['trace'])
    C,Ta=p[:2];cut=C*(p[3]-Ta);restart=C*(p[4]-Ta);stop=C*(p[24]-Ta);cap=C*(p[2]-Ta)
    E=dec(uu[0][9]);on=int(uu[0][10]);age=dec(uu[0][11]);clock=D(0);origin=E;total=[D(0)]*10
    for tick,(u,row) in enumerate(zip(uu,tr)):
        pre=f'{run["id"]}_{tick}';dt=dec(u[4]);demand=dec(u[5]);source=dec(u[6]);remaining=dt;local=D(0);ports=[D(0)]*10
        check(pre+'_schema',len(row)==1380 and row[1]==73 and row[75:100]==run['p'])
        check(pre+'_initial',contains(row[2:4],E));check(pre+'_clock_start',contains(row[57:59],clock))
        Te=p[11]-p[12]-p[13];a=p[14]*(Te+dec(273.15));floor=p[18]+p[19]
        ideal=min(p[10],source*p[12]*(1+(floor+p[17]-Te)/a),p[15]*p[16]);L=dec(row[56])
        check(pre+'_source_capacity_certificate',contains(row[65:67],source*p[12]))
        check(pre+'_source_limiter_certificate',contains(row[67:69],source*p[12]*(1+(floor+p[17]-Te)/a)))
        check(pre+'_water_limiter_certificate',contains(row[69:71],p[15]*p[16]))
        check(pre+'_selected_limiter',L<=dec(row[67]) and L<=dec(row[69]) and L<=p[10])
        check(pre+'_HP_limit',0<=L<=ideal and ideal-L<=D('1e-12')*max(D(1),ideal))
        actualevents=0
        for slot in range(int(row[12])):
            z=row[100+80*slot:180+80*slot];label=pre+f'_{slot}';event=int(z[2]);incoming=E;beforeAge=age;beforeOn=on
            potential=max(D(0),min(p[8],L-min(demand,L)));chargeEligible=u[8]==1 and E<stop and potential>0
            request=demand+(potential if chargeEligible else 0);future=demand>0 or u[8]==1 and potential>0
            reason=0
            if on and (L==0 or request==0):on=0;age=D(0);reason=3
            elif on and u[7]==0:
                check(label+'_ON_dwell',age>=p[21]);on=0;age=D(0);reason=2
            elif not on and u[7]==1 and L>0 and request>0 and E<=restart and age>=p[22]:on=1;age=D(0);reason=1
            hp,direct,charge,dis,boiler,unmet=map(dec,z[23:29])
            tolerance=D('1e-12')*max(D(1),demand,L)
            def close(x,y):return abs(x-y)<=tolerance
            check(label+'_hp_dispatch',close(hp,min(request,L) if on else D(0)))
            check(label+'_direct_priority',close(direct,min(demand,hp)))
            check(label+'_charge',close(charge,min(potential,max(D(0),hp-direct)) if chargeEligible else D(0)))
            check(label+'_discharge',close(dis,min(p[9],max(D(0),demand-direct)) if charge==0 and E>cut else D(0)))
            check(label+'_backup',close(boiler,min(p[23],max(D(0),demand-direct-dis))))
            check(label+'_unmet',close(unmet,max(D(0),demand-direct-dis-boiler)))
            check(label+'_power_bounds',all(v>=0 for v in [hp,direct,charge,dis,boiler,unmet]) and hp<=L and charge<=p[8] and dis<=p[9] and boiler<=p[23] and charge*dis==0)
            check(label+'_latch_start',z[18]==on and z[22]==reason and z[77]==beforeOn and contains(z[78:80],beforeAge) and contains(z[14:16],age))
            B=p[6]*charge-dis/p[7];check(label+'_forcing',contains(z[29:31],B))
            candidates=[(remaining,0)]
            if charge>0:candidates.append((root(E,B,p[5],stop,1),1))
            if dis>0:candidates.append((root(E,B,p[5],cut,-1),2))
            thermal=INF;wait=max(D(0),p[22]-age)
            if not on and u[7]==1 and L>0 and future:
                thermal=root(E,B,p[5],restart,-1);candidates.append((max(thermal,wait),3))
            duration,expected=min(candidates,key=lambda v:v[0])
            check(label+'_earliest_event',event==expected and duration>0)
            check(label+'_duration',contains(z[6:8],duration));check(label+'_time_start',contains(z[4:6],local));check(label+'_time_end',contains(z[8:10],local+duration))
            check(label+'_inventory_start',contains(z[10:12],E))
            endpoint,integral=storage(E,B,p[5],duration);thermalFlag=0;tag=0
            if event==1:endpoint=stop;thermalFlag=1;tag=1
            elif event==2:endpoint=cut;thermalFlag=1;tag=2
            elif event==3:
                if thermal>wait:endpoint=restart;thermalFlag=1;tag=3
                check(label+'_OFF_dwell',age+duration>=p[22]-D('1e-100'))
            check(label+'_contact_identity',z[3]==thermalFlag and z[21]==tag)
            if event:
                target=[stop,cut,restart][event-1]
                check(label+'_threshold',contains(z[75:77],target))
                if event!=3 or thermalFlag:check(label+'_root_hull',contains(z[71:73],duration))
                if event==3:check(label+'_wait_hull',contains(z[73:75],wait))
            check(label+'_inventory_end',contains(z[12:14],endpoint));check(label+'_TES_bounds',0<=endpoint<cap)
            heat=(direct+charge)*duration;src=source_integral(E,B,p[5],duration,direct+charge,p);work=heat-src
            standing=p[5]*integral;closs=(1-p[6])*charge*duration;dloss=(1/p[7]-1)*dis*duration
            service=(direct+dis+boiler)*duration;back=boiler*duration;missing=unmet*duration;aux=p[20]*work
            increment=[heat,src,work,standing,closs,dloss,service,back,missing,aux]
            for j,value in enumerate(increment):
                check(label+f'_nonnegative_energy_{j}',z[31+2*j]>=0 and value>=0)
                check(label+f'_energy_{j}',contains(z[31+2*j:33+2*j],value));check(label+f'_offset_{j}',contains(z[51+2*j:53+2*j],ports[j]))
                ports[j]+=value
            check(label+'_exact_first_law',abs(E+heat+back-service-endpoint-standing-closs-dloss)<D('1e-100')*max(D(1),E,heat))
            check(label+'_finite_source',src<=source*p[12]*duration and direct+charge<=p[15]*p[16])
            expectedmode=5 if unmet>0 else 4 if boiler>0 else 3 if dis>0 else 2 if charge>0 else 1 if direct>0 else 0
            check(label+'_mode',z[1]==expectedmode)
            age+=duration
            if event==1:on=0;age=D(0)
            elif event==3:on=1;age=D(0)
            check(label+'_latch_end',z[19]==on and contains(z[16:18],age))
            E=endpoint;local+=duration;remaining-=duration;actualevents+=event>0
            numeric.append(dict(id=run['id'],tick=tick,segment=slot,event=event,mode=expectedmode,duration=str(duration),time=str(clock+local),inventory=str(E),heat=str(heat),source=str(src),work=str(work),standing=str(standing),service=str(service),unmet=str(missing)))
        check(pre+'_entire_macro',abs(remaining)<D('1e-100') and actualevents==row[13])
        check(pre+'_final_inventory',contains(row[4:6],E));check(pre+'_final_latch',row[6]==on and contains(row[7:9],age));clock+=dt
        if row[61]==1:
            check(pre+'_retained_age_certificate',contains(row[63:65],age-dec(row[62])))
        check(pre+'_physical_clock',contains(row[9:11],clock));check(pre+'_origin',contains(row[50:52],origin))
        for j,v in enumerate(ports):
            total[j]+=v;check(pre+f'_total_{j}',contains(row[30+2*j:32+2*j],total[j]))
            if j<8:check(pre+f'_macro_{j}',contains(row[14+2*j:16+2*j],v))
        check(pre+'_unmet_macro',contains(row[54:56],ports[8]));check(pre+'_law_hull',row[52]<=0<=row[53])
        check(pre+'_cumulative_exact_law',abs(origin+total[0]+total[7]-total[6]-E-total[3]-total[4]-total[5])<D('1e-100')*max(D(1),origin,total[0]))
        check(pre+'_unused_slots_zero',all(v==0 for v in row[100+80*int(row[12]):]))
    return checks,numeric
