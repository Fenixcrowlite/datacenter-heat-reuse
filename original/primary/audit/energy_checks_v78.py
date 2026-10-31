"""Exact binary operand energy QA. Does not emulate MATLAB's eps operator.

Checks enclosures with Fraction endpoints and physical port equations;
nonlinear trajectory/source integrals remain in the separate closed-form lane.
"""
from fractions import Fraction as F
from earliest_closed_form_v73 import rows

def iv(v):return [F(x) for x in v]
def add(a,b):return [a[0]+b[0],a[1]+b[1]]
def sub(a,b):return [a[0]-b[1],a[1]-b[0]]
def scale(a,b):
    v=[x*y for x in a for y in b];return [min(v),max(v)]
def encloses(a,b):return F(a[0])<=b[0]<=b[1]<=F(a[1])
def overlap(a,b):return a[0]<=b[1] and b[0]<=a[1]
def point(v):return [F(v),F(v)]
def firstlaw(E,heat,back,service,end,standing,closs,dloss):
    return sub(sub(sub(sub(add(E,add(heat,back)),service),end),standing),add(closs,dloss))

def energy_checks(run):
    checks=[];p=list(map(F,run['p']));total=[[F(0),F(0)] for _ in range(10)]
    origin=point(run['adapter']['initial'][0])
    def check(name,ok):checks.append(dict(name=run['id']+'_'+name,passed=bool(ok)))
    for k,(u,r) in enumerate(zip(rows(run['input']),rows(run['trace']))):
        prefix=str(k);ports=[[F(0),F(0)] for _ in range(10)]
        check(prefix+'_origin',iv(r[50:52])==origin)
        for j in range(int(r[12])):
            z=r[100+80*j:180+80*j];q=list(map(F,z[23:29]));d=iv(z[6:8]);label=prefix+'_'+str(j)
            inc=[iv(z[31+2*b:33+2*b]) for b in range(10)]
            check(label+'_port_domain',z[0]==j+1 and z[1] in range(6) and all(v>=0 for v in q))
            check(label+'_power_capacity',q[0]<=F(r[56]) and q[2]<=p[8] and q[3]<=p[9] and q[4]<=p[23] and q[2]*q[3]==0 and (z[18]==1 or q[0]==0))
            # Binary allocation may have rounding; a conservative ulp bound
            # is independently computed from the input float's integer ratio.
            import math
            tol=F(math.ulp(max(1.,u[5],r[56])))*32
            check(label+'_HP_allocation',abs(q[0]-q[1]-q[2])<=tol)
            check(label+'_demand_allocation',abs(F(u[5])-q[1]-q[3]-q[4]-q[5])<=tol)
            mode=5 if q[5]>0 else 4 if q[4]>0 else 3 if q[3]>0 else 2 if q[2]>0 else 1 if q[1]>0 else 0
            check(label+'_mode',z[1]==mode)
            cap=p[0]*(p[2]-p[1]);check(label+'_TES',0<=F(z[10])<=F(z[11]) and 0<=F(z[12])<=F(z[13]) and F(z[13])<cap+tol)
            B=p[6]*q[2]-q[3]/p[7];check(label+'_forcing',encloses(z[29:31],point(B)))
            check(label+'_energy_domain',all(v[0]>=0 and v[0]<=v[1] for v in inc))
            for b in range(10):
                check(label+f'_offset_{b}',encloses(z[51+2*b:53+2*b],ports[b]))
                # Use the actual recorded offset hull for next accumulation.
                ports[b]=add(iv(z[51+2*b:53+2*b]),inc[b])
            for b,value in [(0,scale(point(q[1]+q[2]),d)),(6,scale(point(q[1]+q[3]+q[4]),d)),(7,scale(point(q[4]),d)),(8,scale(point(q[5]),d)),(4,scale(point((1-p[6])*q[2]),d)),(5,scale(point((1/p[7]-1)*q[3]),d)),(9,scale(point(p[20]),inc[2]))]:
                check(label+f'_port_energy_{b}',encloses(inc[b],value))
            check(label+'_HP_law',overlap(add(inc[1],inc[2]),inc[0]))
            law=firstlaw(iv(z[10:12]),inc[0],inc[7],inc[6],iv(z[12:14]),inc[3],inc[4],inc[5])
            check(label+'_segment_first_law',law[0]<=0<=law[1])
        macro=[iv(r[14+2*b:16+2*b]) for b in range(8)]+[iv(r[54:56]),ports[9]]
        for b in range(9):check(prefix+f'_interval_{b}',encloses(macro[b],ports[b]))
        for b in range(10):
            expected=add(total[b],ports[b]);reported=iv(r[30+2*b:32+2*b])
            check(prefix+f'_total_{b}',encloses(reported,expected));total[b]=reported
        law=firstlaw(origin,total[0],total[7],total[6],iv(r[4:6]),total[3],total[4],total[5])
        check(prefix+'_residual_binding',encloses(r[52:54],law) and r[52]<=0<=r[53])
    return checks
