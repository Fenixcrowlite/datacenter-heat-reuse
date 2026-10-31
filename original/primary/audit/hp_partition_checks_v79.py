"""Exact rational necessary HP integral bounds, independent of MATLAB rounding."""
from fractions import Fraction as F
from earliest_closed_form_v73 import rows

def hp_checks(run):
    checks=[]; p=list(map(F,run['p']))
    # Decimal 273.15 is deliberately the exact binary64 production operand.
    Te=p[11]-p[12]-p[13]; A=p[14]*(Te+F(273.15))
    floor=p[18]+p[19]
    def check(name,ok):checks.append(dict(name=run['id']+'_'+name,passed=bool(ok)))
    for k,r in enumerate(rows(run['trace'])):
        for j in range(int(r[12])):
            z=r[100+80*j:180+80*j]; name=f'{k}_{j}'
            heat=list(map(F,z[31:33])); source=list(map(F,z[33:35])); work=list(map(F,z[35:37]))
            if z[23]==0:
                check(name+'_OFF_zero',source==work==[F(0),F(0)])
                continue
            elo=min(F(z[10]),F(z[12])); ehi=max(F(z[11]),F(z[13]))
            llo=max(floor,p[1]+elo/p[0]+p[16])+p[17]-Te
            lhi=max(floor,p[1]+ehi/p[0]+p[16])+p[17]-Te
            check(name+'_positive_axes',A>0 and 0<llo<=lhi)
            sb=[heat[0]*A/(A+lhi),heat[1]*A/(A+llo)]
            wb=[heat[0]*llo/(A+llo),heat[1]*lhi/(A+lhi)]
            check(name+'_source_partition',source[0]<=sb[1] and sb[0]<=source[1])
            check(name+'_work_partition',work[0]<=wb[1] and wb[0]<=work[1])
    return checks
