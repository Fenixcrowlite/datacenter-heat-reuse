"""Independent exact binary algebra, 80-digit event/ODE QA and original MAT binding.
No production MATLAB functions are imported. Same-agent, separate algorithms.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import Decimal as D, localcontext
import json, sys, hashlib, math, copy
ROOT=Path(__file__).resolve().parents[1]
NAMES=['REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT']
def f(x):return F.from_float(float(x))
def dec(x):return D(x.numerator)/D(x.denominator) if isinstance(x,F) else D.from_float(float(x))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(x):return x if isinstance(x,list) else [x]
def close(x,y,tol=2e-12):return abs(dec(x)-dec(y))<=dec(tol)*max(D(1),abs(dec(y)))
def equations(v):
    s={k:f(x) for k,x in v['s'].items()};p={k:f(x) for k,x in v['p'].items()};E=f(v['E'])
    C=p['heat_capacity_MWh_per_K'];Ta=p['ambient_C'];T=Ta+E/C
    floor=s['delivery_C']+s['direct_approach_K'];charge=s['charge_approach_K']
    branch='TANK' if T+charge>floor else 'FLOOR'
    te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K']
    a=s['cooling_factor']*(te+f(273.15));S=s['source_capacity_MW_per_K']*s['source_glide_K'];H=s['hot_capacity_MW_per_K']
    slopes=[F(0)]*5
    if branch=='TANK':
        slopes[3]=S/(a*C)
        intercept=[f(v['request']),s['hp_capacity_MW'],H*charge,S*(1+(Ta+charge+s['condenser_approach_K']-te)/a),p['charge_limit_MW']]
    else:
        slopes[2]=-H/C
        intercept=[f(v['request']),s['hp_capacity_MW'],H*(floor-Ta),S*(1+(floor+s['condenser_approach_K']-te)/a),p['charge_limit_MW']]
    limits=[m*E+b for m,b in zip(slopes,intercept)];idx=min(range(5),key=lambda j:limits[j])
    k=p['eta_charge']*slopes[idx]-p['loss_rate_per_h'];B=p['eta_charge']*intercept[idx];v0=k*E+B
    kink=C*(floor-Ta-charge);cap=C*(s['tank_max_C']-Ta)
    targets=[('ZERO',F(0)),('CAPACITY',cap),('BRANCH',kink)]
    for j in range(5):
        if j!=idx and slopes[idx]!=slopes[j]:targets.append(('LIMIT_'+NAMES[j],(intercept[j]-intercept[idx])/(slopes[idx]-slopes[j])))
    events={}
    for label,et in targets:
        if et<0 or et>cap or v0==0 or (et-E)*v0<=0:continue
        if branch=='TANK' and et<kink or branch=='FLOOR' and et>kink:continue
        if (k*et+B)*v0<=0:continue
        t=dec(et-E)/dec(v0) if k==0 else (1+dec(k*(et-E)/v0)).ln()/dec(k)
        events[label]=(et,t)
    return dict(branch=branch,slopes=slopes,intercept=intercept,limits=limits,idx=idx,k=k,B=B,v0=v0,kink=kink,cap=cap,events=events,s=s,p=p,E=E,te=te,a=a,S=S,H=H,floor=floor)

def checks_case(item):
    v=item['input'];r=item['descriptor'];o=equations(v);idx=o['idx'];result={}
    result['branch']=r['branch']==o['branch'];result['limiter']=r['limiter_index']==idx+1 and r['limiter']==NAMES[idx]
    for j in range(5):
        result[f'slope_{j}']=close(r['slope_per_h'][j],o['slopes'][j])
        result[f'intercept_{j}']=close(r['intercept_MW'][j],o['intercept'][j])
        iv=r['limit_MW_intervals'][j]
        result[f'limit_enclosure_{j}']=f(iv[0])<=o['limits'][j]<=f(iv[1])
    result['strict_unique_sound']=all(o['limits'][idx]<o['limits'][j] for j in range(5) if j!=idx)
    result['strict_policy']=r['limit_MW_intervals'][idx][1]<min(r['limit_MW_intervals'][j][0] for j in range(5) if j!=idx)
    for key,out in [('k','k_per_h'),('B','B_MW'),('v0','initial_velocity_MW'),('kink','branch_energy_MWh'),('cap','capacity_energy_MWh')]:result[key]=close(r[out],o[key])
    actual={e['label']:e for e in arr(r['events'])}
    result['event_complete']=set(actual)==set(o['events'])
    for label,(E,t) in o['events'].items():
        got=actual.get(label)
        result[label+'_energy']=got is not None and close(got['energy_MWh'],E)
        result[label+'_time']=got is not None and close(got['time_h'],t,5e-11)
        if got:
            gd=dec(got['time_h']);k=dec(o['k']);B=dec(o['B']);E0=dec(o['E'])
            endpoint=E0+B*gd if k==0 else E0*(k*gd).exp()+B*((k*gd).exp()-1)/k
            result[label+'_endpoint']=close(endpoint,E,1e-10)
    if o['events']:
        soon=min(t for E,t in o['events'].values());labels={label for label,(E,t) in o['events'].items() if t==soon}
        result['earliest_time']=r['next_event_h'] is not None and close(r['next_event_h'],soon,5e-11)
        result['earliest_labels']=set(r['first_event_labels'])==labels
        dt=min(float(soon)/5,.02)
    else:
        result['no_finite_event']=r['next_event_h'] is None and r['first_event_labels']==[];dt=.02
    # Separate RK4 on the full instantaneous min-envelope, not affine production code.
    def velocity(E):
        s=o['s'];p=o['p'];T=dec(p['ambient_C'])+E/dec(p['heat_capacity_MWh_per_K'])
        hot=max(T+dec(s['charge_approach_K']),dec(o['floor']))
        lift=hot+dec(s['condenser_approach_K'])-dec(o['te'])
        q=min(dec(v['request']),dec(s['hp_capacity_MW']),dec(o['H'])*(hot-T),dec(o['S'])*(1+lift/dec(o['a'])),dec(p['charge_limit_MW']))
        return dec(p['eta_charge'])*q-dec(p['loss_rate_per_h'])*E
    h=dec(dt)/128;E=dec(o['E'])
    for _ in range(128):
        a1=velocity(E);a2=velocity(E+h*a1/2);a3=velocity(E+h*a2/2);a4=velocity(E+h*a3)
        E+=h*(a1+2*a2+2*a3+a4)/6
    kd=dec(o['k']);Bd=dec(o['B']);td=dec(dt);E0=dec(o['E'])
    analytic=E0+Bd*td if kd==0 else E0*(kd*td).exp()+Bd*((kd*td).exp()-1)/kd
    result['independent_min_envelope_RK4']=close(E,analytic,2e-11)
    result['explicit_uncertified']=r['event_times_certified'] is False and 'NO_PROPAGATOR' in r['scope']
    return result

def checks_segment(z,c,q):
    span=f(z[1]);E=f(z[3]);end=f(z[4]);p=list(map(f,c['p']));x=list(map(f,c['inputs']))
    if span==0:return dict(padding_identity=E==end and z[0]==0 and all(y==0 for y in z[5:14]+z[16:21]),canonical=z[4]==q[22])
    qc=f(z[6]);qd=f(z[7]);P=p[4]*qc-qd/p[5]
    # All six retained fixed-input controls have zero loss and no event.
    expected=E+span*P
    supply=f(z[5])+qd+f(z[8]);res=(f(z[11])+f(z[12])+f(z[8]))*span+E-supply*span-end-f(z[16])-f(z[17])-f(z[18])
    need=x[3]-f(z[5])-qd
    return dict(ODE=close(z[4],expected,2e-12),closure=close(res,F(0),2e-12),
        demand=close(f(z[5])+qd+f(z[8])+f(z[9]),x[3]),
        boiler=f(z[8])==min(p[10],max(F(0),need)),unmet=f(z[9])==max(F(0),need-f(z[8])),
        ports=close(f(z[10]),f(z[11])+f(z[12])) and f(z[12])<=x[0],
        SOC=0<=E<=p[1] and 0<=end<=p[1],flow_bounds=all(y>=0 for y in z[5:14]) and qc<=p[2] and qd<=p[3],
        efficiency=close(z[17],(1-p[4])*qc*span) and close(z[18],(1/p[5]-1)*qd*span),
        COP=z[10]==0 or close(z[11],f(z[10])/4),canonical=z[4]==q[22],
        mode=int(z[0])==c['expected_mode'])

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    r=json.loads((folder/'report.json').read_text());checks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','report_binding',r==json.loads((folder/'mat_reopen.json').read_text()))
    check('MATLAB','assertions_pass',r['summary']['failed']==0 and all(x['passed'] for x in r['assertions']))
    spec=json.loads((folder/'spec.json').read_text())
    check('INPUT','spec_binding',[x['input'] for x in r['cases']]==spec['cases'])
    coverage=set();events=set();directions=set();signs=set();accepted=[]
    with localcontext() as ctx:
        ctx.prec=80
        for item in r['cases']:
            v=item['input'];check('DOMAIN',v['id'],item['accepted']==(v['expected']=='ACCEPT'))
            if not item['accepted']:continue
            accepted.append(item);rr=item['descriptor'];coverage.add((rr['branch'],rr['limiter']));events.update(e['label'] for e in arr(rr['events']))
            directions.add((rr['initial_velocity_MW']>0)-(rr['initial_velocity_MW']<0));signs.add((rr['k_per_h']>0)-(rr['k_per_h']<0))
            for name,ok in checks_case(item).items():check('EQUATION',v['id']+'_'+name,ok)
        check('COVERAGE','ten_regimes',coverage=={(b,n) for b in ['FLOOR','TANK'] for n in NAMES})
        check('COVERAGE','both_motion_directions_and_stationary',directions=={-1,0,1})
        check('COVERAGE','all_k_signs',signs=={-1,0,1})
        check('COVERAGE','limiter_branch_capacity_events',{'BRANCH','CAPACITY','LIMIT_HOT_FLOW','LIMIT_REQUEST'}<=events)
        originals=json.loads((folder/'original_simulation_reopen.json').read_text())
        check('MAT','original_simulation_binding',r['runs']==originals)
        for mode,run in enumerate(r['runs']):
            c=dict(run['case'],expected_mode=mode);z=run['raw_segments'];q=run['raw_plans'];d=run['dispatch']
            check('STATEFLOW',run['id']+'_mode',d[0]==mode)
            check('STATEFLOW',run['id']+'_handoff',all(z[j][4]==z[j+1][3] for j in range(63)))
            check('STATEFLOW',run['id']+'_terminal',d[7]==z[-1][4])
            shared=list(range(21))+list(range(22,25));ref=run['reference']
            check('REFERENCE',run['id'],all((d[j] is None and ref[j] is None) or (d[j] is not None and ref[j] is not None and close(d[j],f(ref[j]),1e-9)) for j in shared))
            for j,segment in enumerate(z):
                for name,ok in checks_segment(segment,c,q[j]).items():check('STATEFLOW',run['id']+f'_{j}_'+name,ok)
        check('STATEFLOW','negative_source_actual_rejection','Runtime physical-domain rejection' in r['runtime_fault_message'])
        check('STATEFLOW','observed_charts_and_license',r['metadata']['chart_count']==2 and r['metadata']['stateflow_license_test']==1)
        temporal_path=folder/'temporal_report.json'
        if temporal_path.exists():
            temporal=json.loads(temporal_path.read_text());run=temporal['run'];c=run['case'];dispatch=run['dispatch']
            check('TEMPORAL','MAT_original_binding',run==json.loads((folder/'temporal_original_reopen.json').read_text()))
            check('TEMPORAL','MATLAB_assertions',temporal['summary']['failed']==0 and all(x['passed'] for x in temporal['assertions']))
            check('TEMPORAL','mode_transitions',sum(a[0]!=b[0] for a,b in zip(dispatch,dispatch[1:]))>=4)
            check('TEMPORAL','macro_handoff',all(run['energy_start'][j]==dispatch[j-1][7] for j in range(1,7)))
            blocker=run['blocker'];o=equations(blocker['input'])
            exact_gap=f(blocker['input']['p']['ambient_C'])+f(blocker['nominal_endpoint_MWh'])/f(blocker['input']['p']['heat_capacity_MWh_per_K'])+f(blocker['input']['s']['charge_approach_K'])-f(blocker['input']['s']['delivery_C'])-f(blocker['input']['s']['direct_approach_K'])
            check('BLOCKER','exact_binary_witness',exact_gap==F(-5,3602879701896397))
            check('BLOCKER','endpoint_rejection',blocker['endpoint_identifier']=='DCHR:v55:UnresolvedBranch' and blocker['coupled_release_blocked'])
            check('BLOCKER','nominal_kink_not_exact',f(blocker['nominal_endpoint_MWh'])!=o['kink'])
            seen=set();positive_count=0
            for j in range(7):
                z=[run['raw_segments'][j][n:n+28] for n in range(0,1792,28)]
                q=[run['raw_plans'][j][n:n+23] for n in range(0,1472,23)]
                check('TEMPORAL',f'{j}_handoff',all(a[4]==b[3] for a,b in zip(z,z[1:])))
                check('TEMPORAL',f'{j}_terminal',dispatch[j][7]==z[-1][4])
                energy=[D(0)]*9;loss=[D(0)]*3
                for slot,(segment,plan) in enumerate(zip(z,q)):
                    cc=dict(c,inputs=c['inputs'][j],expected_mode=int(segment[0]))
                    for name,ok in checks_segment(segment,cc,plan).items():check('TEMPORAL',f'{j}_{slot}_{name}',ok)
                    if segment[1]>0:
                        seen.add(int(segment[0]));positive_count+=1
                        span=dec(segment[1]);mode=next((n for n,index in [(5,9),(4,8),(3,7),(2,6),(1,5)] if segment[index]>0),0)
                        check('TEMPORAL',f'{j}_{slot}_mode_from_actual_flows',segment[0]==mode)
                        check('TEMPORAL',f'{j}_{slot}_cutoff',segment[7]==0 or min(segment[3:5])>=c['p'][7]-1e-12)
                        check('TEMPORAL',f'{j}_{slot}_clock',close(segment[27],f(segment[26])+f(segment[1])) and segment[25]==plan[14])
                        for index in range(9):energy[index]+=dec(segment[index+5])*span
                        for index in range(3):loss[index]+=dec(segment[index+16])
                summary_port_columns=[1,2,3,4,5,18,19,20,21]
                for index,val in enumerate(energy):check('TEMPORAL',f'{j}_integrated_port_{index}',close(dispatch[j][summary_port_columns[index]],val/dec(c['p'][0])))
                # Summary loss columns 9..11 are interval energies, not powers.
                for index,val in enumerate(loss):check('TEMPORAL',f'{j}_integrated_loss_{index}',close(dispatch[j][index+8],val))
            check('TEMPORAL','five_sequence_modes',seen=={0,2,3,4,5})
            temporal_counts=dict(intervals=7,positive_segments=positive_count,macro_transitions=sum(a[0]!=b[0] for a,b in zip(dispatch,dispatch[1:])))
        else:temporal_counts=None
        # Separate synthetic reviewer mutations; never count as actual execution.
        selfchecks=[]
        for field in ['k_per_h','B_MW','branch_energy_MWh']:
            mutant=copy.deepcopy(accepted[0]);mutant['descriptor'][field]+=1
            selfchecks.append(dict(name=field+'_mutation',passed=not all(checks_case(mutant).values())))
        mutant=copy.deepcopy(accepted[0]);mutant['descriptor']['event_times_certified']=True
        selfchecks.append(dict(name='false_certificate_mutation',passed=not all(checks_case(mutant).values())))
        event_case=next(x for x in accepted if x['descriptor']['events'])
        mutant=copy.deepcopy(event_case);arr(mutant['descriptor']['events'])[0]['time_h']*=2
        selfchecks.append(dict(name='event_time_mutation',passed=not all(checks_case(mutant).values())))
    for manifest in ['preservation.json','source_hashes.json']:
        for item in json.loads((folder/manifest).read_text()):
            check('PRESERVATION',item['path'],sha(ROOT/item['path'])==item['sha256'])
            if manifest=='source_hashes.json':check('SNAPSHOT',item['path'],sha(folder/'source_snapshot'/item['path'])==item['sha256'])
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out=dict(version='0.56',timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
        summary=dict(passed=sum(x['passed'] for x in checks),failed=sum(not x['passed'] for x in checks)),
        reviewer_selfchecks=selfchecks,regime_coverage=sorted([list(x) for x in coverage]),event_labels=sorted(events),
        charge_cases_accepted=len(accepted),charge_cases_rejected=len(r['cases'])-len(accepted),
        temporal_counts=temporal_counts,
        limitations=['Nominal event times only; no propagated endpoint enclosure or variable-power integral acceptance.','Independent algorithms by the same agent; no independent personnel or calibrated physical validation.'])
    path=folder/f'independent_QA_v56_{stamp}.json';path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(path=path.relative_to(ROOT).as_posix(),summary=out['summary'],reviewer_selfchecks=selfchecks)))
    failures=[x for x in checks if not x['passed']]
    if failures:print(json.dumps(failures[:30],indent=2))
    if failures or not all(x['passed'] for x in selfchecks):raise SystemExit(1)
if __name__=='__main__':main()
