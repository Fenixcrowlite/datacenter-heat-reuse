"""Independent Decimal equations, independently programmed RK4, saved-model QA.
No MATLAB production imports; same-agent algorithmic QA, not personnel/physical QA.
"""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D,localcontext
import json,math,hashlib,sys,copy,zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def d(x):return D.from_float(x) if isinstance(x,float) else D(x)
def near(a,b,tol='3e-12'):
    return a is not None and math.isfinite(float(a)) and abs(d(a)-d(b))<=D(tol)*max(D(1),abs(d(b)))
def boundary(s,p,E,request):
    s={k:d(v) for k,v in s.items()};p={k:d(v) for k,v in p.items()}
    T=p['ambient_C']+d(E)/p['heat_capacity_MWh_per_K'];Te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K']
    H=max(T+s['charge_approach_K'],s['delivery_C']+s['direct_approach_K']);Tc=H+s['condenser_approach_K'];g=H-T
    a=s['cooling_factor']*(Te+D('273.15'));lift=Tc-Te;cop=1+a/lift;S=s['source_capacity_MW_per_K']*s['source_glide_K']
    hot=s['hot_capacity_MW_per_K']*g;source=S*(1+lift/a);limits=[d(request),s['hp_capacity_MW'],hot,source];q=min(limits);w=q/cop;ql=q-w
    return dict(tank_C=T,hot_in_C=T,hot_out_C=H,evaporator_C=Te,condenser_C=Tc,hot_glide_K=g,
        cutoff_C=s['delivery_C']+s['discharge_approach_K'],cop_compressor=cop,heating_factor=(lift+a)/(Tc+D('273.15')),
        source_budget_MW=S,hot_budget_MW=hot,source_bound_MW=source,heat_MW=q,compressor_MW=w,source_MW=ql,
        aux_rejected_MW=s['aux_per_compressor']*w,hot_capacity_required_MW_per_K=q/g if g else D(0),
        source_capacity_required_MW_per_K=ql/s['source_glide_K'],limiter=limits.index(q)+1,
        tank_branch=T+s['charge_approach_K']>=s['delivery_C']+s['direct_approach_K'])
def exact(s,p,E,span):
    b=boundary(s,p,E,8);S=b['source_budget_MW'];C=d(p['heat_capacity_MWh_per_K']);a=d(s['cooling_factor'])*(b['evaporator_C']+D('273.15'))
    L=d(p['ambient_C'])+d(s['charge_approach_K'])+d(s['condenser_approach_K'])-b['evaporator_C']
    alpha=S/(a*C);beta=S*(1+L/a);k=d(p['eta_charge'])*alpha-d(p['loss_rate_per_h']);B=d(p['eta_charge'])*beta;t=d(span)
    if k==0:phi=t;psi=t*t/2
    else:phi=((k*t).exp()-1)/k;psi=(phi-t)/k
    end=d(E)*(k*t).exp()+B*phi;integral=d(E)*phi+B*psi;q=alpha*integral+beta*t;w=S/a*(L*t+integral/C)
    return dict(initial_energy_MWh=d(E),end_energy_MWh=end,span_h=t,k_per_h=k,B_MW=B,integral_energy_MWh_h=integral,
        heat_MWh=q,compressor_MWh=w,source_MWh=S*t,aux_rejected_MWh=d(s['aux_per_compressor'])*w,
        standing_loss_MWh=d(p['loss_rate_per_h'])*integral,charge_loss_MWh=(1-d(p['eta_charge']))*q,
        first_law_residual_MWh=d(E)+S*t+w-end-d(p['loss_rate_per_h'])*integral-(1-d(p['eta_charge']))*q)
def rk4(s,p,E,span,n=1024):
    # Re-evaluate min envelopes and COP at each RK stage: no affine constants.
    def rhs(y):
        T=p['ambient_C']+y[0]/p['heat_capacity_MWh_per_K'];te=s['source_in_C']-s['source_glide_K']-s['evaporator_approach_K']
        hot=max(T+s['charge_approach_K'],s['delivery_C']+s['direct_approach_K']);lift=hot+s['condenser_approach_K']-te
        cop=1+s['cooling_factor']*(te+273.15)/lift;budget=s['source_capacity_MW_per_K']*s['source_glide_K']
        q=min(8,s['hp_capacity_MW'],s['hot_capacity_MW_per_K']*(hot-T),budget*cop/(cop-1));w=q/cop;ql=q-w
        loss=p['loss_rate_per_h']*y[0]
        return [p['eta_charge']*q-loss,q,w,ql,loss,(1-p['eta_charge'])*q]
    y=[float(E),0.,0.,0.,0.,0.];h=span/n
    for _ in range(n):
        k1=rhs(y);k2=rhs([v+h/2*k for v,k in zip(y,k1)]);k3=rhs([v+h/2*k for v,k in zip(y,k2)]);k4=rhs([v+h*k for v,k in zip(y,k3)])
        y=[v+h*(a+2*b+2*c+e)/6 for v,a,b,c,e in zip(y,k1,k2,k3,k4)]
    return dict(zip(['end_energy_MWh','heat_MWh','compressor_MWh','source_MWh','standing_loss_MWh','charge_loss_MWh'],y))
def actual_segment(z,a):
    p,h,x=a['p'],a['h'],a['x'];span=d(z[1]);E=d(z[3]);P=d(p[4])*d(z[6])-d(z[7])/d(p[5]);rate=d(p[6])
    end=E*(-rate*span).exp()+P*(1-(-rate*span).exp())/rate if rate else E+P*span
    cop=d(h[1])*(d(x[2])+D('273.15'))/(d(x[2])-d(x[1]));want=min(d(h[0]),d(z[13]),d(x[0])*cop/(cop-1))
    tol=72*d(math.ulp(max(1,p[1])))
    return dict(held_ODE=abs(d(z[4])-end)<=tol,HP=near(z[10],want) and near(z[11],d(z[10])/cop) and near(z[12],d(z[10])-d(z[11])) and near(z[14],cop),
        mode=z[0]==2 and z[5]==0 and z[6]==z[10] and all(v==0 for v in z[7:10]),
        bounds=min(z[3:14])>=0 and max(z[3:5])<=p[1] and z[6]<=p[2] and z[10]<=h[0] and z[12]<=x[0]+1e-12,
        losses=near(z[16],E+P*span-end) and near(z[17],(1-d(p[4]))*d(z[6])*span) and z[18]==0,
        law=abs(E+(d(z[11])+d(z[12]))*span-d(z[4])-d(z[16])-d(z[17]))<=tol,
        temperatures=near(z[21],d(p[9])+E/d(p[8])) and near(z[22],d(p[9])+d(z[4])/d(p[8])))
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');r=json.loads((folder/'report.json').read_text());spec=json.loads((folder/'spec.json').read_text());checks=[];selfchecks=[];branch_flags=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','report_reopen',r==json.loads((folder/'mat_reopen.json').read_text()))
    check('execution','harness',r['summary']['failed']==0 and all(c['passed'] for c in r['assertions']))
    check('scope','no_new_model',r['new_model'] is False and r['model_version']=='0.52')
    check('Stateflow','actual_charts_license',r['metadata']['chart_count']==2 and r['metadata']['stateflow_license_test']==1)
    with localcontext() as ctx:
        ctx.prec=70
        check('vectors','count',len(r['vectors'])==168)
        for i,v in enumerate(r['vectors']):
            want=boundary(v['spec'],v['policy'],v['energy'],v['request']);b=v['boundary']
            for key,value in want.items():
                if key=='tank_branch':
                    floor=d(v['spec']['delivery_C'])+d(v['spec']['direct_approach_K']);gap=want['tank_C']+d(v['spec']['charge_approach_K'])-floor
                    if b[key]!=value:
                        bound=2*d(math.ulp(float(want['tank_C'])))+2*d(math.ulp(float(floor)))
                        branch_flags.append(dict(vector=i,exact_input_gap_K=str(gap),rounding_enclosure_K=str(bound),nominal_branch=b[key],exact_input_branch=value,status='OPEN_UNCERTIFIED_BRANCH_AT_ROUNDOFF_SCALE'))
                        check('branch_ambiguity_enclosure',str(i),abs(gap)<=bound and b[key]==(b['tank_C']+v['spec']['charge_approach_K']>=v['spec']['delivery_C']+v['spec']['direct_approach_K']))
                    else:check('exact_branch_classification',str(i),True)
                else:check('instantaneous',f'{i}_{key}',b[key]==value if key=='limiter' else near(b[key],value))
            check('instantaneous','Carnot_'+str(i),d(b['cop_compressor'])<=(want['condenser_C']+D('273.15'))/(want['condenser_C']-want['evaporator_C'])+D('1e-12'))
        for i,v in enumerate(r['analytic']):
            z=v['result'];want=exact(v['spec'],v['policy'],z['initial_energy_MWh'],z['span_h']);numeric=rk4(v['spec'],v['policy'],z['initial_energy_MWh'],z['span_h'])
            for key,value in want.items():check('exact_equation',f'{i}_{key}',near(z[key],value))
            for key,value in numeric.items():check('independent_RK4',f'{i}_{key}',near(z[key],value,'1e-10'))
            # Interior audits exercise the endpoint-certification claim, not production code.
            for fraction in [.25,.5,.75]:
                mid=exact(v['spec'],v['policy'],z['initial_energy_MWh'],z['span_h']*fraction)
                b=boundary(v['spec'],v['policy'],mid['end_energy_MWh'],v['request'])
                check('regime_certificate',f'{i}_{fraction}',b['limiter']==4 and b['tank_branch'] and b['tank_C']<=d(v['spec']['tank_max_C']))
        check('domains','rejections',len(r['faults'])==14 and all(f['rejected'] and f['identifier'].startswith('DCHR:v54:') for f in r['faults']))
        reject=r['rejection'];a=reject['inputs'];check('unsupported','actual_cold_rejection','Condenser must support tank maximum' in reject['error_message'] and a['x'][2]<spec['boundary']['tank_max_C'])
        check('unsupported','cold_instantaneous_admissible',boundary(spec['boundary'],spec['policy'],a['E0'],8)['heat_MW']>0)
        ref=exact(spec['boundary'],spec['policy'],spec['policy']['initial_energy_MWh'],spec['policy']['dt_h'])
        for key,val in ref.items():check('reference',key,near(r['reference'][key],val))
        originals=json.loads((folder/'original_simulation_reopen.json').read_text());check('MAT','simulation_count',len(originals)==15)
        errors=[];workerrors=[];intervals=0;active=None
        for ex in r['experiments']:
            energy=spec['policy']['initial_energy_MWh'];clock=[1,0,0,0];tot=[D(0)]*5
            runs=[ex['runs']] if isinstance(ex['runs'],dict) else ex['runs']
            check('execution','chunk_count_'+str(ex['chunks']),len(runs)==ex['chunks'])
            for item in runs:
                intervals+=1;id=item['id'];a=item['inputs'];ds=item['dispatch'];zs=[item['raw_segments'][j:j+28] for j in range(0,1792,28)];ps=[item['raw_plans'][j:j+23] for j in range(0,1472,23)]
                check('MAT',id,item==next(o for o in originals if o['id']==id))
                check('memory',id,a['E0']==energy and a['m0']==clock and item['clock_start']==clock)
                b=boundary(spec['boundary'],spec['policy'],energy,8)
                check('coupled_sample',id,near(a['x'][2],b['condenser_C']) and near(a['h'][1],b['heating_factor']) and near(a['h'][0],min(d(spec['boundary']['hp_capacity_MW']),b['hot_budget_MW'])))
                check('handoff',id,all(zs[j][4]==zs[j+1][3] for j in range(63)) and all(z[4]==p[22] and z[3]==p[1] for z,p in zip(zs,ps)) and ds[7]==zs[-1][4])
                duration=D(0);start=energy;subtotal=[D(0)]*5
                for j,z in enumerate(zs):
                    if z[1]==0:check('padding',f'{id}_{j}',z[3]==z[4] and z[0]==0 and all(v==0 for v in z[5:14]+z[16:21]) and z[26]==z[27]);continue
                    active=(z,a)
                    for kind,ok in actual_segment(z,a).items():check(kind,f'{id}_{j}',ok)
                    check('sample_clock',f'{id}_{j}',z[25]==1 and near(z[26],d(clock[1])+duration) and near(z[27],d(clock[1])+duration+d(z[1])))
                    duration+=d(z[1]);subtotal=[v+d(z[k])*d(z[1]) for v,k in zip(subtotal[:3],[10,11,12])]+[subtotal[3]+d(z[16]),subtotal[4]+d(z[17])]
                check('macro',id,near(duration,a['dt_h']) and near(ds[18]*a['dt_h'],subtotal[0]) and near(ds[19]*a['dt_h'],subtotal[1]) and near(ds[20]*a['dt_h'],subtotal[2]) and near(ds[8],subtotal[3]) and near(ds[9],subtotal[4]))
                check('macro_law',id,abs(d(start)+subtotal[1]+subtotal[2]-d(ds[7])-subtotal[3]-subtotal[4])<D('2e-12'))
                clock=item['clock_end'];energy=ds[7];tot=[a+b for a,b in zip(tot,subtotal)]
            check('experiment',str(ex['chunks']),near(ex['end_energy_MWh'],energy) and all(near(ex[key],v) for key,v in zip(['heat_MWh','compressor_MWh','source_MWh','standing_loss_MWh','charge_loss_MWh'],tot)))
            errors.append(abs(d(energy)-ref['end_energy_MWh']));workerrors.append(abs(d(ex['compressor_MWh'])-ref['compressor_MWh']))
        check('discrepancy','held_temperature',errors[0]>D('1e-6') and workerrors[0]>D('1e-6'))
        check('sensitivity','monotone_refinement',all(a>b for a,b in zip(errors,errors[1:])) and errors[-1]<errors[0]/4 and all(a>b for a,b in zip(workerrors,workerrors[1:])))
        z,a=active
        for name,index in [('electric',11),('source',12),('endpoint',4),('charge',6)]:
            changed=z.copy();changed[index]+=.01;selfchecks.append(dict(name=name,passed=not all(actual_segment(changed,a).values())))
        z=copy.deepcopy(r['analytic'][0]['result']);z['compressor_MWh']+=.01
        selfchecks.append(dict(name='exact_propagator_work',passed=not near(z['compressor_MWh'],exact(r['analytic'][0]['spec'],r['analytic'][0]['policy'],z['initial_energy_MWh'],z['span_h'])['compressor_MWh'])))
    for v in json.loads((folder/'preservation.json').read_text()):check('preservation',v['path'],sha(ROOT/v['path'])==v['sha256'] and (ROOT/v['path']).stat().st_size==v['size'])
    revisions=sorted(folder.glob('reviewer_revision*.json'));revision=json.loads(revisions[-1].read_text()) if revisions else None
    for v in json.loads((folder/'source_hashes.json').read_text()):
        current_ok=sha(ROOT/v['path'])==v['sha256']
        if revision and v['path']==revision['path']:
            current_ok=revision['original_sha256']==v['sha256'] and sha(ROOT/v['path'])==revision['revised_sha256'] and sha(folder/revision['snapshot'])==revision['revised_sha256']
        check('snapshot',v['path'],current_ok and sha(folder/'source_snapshot'/v['path'])==v['sha256'])
    observed=json.loads((folder/'source_observations.json').read_text());check('source','primary_binding',sha(ROOT/'sources/papers/20_Verzino_Varna_2026.pdf')==observed['source20_pdf_sha256'] and observed['equipment_calibration']=='OPEN' and observed['full_primary_signoffs']==0)
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')];check('execution','successful_receipt',any(v['exit_code']==0 and 'run_coupled_interface_v54' in v['command'] for v in receipts))
    with zipfile.ZipFile(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx') as ar:
        payload=b' '.join(ar.read(n) for n in ar.namelist() if n.endswith('.xml'));check('artifact','saved_six_states',all(n.encode() in payload for n in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']))
    result=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),report_sha256=sha(folder/'report.json'),actual_passed=sum(c['passed'] for c in checks),actual_failed=sum(not c['passed'] for c in checks),
        reviewer_selfchecks_passed=sum(c['passed'] for c in selfchecks),reviewer_selfchecks_failed=sum(not c['passed'] for c in selfchecks),actual_successful_intervals=intervals,actual_unsupported_rejections=1,
        energy_errors_MWh=[str(e) for e in errors],compressor_errors_MWh=[str(e) for e in workerrors],exact_branch_classification_failures=len(branch_flags),branch_flags=branch_flags,checks=checks,selfchecks=selfchecks,
        scope='Continuous-power equations and nonboundary single-regime propagation PASS if checks pass; exact branch classification flags remain OPEN and are not accepted discrete guards.',
        independence='70-digit equations and independently programmed min-envelope RK4; no production imports; same-agent review, no measured physical validation')
    path=folder/('independent_QA_v54_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json');path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','selfchecks']}));print(path.relative_to(ROOT).as_posix())
    sys.exit(1 if result['actual_failed'] or result['reviewer_selfchecks_failed'] else 0)
if __name__=='__main__':main()
