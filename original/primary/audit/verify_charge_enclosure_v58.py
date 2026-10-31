"""Independent exact-input coefficients and 80/120-digit analytic energy QA.
No production imports. Inputs/output intervals are original-MAT binary exports.
Independent algorithms by the same agent, not independent personnel.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import json, struct, hashlib, sys, copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(v):
    if isinstance(v,F):return D(v.numerator)/D(v.denominator)
    return D.from_float(v)
def coeff(s,p,E,request,branch,j):
    s={k:F(v) for k,v in s.items()};p={k:F(v) for k,v in p.items()}
    C=p['heat_capacity_MWh_per_K'];Ta=p['ambient_C'];d=s['charge_approach_K']
    Te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K'];a=s['cooling_factor']*(Te+F(273.15))
    S=s['source_capacity_MW_per_K']*s['source_glide_K'];H=s['hot_capacity_MW_per_K'];floor=s['delivery_C']+s['direct_approach_K']
    al=[F(0)]*5;be=[F(request),s['hp_capacity_MW'],F(0),F(0),p['charge_limit_MW']]
    if branch=='TANK':
        l0=Ta+d+s['condenser_approach_K']-Te;l1=1/C
        al[3]=S/(a*C);be[2]=H*d;be[3]=S*(1+l0/a)
    else:
        l0=floor+s['condenser_approach_K']-Te;l1=F(0)
        al[2]=-H/C;be[2]=H*(floor-Ta);be[3]=S*(1+l0/a)
    A=al[j];beta=be[j];k=p['eta_charge']*A-p['loss_rate_per_h'];B=p['eta_charge']*beta
    return dict(alpha_interval=A,beta_interval=beta,k_interval=k,B_interval=B,lift0_interval=l0,
                lift1_interval=l1,cooling_coefficient_interval=a),al,be,S,s,p
def evaluate(s,p,E,t,request,branch,j,precision):
    with localcontext() as ctx:
        ctx.prec=precision
        cf,al,be,S,sf,pf=coeff(s,p,E,request,branch,j)
        A,b,k,B,l0,l1,a=[dec(cf[x]) for x in ['alpha_interval','beta_interval','k_interval','B_interval','lift0_interval','lift1_interval','cooling_coefficient_interval']]
        dt=dec(t);e=dec(E);v=k*e+B;x=k*dt
        # Independent exponential series to avoid cancellation near k=0.
        term=D(1);phi1=D(1);phi2=D('0.5')
        for n in range(1,precision+30):
            term*=x/D(n+1);phi1+=term;phi2+=term/D(n+2)
        finish=e+v*dt*phi1;intE=e*dt+v*dt*dt*phi2;heat=A*intE+b*dt
        if j==3:source=dec(S)*dt
        elif branch=='FLOOR':source=heat*a/(l0+a)
        else:
            # All non-source TANK limits are constant q. With y=L+a,
            # y'=k*y+c, integral(1/y)=(log(y1/y0)-k*t)/c.
            y0=l0+a+l1*e;y1=l0+a+l1*finish
            c_exact=cf['lift1_interval']*cf['B_interval']-cf['k_interval']*(cf['lift0_interval']+cf['cooling_coefficient_interval'])
            v_exact=cf['k_interval']*F(E)+cf['B_interval']
            if v_exact==0:J=dt/y0
            elif c_exact==0:J=(1-(-k*dt).exp())/(k*y0)
            else:J=((y1/y0).ln()-k*dt)/dec(c_exact)
            source=b*a*J
        work=heat-source;standing=dec(pf['loss_rate_per_h'])*intE
        loss=(1-dec(pf['eta_charge']))*heat;aux=dec(sf['aux_per_compressor'])*work
        expected=dict(end_energy_MWh_interval=finish,integral_energy_MWh_h_interval=intE,
            heat_MWh_interval=heat,source_MWh_interval=source,compressor_MWh_interval=work,
            standing_loss_MWh_interval=standing,charge_loss_MWh_interval=loss,aux_rejected_MWh_interval=aux,
            first_law_MWh_interval=e+heat-finish-standing-loss)
        expected.update({name:dec(value) for name,value in cf.items()})
        # Regime validity independently at both exact endpoints (affine gaps).
        Es=[F(E),F(finish)];ok=True
        for en in Es:
            q=[ai*en+bi for ai,bi in zip(al,be)]
            gap=pf['ambient_C']+en/pf['heat_capacity_MWh_per_K']+sf['charge_approach_K']-sf['delivery_C']-sf['direct_approach_K']
            ok &= (gap>0 if branch=='TANK' else gap<0) and q[j]>0 and all(q[j]<q[n] for n in range(5) if n!=j)
            ok &= 0<=en<pf['heat_capacity_MWh_per_K']*(sf['tank_max_C']-pf['ambient_C'])
        return expected,bool(ok)
def contains(iv,point):return dec(iv[0])<=point<=dec(iv[1])
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());manifest=json.loads((folder/'binary_manifest.json').read_text())
    checks=[];mutations=[];traces=[];regimes=set();byid={v['input']['id']:v for v in report['runs']}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_report',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(x['passed'] for x in report['assertions']))
    check('scope','no_coupled_acceptance',not report['coupled_stateflow_acceptance'] and not report['new_model'])
    values=0;binary_hashes=[];fixture=None;worst_width=D(0)
    for rec in manifest['records']:
        path=(folder/rec['file']).resolve();assert path.is_relative_to(folder/'binary')
        payload=path.read_bytes();numbers=[v[0] for v in struct.iter_unpack('<d',payload)];values+=len(numbers)
        binary_hashes.append(dict(path=rec['file'],sha256=sha(path)));count=rec['input_count'];inputs=numbers[:count]
        E,t,request=inputs[:3];offset=3
        s=dict(zip(rec['s_names'],inputs[offset:offset+len(rec['s_names'])]));offset+=len(rec['s_names'])
        p=dict(zip(rec['p_names'],inputs[offset:]));result=byid[rec['id']];fine=result['fine'];branch=fine['branch'];j=fine['limiter_index']-1
        check('binary',rec['id'],len(numbers)==count+64 and s==result['input']['s'] and p==result['input']['p'] and E==result['input']['E'] and t==result['dt'] and request==result['input']['request'])
        regimes.add((branch,j));lo,ok=evaluate(s,p,E,t,request,branch,j,80);hi,okhi=evaluate(s,p,E,t,request,branch,j,120)
        check('independent_regime',rec['id'],ok and okhi)
        for level in range(2):
            out=result['coarse' if level==0 else 'fine'];start=count+level*32
            for n,name in enumerate(rec['output_names']):
                iv=numbers[start+n*2:start+n*2+2];want=hi[name]
                check('original_binary_binding',rec['id']+str(level)+name,iv==out[name])
                check('analytic_enclosure',rec['id']+str(level)+name,contains(iv,want) and contains(iv,lo[name]))
                with localcontext() as ctx:
                    ctx.prec=120
                    check('precision_stability',rec['id']+str(level)+name,abs(want-lo[name])<D('1e-65')*max(D(1),abs(want)))
                traces.append(dict(id=rec['id'],level=level,quantity=name,lower=iv[0],upper=iv[1],reference=str(want)))
        width=dec(fine['source_MWh_interval'][1])-dec(fine['source_MWh_interval'][0]);worst_width=max(worst_width,width)
        check('refinement',rec['id'],width<=dec(result['coarse']['source_MWh_interval'][1])-dec(result['coarse']['source_MWh_interval'][0])+D('1e-12'))
        if branch=='TANK' and j==0 and fixture is None:fixture=(copy.deepcopy(fine),hi)
    check('regime_coverage','ten_regimes',len(regimes)==10)
    witness=report['blocker'];s=witness['input']['s'];p=witness['input']['p']
    gap=F(p['ambient_C'])+F(witness['energy_MWh'])/F(p['heat_capacity_MWh_per_K'])+F(s['charge_approach_K'])-F(s['delivery_C'])-F(s['direct_approach_K'])
    check('blocker','exact_nonrepresentable_kink',gap!=0 and witness['identifier']=='DCHR:v55:UnresolvedBranch')
    check('blocker','event_enclosure_rejection',any(v['id']=='nominal_event_endpoint' and v['identifier']=='DCHR:v58:EventUnresolved' for v in report['faults']))
    # Deliberately corrupt endpoints/ports/coefficients and require rejection.
    fine,expected=fixture
    for name in ['end_energy_MWh_interval','source_MWh_interval','compressor_MWh_interval','alpha_interval','cooling_coefficient_interval']:
        bad=copy.deepcopy(fine);point=expected[name];bad[name]=[float(point)+.01,float(point)+.02]
        mutations.append(dict(name=name,passed=not contains(bad[name],point)))
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):
        check('source',rec['path'],sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    executions=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','actual_success_receipt',any(x['exit_code']==0 for x in executions))
    check('MAT','original_file',(folder/'charge_enclosure_v58.mat').stat().st_size>1000)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    result=dict(version='0.58',timestamp_utc=datetime.now(timezone.utc).isoformat(),scope='SINGLE_REGIME_ENCLOSURES_ONLY',
        summary=dict(passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks)),
        reviewer_selfchecks=dict(passed=sum(x['passed'] for x in mutations),failed=sum(not x['passed'] for x in mutations)),
        cases=len(manifest['records']),regimes=len(regimes),binary_values=values,exact_kink_gap_K=str(gap),
        max_source_enclosure_width_MWh=str(worst_width),checks=checks,mutations=mutations,binary_hashes=binary_hashes)
    output=folder/f'independent_QA_v58_{stamp}.json';output.write_text(json.dumps(result,indent=2)+'\n')
    import csv
    with (folder/f'analytic_traces_v58_{stamp}.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(traces[0]));writer.writeheader();writer.writerows(traces)
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','mutations','binary_hashes']}))
    if result['summary']['failed'] or result['reviewer_selfchecks']['failed']:sys.exit(1)
if __name__=='__main__':main()
