"""Independent exact-Fraction guards, Decimal log event times and analytic QA.
No production imports. Original-MAT binary64 exports are authoritative.
Same agent, independent algorithms; synthetic reviewer mutations are separate.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import json, struct, hashlib, sys, math, csv, copy
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(x):
    if isinstance(x,D):return x
    if isinstance(x,F):return D(x.numerator)/D(x.denominator)
    return D.from_float(x)
def coefficients(s,p,request,branch,j):
    s={n:F(x) for n,x in s.items()};p={n:F(x) for n,x in p.items()}
    C=p['heat_capacity_MWh_per_K'];Ta=p['ambient_C'];d=s['charge_approach_K']
    floor=s['delivery_C']+s['direct_approach_K'];Te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K']
    a=s['cooling_factor']*(Te+F(273.15));S=s['source_capacity_MW_per_K']*s['source_glide_K'];H=s['hot_capacity_MW_per_K']
    al=[F(0)]*5;be=[F(request),s['hp_capacity_MW'],F(0),F(0),p['charge_limit_MW']]
    if branch=='TANK':
        l0=Ta+d+s['condenser_approach_K']-Te;l1=1/C;be[2]=H*d;al[3]=S/(a*C);be[3]=S*(1+l0/a)
    else:
        l0=floor+s['condenser_approach_K']-Te;l1=F(0);al[2]=-H/C;be[2]=H*(floor-Ta);be[3]=S*(1+l0/a)
    A=al[j];beta=be[j];k=p['eta_charge']*A-p['loss_rate_per_h'];B=p['eta_charge']*beta
    ga=[F(1),F(-1),1/C,A];gb=[F(0),C*(s['tank_max_C']-Ta),Ta+d-floor,beta]
    if branch=='FLOOR':ga[2]=-ga[2];gb[2]=-gb[2]
    labels=['ZERO','CAPACITY','BRANCH','HEAT_ZERO'];names=['REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT']
    for n in range(5):
        if n!=j:ga.append(al[n]-A);gb.append(be[n]-beta);labels.append('LIMIT_'+names[n])
    return dict(s=s,p=p,al=al,be=be,A=A,beta=beta,k=k,B=B,l0=l0,l1=l1,a=a,S=S,ga=ga,gb=gb,labels=labels)
def energy(c,E,t):
    e=dec(E);t=dec(t);k=dec(c['k']);v=dec(c['k']*F(E)+c['B'])
    return e+v*t if not c['k'] else e+v*((k*t).exp()-1)/k
def roots(c,E):
    result=[];v=c['k']*F(E)+c['B']
    for a,b in zip(c['ga'],c['gb']):
        t=None
        if a and v:
            target=-b/a
            if not c['k']:candidate=dec((target-F(E))/v)
            else:
                ratio=(c['k']*target+c['B'])/v
                candidate=dec(ratio).ln()/dec(c['k']) if ratio>0 else None
            if candidate is not None and candidate>0:t=candidate
        result.append(t)
    return result
def contains(iv,v):return dec(iv[0])<=dec(v)<=dec(iv[1])
def flat(v):
    if isinstance(v,list):return [x for item in v for x in flat(item)]
    return [float(v)]
def valid_protocol(item):
    z=item['event']
    return not z['event_transition_authorized'] and not z['memory_handoff_authorized'] and 0<=item['integrated_span_h']<=z['safe_prefix_h'] and item['integrated_prefix']['span_h']==item['integrated_span_h']
def prefix_ports(c,E,t,j,branch):
    e=dec(E);t=dec(t);k=dec(c['k']);B=dec(c['B']);v=dec(c['k']*F(E)+c['B'])
    en=energy(c,E,t)
    integ=e*t+v*t*t/2 if not c['k'] else e*t+v*((k*t).exp()-1-k*t)/(k*k)
    A,beta,l0,l1,a=[dec(c[n]) for n in ['A','beta','l0','l1','a']]
    heat=A*integ+beta*t
    if j==3:source=dec(c['S'])*t
    elif branch=='FLOOR':source=heat*a/(l0+a)
    else:
        y0=l0+a+l1*e;y1=l0+a+l1*en;cc=c['l1']*c['B']-c['k']*(c['l0']+c['a'])
        if c['k']*F(E)+c['B']==0:J=t/y0
        elif cc==0:J=(1-(-k*t).exp())/(k*y0)
        else:J=((y1/y0).ln()-k*t)/dec(cc)
        source=beta*a*J
    work=heat-source;standing=dec(c['p']['loss_rate_per_h'])*integ;loss=(1-dec(c['p']['eta_charge']))*heat
    return dict(end_energy_MWh_interval=en,integral_energy_MWh_h_interval=integ,heat_MWh_interval=heat,
        source_MWh_interval=source,compressor_MWh_interval=work,standing_loss_MWh_interval=standing,
        charge_loss_MWh_interval=loss,aux_rejected_MWh_interval=dec(c['s']['aux_per_compressor'])*work,
        first_law_MWh_interval=e+heat-en-standing-loss)
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());manifest=json.loads((folder/'binary_manifest.json').read_text())
    checks=[];selfchecks=[];data={};hashes=[];traces=[];regimes=set();statuses={};crossings={};samples=0
    byid={v['id']:v for v in report['runs']}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopen',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MATLAB','assertions',report['summary']['failed']==0 and all(v['passed'] for v in report['assertions']))
    check('scope','no_coupled_acceptance',not report['new_model'] and not report['coupled_stateflow_acceptance'])
    for rec in manifest['records']:
        path=(folder/rec['file']).resolve();assert path.is_relative_to(folder/'binary')
        vals=[x[0] for x in struct.iter_unpack('<d',path.read_bytes())];samples+=len(vals)
        key=(rec['id'],rec['group'],rec['field']);check('binary','unique_'+str(key),key not in data)
        check('binary','shape_'+str(key),len(vals)==rec['rows']*rec['columns']);data[key]=vals
        hashes.append(dict(path=rec['file'],sha256=sha(path)))
        if rec['id']=='blocker':want=report['blocker'][rec['field']]
        else:
            item=byid[rec['id']];group=rec['group'];field=rec['field']
            if group=='input':want=[item['input']['E'],item['horizon_h'],item['input']['request'],item['integrated_span_h']]
            elif group in ['s','p']:want=item['input'][group][field]
            else:want=item[group][field]
        check('original_binary_binding',str(key),vals==flat(want))
    with localcontext() as ctx:
        ctx.prec=120
        for item in report['runs']:
            id=item['id'];raw=lambda group,field:data[(id,group,field)]
            E,horizon,request,t=raw('input','E_horizon_request_span')
            s={n:raw('s',n)[0] for n in item['input']['s']};p={n:raw('p',n)[0] for n in item['input']['p']}
            z=item['event'];branch=z['branch'];j=int(raw('event','limiter_index')[0])-1;c=coefficients(s,p,request,branch,j)
            regimes.add((branch,j));statuses[z['status']]=statuses.get(z['status'],0)+1
            rt=roots(c,E);prefix=raw('event','safe_prefix_h')[0];en=energy(c,E,prefix)
            check('analytic_energy',id+'_prefix',contains(raw('event','safe_prefix_energy_MWh_interval'),en))
            check('analytic_energy',id+'_continuation',contains(raw('event','continuation_energy_at_horizon_MWh_interval'),energy(c,E,horizon)))
            check('guard_labels',id,z['guard_labels']==c['labels'])
            check('arithmetic_domain',id,abs(dec(c['k'])*dec(horizon))<=1)
            check('no_authorization',id,raw('event','event_transition_authorized')==[0.] and raw('event','memory_handoff_authorized')==[0.])
            check('handoff_protocol',id,valid_protocol(item))
            for name in ['k','B']:
                check('coefficient',id+name,contains(raw('event',name+'_interval'),c[name]))
            for n,label in enumerate(c['labels']):
                check('coefficient',id+label+'A',contains(raw('event','guard_alpha_interval')[2*n:2*n+2],c['ga'][n]))
                check('coefficient',id+label+'B',contains(raw('event','guard_beta_interval')[2*n:2*n+2],c['gb'][n]))
                for field,tm in [('initial_guard_intervals',0.),('horizon_guard_intervals',horizon),('safe_prefix_guard_intervals',prefix)]:
                    val=dec(c['ga'][n])*energy(c,E,tm)+dec(c['gb'][n]);iv=raw('event',field)[2*n:2*n+2]
                    check('guard_enclosure',id+label+field,contains(iv,val))
                    if field!='horizon_guard_intervals':check('strict_prefix',id+label+field,val>0 and iv[0]>0)
                lo,hi=raw('event','guard_time_windows_h')[2*n:2*n+2];exists=bool(raw('event','guard_has_candidate')[n]);cert=bool(raw('event','upper_crossing_certified')[n]);root=rt[n]
                for index,tm in [(0,lo),(2,hi)]:
                    ep=raw('event','guard_endpoint_intervals')[4*n+index:4*n+index+2]
                    check('bracket_guard',id+label+str(index),contains(ep,dec(c['ga'][n])*energy(c,E,tm)+dec(c['gb'][n])))
                if exists:
                    check('safe_window_lower',id+label,root is None or root>=dec(lo))
                    if cert:
                        check('event_root_isolation',id+label,root is not None and dec(lo)<=root<=dec(hi)<=dec(horizon))
                        check('event_upper_negative',id+label,raw('event','guard_endpoint_intervals')[4*n+3]<0)
                        crossings[label]=crossings.get(label,0)+1
                else:check('no_event_guard',id+label,root is None or root>dec(horizon))
                traces.append(dict(id=id,guard=label,exact_event_h=str(root),window_lower_h=lo,window_upper_h=hi,upper_certified=cert))
            actual=[v for v in rt if v is not None and v<=dec(horizon)]
            first=raw('event','first_event_window_h')
            if actual:
                check('first_event',id,contains(first,min(actual)) and z['status']!='CERTIFIED_NO_EVENT')
            if z['status']=='CERTIFIED_NO_EVENT':check('no_event',id,not actual and prefix==horizon)
            if z['crossing_isolated']:check('isolated_exist',id,bool(actual) and dec(first[0])<=min(actual)<=dec(first[1]))
            expect=prefix_ports(c,E,t,j,branch)
            for field,val in expect.items():check('prefix_energy_ports',id+field,contains(raw('integrated_prefix',field),val))
            with localcontext() as more:
                more.prec=160;again=roots(c,E);again_ports=prefix_ports(c,E,t,j,branch)
                for n,val in enumerate(rt):
                    if val is not None:check('precision_stability',id+str(n),abs(val-again[n])<D('1e-100')*max(D(1),abs(val)))
                for field,val in expect.items():check('precision_stability',id+field,abs(val-again_ports[field])<D('1e-100')*max(D(1),abs(val)))
            if id.startswith('stationary_exact'):check('stationary',id,c['k']*F(E)+c['B']==0 and not actual and z['status']=='CERTIFIED_NO_EVENT')
    check('coverage','ten_regimes',len(regimes)==10)
    for label in ['BRANCH','CAPACITY','LIMIT_HOT_FLOW','LIMIT_REQUEST']:
        check('event_coverage',label,crossings.get(label,0)>0)
    both=[v for v in report['runs'] if v['id'].startswith('simultaneous_branch_hot') and v['event']['crossing_isolated']]
    check('simultaneous','not_arbitrarily_ordered',bool(both) and all(not v['event']['unique_first_guard'] and set(v['event']['candidate_labels'])=={'BRANCH','LIMIT_HOT_FLOW'} for v in both))
    b=report['blocker'];s={n:F(x) for n,x in b['input']['s'].items()};p={n:F(x) for n,x in b['input']['p'].items()}
    target=p['heat_capacity_MWh_per_K']*(s['delivery_C']+s['direct_approach_K']-p['ambient_C']-s['charge_approach_K'])
    left,right=data[('blocker','witness','adjacent_energy_MWh')]
    check('blocking_defect','adjacent_binary_values',math.nextafter(left,math.inf)==right)
    check('blocking_defect','no_exact_binary64_endpoint',F(left)<target<F(right))
    check('blocking_defect','scalar_API_rejections',all(b['rejection_identifiers']))
    resolved=F(data[('blocker','witness','resolved_tank_energy_MWh')][0])
    check('blocking_defect','resolved_tank_branch',resolved>target)
    check('blocking_defect','persistent_exact_equivalent_limits',F(b['input']['request'])==s['hot_capacity_MW_per_K']*s['charge_approach_K'])
    check('blocking_defect','actual_persistent_tie_rejection',b['persistent_tie_identifier']=='DCHR:v56:UnresolvedLimiter')
    # Synthetic corruption probes test reviewer sensitivity; not plant tests.
    fixture=next(v for v in report['runs'] if v['event']['crossing_isolated'] and v['event']['unique_first_guard'])
    z=fixture['event'];c=coefficients(fixture['input']['s'],fixture['input']['p'],fixture['input']['request'],z['branch'],z['limiter_index']-1)
    with localcontext() as ctx:
        ctx.prec=120;true=min(v for v in roots(c,fixture['input']['E']) if v is not None)
        selfchecks.append(dict(name='event_window_shift',passed=not contains([float(true)+.01,float(true)+.02],true)))
        selfchecks.append(dict(name='energy_interval_shift',passed=not contains([100.,101.],energy(c,fixture['input']['E'],z['safe_prefix_h']))))
        bad=copy.deepcopy(fixture);bad['event']['memory_handoff_authorized']=True
        selfchecks.append(dict(name='memory_authorization',passed=not valid_protocol(bad)))
        selfchecks.append(dict(name='endpoint_snap',passed=not (F(left)==target)))
        bad=copy.deepcopy(fixture);bad['integrated_span_h']=bad['horizon_h'];bad['integrated_prefix']['span_h']=bad['horizon_h']
        selfchecks.append(dict(name='post_event_port_credit',passed=not valid_protocol(bad)))
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):check('source',rec['path'],sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    check('execution','success_receipt',any(json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0 for p in folder.glob('execution_*.json')))
    check('MAT','original_file',(folder/'charge_events_v59.mat').stat().st_size>1000)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    result=dict(version='0.59',timestamp_utc=datetime.now(timezone.utc).isoformat(),scope='EVENT_ISOLATION_ONLY_CORRELATED_STATEFLOW_HANDOFF_BLOCKED',
        summary=dict(passed=sum(v['passed'] for v in checks),failed=sum(not v['passed'] for v in checks)),
        reviewer_selfchecks=dict(passed=sum(v['passed'] for v in selfchecks),failed=sum(not v['passed'] for v in selfchecks)),
        cases=len(report['runs']),regimes=len(regimes),binary_values=samples,status_counts=statuses,certified_crossing_counts=crossings,
        exact_branch_endpoint_MWh=str(target),adjacent_binary64_energy_MWh=[left,right],checks=checks,mutations=selfchecks,binary_hashes=hashes)
    out=folder/f'independent_QA_v59_{stamp}.json';out.write_text(json.dumps(result,indent=2)+'\n')
    with (folder/f'event_traces_v59_{stamp}.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(traces[0]));writer.writeheader();writer.writerows(traces)
    print(json.dumps({k:v for k,v in result.items() if k not in ['checks','mutations','binary_hashes']}))
    if result['summary']['failed'] or result['reviewer_selfchecks']['failed']:sys.exit(1)
if __name__=='__main__':main()
