"""Independent Fraction manifolds, 120/160-digit roots and port integrals.
No production imports. Same-agent algorithmic QA, not personnel/physical QA.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import json, struct, hashlib, sys, copy, csv, math
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dec(x):
    if isinstance(x,D):return x
    if isinstance(x,F):return D(x.numerator)/D(x.denominator)
    return D.from_float(x)
def rational(x):return F(int(x['numerator']),int(x['denominator']))
def contains(iv,x):return dec(iv[0])<=dec(x)<=dec(iv[1])
def flat(x):return [v for y in x for v in flat(y)] if isinstance(x,list) else [float(x)]
def exact(c,total):
    s={n:F(x) for n,x in c['s'].items()};p={n:F(x) for n,x in c['p'].items()}
    C=p['heat_capacity_MWh_per_K'];Ta=p['ambient_C'];floor=s['delivery_C']+s['direct_approach_K'];approach=s['charge_approach_K']
    star=C*(floor-Ta-approach);cap=C*(s['tank_max_C']-Ta);E=F(c['E']);q=F(c['request']);lam=p['loss_rate_per_h'];B=p['eta_charge']*q
    Te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K'];a=s['cooling_factor']*(Te+F(273.15));S=s['source_capacity_MW_per_K']*s['source_glide_K']
    lf=floor+s['condenser_approach_K']-Te;l0=Ta+approach+s['condenser_approach_K']-Te;l1=1/C
    T=dec(total);k=-dec(lam);bb=dec(B);e=dec(E);st=dec(star)
    if not lam:
        t=dec((star-E)/B);end=e+bb*T;integral=e*T+bb*T*T/2
    else:
        t=-dec((B-lam*star)/(B-lam*E)).ln()/dec(lam);eq=bb/dec(lam);r=(k*T).exp()
        end=eq+(e-eq)*r;integral=eq*T+(e-eq)*(1-r)/dec(lam)
    dt=T-t;y0=dec(a+l0+l1*star);y1=dec(a+l0)+dec(l1)*end;cc=dec(l1*B+lam*(a+l0))
    assert cc>0
    J=((y1/y0).ln()-k*dt)/cc
    srcin=dec(q*a/(a+lf))*t;srcout=dec(q*a)*J;heat=dec(q)*T;source=srcin+srcout;work=heat-source
    standing=dec(lam)*integral;loss=dec((1-p['eta_charge'])*q)*T;aux=dec(s['aux_per_compressor'])*work
    values=dict(event_time_h_interval=t,event_energy_MWh_interval=st,post_event_duration_h_interval=dt,end_energy_MWh_interval=end,
        incoming_heat_MWh_interval=dec(q)*t,outgoing_heat_MWh_interval=dec(q)*dt,
        incoming_source_MWh_interval=srcin,outgoing_source_MWh_interval=srcout,heat_MWh_interval=heat,source_MWh_interval=source,
        compressor_MWh_interval=work,standing_loss_MWh_interval=standing,charge_loss_MWh_interval=loss,aux_rejected_MWh_interval=aux,
        first_law_MWh_interval=e+heat-end-standing-loss)
    exacts=dict(exact_branch_energy_MWh=star,exact_capacity_MWh=cap,exact_right_heat_MW=q,exact_event_velocity_MW=B-lam*star,
        exact_cooling_coefficient=a,exact_source_budget_MW=S,exact_floor_lift_K=lf,exact_right_lift0_K=l0,exact_right_lift1_per_h=l1)
    limits=[q,s['hp_capacity_MW'],s['hot_capacity_MW_per_K']*approach,S*(1+lf/a),p['charge_limit_MW']]
    names=['REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'];ties=[n for n,v in zip(names,limits) if v==q]
    return values,exacts,ties
def validation(c,total,z):
    vals,exacts,ties=exact(c,total);result={}
    for n,v in vals.items():result['analytic_'+n]=contains(z[n],v)
    for n,v in exacts.items():result['rational_'+n]=rational(z[n])==v
    got=z['right_equivalent_limiters'];got=[got] if isinstance(got,str) else got
    result['exact_persistent_tie_set']=got==ties
    result['right_branch']=z['right_branch']=='TANK' and z['bounded_branch_continuation']
    result['no_scalar_handoff']=not z['scalar_memory_handoff_authorized'] and not z['compiled_stateflow_handoff_authorized']
    result['exact_threshold_bracket']=contains(z['event_energy_MWh_interval'],exacts['exact_branch_energy_MWh'])
    lo,hi=z['event_energy_MWh_interval'];result['tight_threshold_bracket']=lo==hi or math.nextafter(lo,math.inf)==hi
    for index,age in enumerate(c['age']):
        result['event_age_'+str(index)]=contains(z['event_hp_age_h_interval'],dec(age)+vals['event_time_h_interval'])
        result['end_age_'+str(index)]=contains(z['end_hp_age_h_interval'],dec(age)+dec(total))
    result['latch_retained']=z['hp_latch_retained']
    result['manifold_constraint']='same exact E_event' in z['correlation']['outgoing_initial_energy']
    return result
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());manifest=json.loads((folder/'binary_manifest.json').read_text());checks=[];data={};hashes=[];values=0
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_report',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_exists',(folder/manifest['source_mat']).stat().st_size>1000 and manifest['source']=='ORIGINAL_REOPENED_MAT_BINARY64')
    check('MATLAB','assertions',report['summary']['failed']==0 and all(x['passed'] for x in report['assertions']))
    check('scope','no_coupled_model_acceptance',not report['new_model'] and not report['coupled_stateflow_acceptance'])
    byid={r['id']:r for r in report['runs']}
    for rec in manifest['records']:
        path=(folder/rec['file']).resolve();assert path.is_relative_to(folder/'binary')
        raw=[x[0] for x in struct.iter_unpack('<d',path.read_bytes())];values+=len(raw);key=(rec['id'],rec['group'],rec['field'])
        check('binary','unique_'+str(key),key not in data);data[key]=raw
        check('binary','shape_'+str(key),len(raw)==rec['rows']*rec['columns']);hashes.append(dict(path=rec['file'],sha256=sha(path)))
        item=byid[rec['id']];g=rec['group'];f=rec['field']
        want=[item['input']['E'],item['total_h'],item['input']['request'],*item['input']['age']] if g=='input' else item['record'][f] if g=='record' else item['input'][g][f]
        check('original_binary_binding',str(key),raw==flat(want))
    traces=[];tie_counts=set();checks_by_run={}
    with localcontext() as ctx:
        ctx.prec=120
        for item in report['runs']:
            id=item['id'];raw=lambda g,f:data[(id,g,f)];E,T,q,*age=raw('input','E_total_request_age')
            c=dict(E=E,request=q,age=age,s={n:raw('s',n)[0] for n in item['input']['s']},p={n:raw('p',n)[0] for n in item['input']['p']})
            z=copy.deepcopy(item['record'])
            for rec in manifest['records']:
                if rec['id']==id and rec['group']=='record':
                    f=rec['field'];x=raw('record',f);z[f]=x[0] if rec['rows']*rec['columns']==1 else x
            vals,exacts,ties=exact(c,T);tie_counts.add(len(ties));valid=validation(c,T,z);checks_by_run[id]=valid
            for n,ok in valid.items():check('equation_protocol',id+'_'+n,ok)
            check('event_proof',id,z['incoming_event']['crossing_isolated'] and 'BRANCH' in z['incoming_event']['candidate_labels'])
            check('physical_bounds',id,0<exacts['exact_branch_energy_MWh']<exacts['exact_capacity_MWh'] and vals['end_energy_MWh_interval']<dec(exacts['exact_capacity_MWh']) and vals['post_event_duration_h_interval']>0)
            check('port_bounds',id,all(v>=0 for n,v in vals.items() if n!='first_law_MWh_interval'))
            check('continuous_constant_heat',id,exacts['exact_right_heat_MW']==F(q))
            with localcontext() as more:
                more.prec=160;again,_,_=exact(c,T)
                for n,v in vals.items():check('precision_stability',id+n,abs(v-again[n])<D('1e-100')*max(D(1),abs(v)))
            traces.append(dict(id=id,exact_event_h=str(vals['event_time_h_interval']),event_lo_h=z['event_time_h_interval'][0],event_hi_h=z['event_time_h_interval'][1],
                exact_event_MWh=str(exacts['exact_branch_energy_MWh']),exact_end_MWh=str(vals['end_energy_MWh_interval']),end_lo_MWh=z['end_energy_MWh_interval'][0],end_hi_MWh=z['end_energy_MWh_interval'][1],
                source_MWh=str(vals['source_MWh_interval']),compressor_MWh=str(vals['compressor_MWh_interval']),standing_loss_MWh=str(vals['standing_loss_MWh_interval']),ties='|'.join(ties)))
        first=report['runs'][0];c=first['input'];T=first['total_h'];z=first['record'];selfchecks=[]
        mutations=[]
        v=copy.deepcopy(z);v['exact_branch_energy_MWh']['numerator']=str(int(v['exact_branch_energy_MWh']['numerator'])+1);mutations.append(('exact_manifold_one_integer',v))
        v=copy.deepcopy(z);v['right_equivalent_limiters']=['REQUEST'];mutations.append(('missing_persistent_tie',v))
        for label,field in [('inventory','end_energy_MWh_interval'),('source','source_MWh_interval'),('age_reset','end_hp_age_h_interval')]:
            v=copy.deepcopy(z);v[field]=[x+1 for x in v[field]] if label!='age_reset' else [0,0];mutations.append((label,v))
        v=copy.deepcopy(z);v['scalar_memory_handoff_authorized']=True;mutations.append(('scalar_credit_authorization',v))
        for label,v in mutations:selfchecks.append(dict(name=label,passed=not all(validation(c,T,v).values())))
        for probe in report['rational_probes']:check('binary_rational_conversion',repr(probe['value']),rational(probe['rational'])==F(probe['value']))
    check('coverage','unique_and_equivalent_limiter',tie_counts=={1,2});check('coverage','48_actual_runs',len(report['runs'])==48)
    check('domain','eight_rejections',len(report['faults'])==8 and all(x['identifier']==x['expected'] for x in report['faults']))
    for rec in json.loads((folder/'preservation.json').read_text()):check('preservation',rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    for rec in json.loads((folder/'source_hashes.json').read_text()):check('sealed_sources',rec['path'],sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','batch_exit_zero',any(r['exit_code']==0 for r in receipts))
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');csvpath=folder/f'numeric_traces_v61_{stamp}.csv'
    with csvpath.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(traces[0]));w.writeheader();w.writerows(traces)
    result=dict(version='0.61',timestamp_utc=datetime.now(timezone.utc).isoformat(),runs=len(report['runs']),binary_values=values,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),reviewer_selfchecks=selfchecks,
        checks=checks,binary_hashes=hashes,numeric_traces=csvpath.relative_to(folder).as_posix(),
        limitations=['Host-only exact rational contact and constant request branch crossing; no compiled correlated Stateflow memory or physical validation.','Independent algorithms by same agent; synthetic reviewer mutations reported separately.'])
    path=folder/f'independent_QA_v61_{stamp}.json';path.write_text(json.dumps(result,indent=2)+'\n')
    failures=[c for c in checks if not c['passed']];print(json.dumps(dict(summary=result['summary'],reviewer_selfchecks=selfchecks,first_failures=failures[:20]),indent=2))
    assert not failures and all(v['passed'] for v in selfchecks),f'Inspect {path}'
if __name__=='__main__':main()

