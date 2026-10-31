"""Exact Fraction input algebra and independent Decimal saved-trace review.
No MATLAB production code imports; same-agent independent algorithm QA.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import json, sys, hashlib, copy, math
ROOT=Path(__file__).resolve().parents[1]
def f(x): return F.from_float(float(x))
def d(x): return D.from_float(float(x))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(x): return x if isinstance(x,list) else [x]
def encloses(interval,value): return len(interval)==2 and f(interval[0])<=value<=f(interval[1])
def algebra(v):
    s={k:f(x) for k,x in v['s'].items()};p={k:f(x) for k,x in v['p'].items()}
    T=p['ambient_C']+f(v['E'])/p['heat_capacity_MWh_per_K']
    tank=T+s['charge_approach_K'];floor=s['delivery_C']+s['direct_approach_K'];gap=tank-floor
    te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K']
    hot=max(tank,floor);tc=hot+s['condenser_approach_K'];a=s['cooling_factor']*(te+f(273.15))
    limits=[f(v['request']),s['hp_capacity_MW'],s['hot_capacity_MW_per_K']*(hot-T),
            s['source_capacity_MW_per_K']*s['source_glide_K']*(1+(tc-te)/a)]
    return dict(tank_C_interval=T,tank_outlet_interval=tank,floor_outlet_interval=floor,gap_K_interval=gap),limits
def vector_checks(v):
    want,limits=algebra(v);c=v['certificate'];gap=want['gap_K_interval']
    result={key:encloses(c[key],val) for key,val in want.items()}
    result.update({f'limit_{j}':encloses(iv,val) for j,(iv,val) in enumerate(zip(c['limit_MW_intervals'],limits))})
    result['limit_shape']=len(c['limit_MW_intervals'])==4
    branch=c['branch'];lo,hi=map(f,c['gap_K_interval'])
    expected='TANK' if lo>0 else 'FLOOR' if hi<0 else 'UNRESOLVED'
    result['interval_sign_policy']=branch==expected
    result['resolved_flag']=c['resolved']==(branch!='UNRESOLVED')
    result['exact_branch_sound']=branch=='UNRESOLVED' or (branch=='TANK' and gap>0) or (branch=='FLOOR' and gap<0)
    result['gate']=v['accepted']==(branch!='UNRESOLVED') and (v['accepted'] or v['identifier']=='DCHR:v55:UnresolvedBranch')
    result['nominal_agreement']=not v['accepted'] or c['nominal_boundary']['tank_branch']==(branch=='TANK')
    strict=c['source_strictly_limited'];ivs=c['limit_MW_intervals']
    result['strict_policy']=strict==(f(ivs[3][1])<min(f(iv[0]) for iv in ivs[:3]))
    result['strict_source_sound']=not strict or limits[3]<min(limits[:3])
    return result
def segment_checks(z,a):
    if z[1]==0:
        return dict(padding=z[3]==z[4] and z[0]==0 and all(v==0 for v in z[5:14]+z[16:21]) and z[26]==z[27])
    p=a['p'];span=d(z[1]);E=d(z[3]);rate=d(p[6]);P=d(p[4])*d(z[6])-d(z[7])/d(p[5])
    end=E*(-rate*span).exp()+P*(1-(-rate*span).exp())/rate if rate else E+P*span
    tol=72*d(math.ulp(max(1,p[1])))
    cop=d(a['h'][1])*(d(a['x'][2])+D('273.15'))/(d(a['x'][2])-d(a['x'][1]))
    q=min(d(a['h'][0]),d(z[13]),d(a['x'][0])*cop/(cop-1))
    def near(x,y):return abs(d(x)-y)<D('3e-12')*max(1,abs(y))
    return dict(held_ODE=abs(d(z[4])-end)<=tol,
                first_law=abs(E+(d(z[11])+d(z[12]))*span-d(z[4])-d(z[16])-d(z[17]))<=tol,
                ports=near(z[10],q) and near(z[11],d(z[10])/cop) and near(z[12],d(z[10])-d(z[11])),
                bounds=min(z[3:14])>=0 and max(z[3:5])<=p[1] and z[6]<=p[2] and z[12]<=a['x'][0]+1e-12,
                mode=z[0]==2 and z[5]==0 and z[6]==z[10] and all(v==0 for v in z[7:10]),
                losses=near(z[16],E+P*span-end) and near(z[17],(1-d(p[4]))*d(z[6])*span),
                clock=z[25]==1 and near(z[27],d(z[26])+span))
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    r=json.loads((folder/'report.json').read_text());checks=[];mutations=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','report_binding',r==json.loads((folder/'mat_reopen.json').read_text()))
    check('execution','MATLAB',r['summary']['failed']==0 and all(c['passed'] for c in r['assertions']))
    check('scope','saved_model',r['model_version']=='0.52' and r['new_model'] is False)
    check('Stateflow','license_and_charts',r['metadata']['stateflow_license_test']==1 and r['metadata']['chart_count']==2)
    spec=json.loads((folder/'spec.json').read_text());vectors=r['vectors']
    check('vectors','count_binding',len(vectors)==len(spec['vectors']))
    legacy_wrong=[];accepted=[];unresolved=[]
    for v,sv in zip(vectors,spec['vectors']):
        check('spec',v['id'],all(v[k]==sv[k] for k in ['id','s','p','E','request']))
        for key,ok in vector_checks(v).items():check('exact_rational',v['id']+'_'+key,ok)
        want,_=algebra(v);gap=want['gap_K_interval']
        if isinstance(v['legacy_branch'],bool) and v['legacy_branch']!=(gap>=0):
            legacy_wrong.append(dict(id=v['id'],exact_gap_fraction=str(gap),exact_gap_K=float(gap),rejected=not v['accepted']))
            check('legacy_defect',v['id'],not v['accepted'])
        (accepted if v['accepted'] else unresolved).append(v['id'])
    check('legacy_defect','all_twelve_reproduced_and_rejected',len(legacy_wrong)==12 and all(v['rejected'] for v in legacy_wrong))
    kink=next(v for v in vectors if v['id']=='kink_0.0_0');kgap=algebra(kink)[0]['gap_K_interval']
    check('witness','exact_binary_negative_gap',kgap<0 and kink['certificate']['nominal_boundary']['tank_branch'] and not kink['accepted'])
    check('coverage','resolved_both_sides',any(v['certificate']['branch']=='TANK' for v in vectors) and any(v['certificate']['branch']=='FLOOR' for v in vectors))
    check('coverage','limiter_both_policies',any(v['certificate']['source_strictly_limited'] for v in vectors) and any(not v['certificate']['source_strictly_limited'] for v in vectors))
    check('domains','six_actual_rejections',len(r['faults'])==6 and all(x['rejected'] for x in r['faults']))
    originals=json.loads((folder/'original_simulation_reopen.json').read_text())
    check('MAT','original_traces_binding',r['runs']==originals and len(originals)==2)
    with localcontext() as ctx:
        ctx.prec=80
        active=None;padding=None;segments=0
        for run in originals:
            a=run['inputs'];zs=[run['raw_segments'][j:j+28] for j in range(0,1792,28)];ps=[run['raw_plans'][j:j+23] for j in range(0,1472,23)]
            check('handoff',run['id'],all(zs[j][4]==zs[j+1][3] for j in range(63)) and all(z[3]==p[1] and z[4]==p[22] for z,p in zip(zs,ps)) and run['dispatch'][7]==zs[-1][4])
            duration=D(0);heat=D(0);work=D(0);source=D(0);loss=D(0);closs=D(0)
            for j,z in enumerate(zs):
                for key,ok in segment_checks(z,a).items():check('actual_'+key,run['id']+'_'+str(j),ok)
                if z[1]>0:
                    active=(z,a);segments+=1;duration+=d(z[1]);heat+=d(z[10])*d(z[1]);work+=d(z[11])*d(z[1]);source+=d(z[12])*d(z[1]);loss+=d(z[16]);closs+=d(z[17])
                else:padding=(z,a)
            check('macro',run['id'],abs(duration-d(a['dt_h']))<D('1e-15') and abs(d(a['E0'])+work+source-d(run['dispatch'][7])-loss-closs)<D('2e-12'))
            check('clock',run['id'],run['clock_start']==a['m0'] and abs(d(run['clock_end'][1])-duration)<D('1e-15'))
        # Reviewer mutations are synthetic and counted separately.
        resolved=next(v for v in vectors if v['certificate']['branch']=='TANK')
        m=copy.deepcopy(resolved);m['certificate']['gap_K_interval']=[0.,0.]
        mutations.append(dict(name='false_enclosure',passed=not all(vector_checks(m).values())))
        m=copy.deepcopy(kink);m['accepted']=True;m['certificate']['branch']='TANK';m['certificate']['resolved']=True
        mutations.append(dict(name='uncertain_branch_accepted',passed=not all(vector_checks(m).values())))
        m=copy.deepcopy(resolved);m['certificate']['source_strictly_limited']=not m['certificate']['source_strictly_limited']
        mutations.append(dict(name='limiter_flag_flipped',passed=not all(vector_checks(m).values())))
        z,a=copy.deepcopy(active);z[11]+=.01
        mutations.append(dict(name='compressor_corruption',passed=not all(segment_checks(z,a).values())))
        z,a=copy.deepcopy(padding);z[4]=math.nextafter(z[3],math.inf)
        mutations.append(dict(name='one_ULP_padding',passed=not all(segment_checks(z,a).values())))
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):
        check('snapshot',rec['path'],sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    receipts=[json.loads(x.read_text(encoding='utf-8-sig')) for x in folder.glob('execution_*.json')]
    check('execution','successful_receipt',any(x['exit_code']==0 for x in receipts))
    out=dict(version='0.55',timestamp_utc=datetime.now(timezone.utc).isoformat(),scope='EXACT_BINARY_INSTANTANEOUS_CERTIFICATE_AND_TWO_HELD_SAVED_V52_CONTROLS',
             passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks),
             vectors=len(vectors),resolved_accepted=len(accepted),unresolved_rejected=len(unresolved),
             legacy_branch_defects=legacy_wrong,exact_witness_gap_fraction=str(kgap),exact_witness_gap_K=float(kgap),
             actual_intervals=2,actual_positive_segments=segments,actual_modes=[2],
             reviewer_selfchecks_passed=sum(x['passed'] for x in mutations),reviewer_selfchecks_failed=sum(not x['passed'] for x in mutations),
             checks=checks,reviewer_selfchecks=mutations)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');path=folder/f'independent_QA_v55_{stamp}.json'
    path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['checks','legacy_branch_defects','reviewer_selfchecks']}));print(path.relative_to(ROOT).as_posix())
    if out['failed'] or out['reviewer_selfchecks_failed']:
        print(json.dumps([x for x in checks if not x['passed']][:20],indent=2));sys.exit(1)
if __name__=='__main__': main()
