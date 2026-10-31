"""Independent Decimal clocks, analytic HP root, ODE and artifact review.

No production MATLAB function is imported or translated. QA is an independent
algorithm in the same agent, not separate personnel or physical validation.
"""
from datetime import datetime,timezone
from decimal import Decimal,localcontext
from pathlib import Path
import csv,hashlib,json,math,shutil,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v,width):return [] if not v else v if isinstance(v[0],list) else [v] if width>1 else [[x] for x in v]
def dec(v):return Decimal.from_float(float(v))
def approx(a,b,tol=2e-9):return a is None and b is None or a is not None and b is not None and abs(a-b)<=tol+2e-11*abs(b)
def nearflow(a,b):return abs(a-b)<=64*max(math.ulp(a),math.ulp(b))+abs(b)*1e-13
def hp_oracle(q):
    """Solve normalized source constraint analytically in 110-digit Decimal."""
    with localcontext() as ctx:
        ctx.prec=110
        cap,request,source=map(dec,(q['cap_MW'],q['request_MW'],q['source_MW']))
        penalty,minimum=dec(q['penalty']),dec(q['cop_min']);nominal=Decimal(4)
        if cap==0 or request==0 or source==0:return None
        a=nominal*(1-penalty);b=nominal*penalty
        low=max(Decimal(0),(minimum/nominal-(1-penalty))/penalty) if penalty else Decimal(0)
        upper=min(request,cap)/cap
        if low>upper:return None
        evap=lambda r:cap*r*(1-1/(a+b*r)) if r else Decimal(0)
        if evap(low)>source:return None
        r=upper
        if evap(upper)>source:
            s=source/cap;B=a-1-s*b
            if b==0:r=s*a/(a-1)
            else:
                disc=(B*B+4*b*s*a).sqrt()
                r=2*s*a/(B+disc) if B>=0 else (-B+disc)/(2*b)
        output=cap*r;cop=a+b*r
        return tuple(float(x) for x in (output,cop,output/cop,output-output/cop))
def main():
    folder=ROOT/Path(sys.argv[1]);receipts=[read(ROOT/Path(x)) for x in sys.argv[2:]]
    spec=read(folder/'source_snapshot/spec/cases.json');execution=read(folder/'execution_v38.json')
    saved=read(folder/'mat_audit_v38.json');mats={x['id']:x for x in saved['simulations']}
    metadata=read(folder/'numeric_metadata_v38.json');groups={};ledger=[];clockledger=[]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    snapshot=folder/'qa_source'/stamp;snapshot.mkdir(parents=True);shutil.copy2(__file__,snapshot/Path(__file__).name)
    def ck(group,name,ok):groups.setdefault(group,[]).append(dict(name=name,passed=bool(ok)))
    ck('artifact','three_observed_zero_exit_batches',len(receipts)==3 and all(r['exit_code']==0 for r in receipts))
    ck('artifact','actual_saved_v38_execution','run_stateflow_acceptance_v38' in receipts[0]['command'])
    ck('artifact','separate_saved_MAT_export','export_stateflow_resolution_v38' in receipts[1]['command'])
    ck('artifact','actual_Stateflow_license',metadata['stateflow_license_test']==1)
    ck('artifact','six_saved_thermal_states',set(metadata['thermal_state_names'])=={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'})
    ck('artifact','two_saved_supervisor_states',set(metadata['supervisor_state_names'])=={'HP_OFF','HP_ON'})
    ck('artifact','unique_full_execution_set',len(execution)==len(spec['cases'])==len({c['id'] for c in execution}))
    actual={x['id']:x for x in execution};vectors=list(csv.DictReader((folder/'source_snapshot/spec/vectors.csv').open(encoding='utf-8')))
    allmodes=set();maxbalance=0.;equations=0
    for c in spec['cases']:
        a=actual[c['id']];ck('artifact',c['id']+'_MAT_binding',a==mats[c['id']])
        ck('artifact',c['id']+'_MAT_file',(folder/(c['id']+'_simulation.mat')).stat().st_size>0)
        ck('domain',c['id']+'_expected_rejection',a['rejected']==c['expected_reject'])
        if a['rejected']:
            ck('domain',c['id']+'_runtime',a['phase']=='Execution')
            if c['kind'] in ('band','cutoff_band'):ck('domain',c['id']+'_before_events','Unresolved capacity/restart/cutoff' in a['error_message'] and 'Nonpositive event progress' not in a['error_message'])
            continue
        yy=rows(a['dispatch'],25);ss=rows(a['segments'],52);starts=rows(a['clock_start'],4);ends=rows(a['clock_end'],4)
        ck('numeric',c['id']+'_sample_count',len(yy)==len(c['inputs'])==len(starts)==len(ends))
        p,h=c['p'],c['h'];etol=1e-10+128*math.ulp(max(1.,p[1]));previousE=c['initial_energy_MWh']
        with localcontext() as ctx:
            ctx.prec=110
            trueAge=dec(c['initial_clock'][1])+dec(c['initial_clock'][2]);previousLatch=c['initial_clock'][0]
            previousBound=c['initial_clock'][3];expandedErrors=[];highErrors=[]
            for i,(y,start,end,x) in enumerate(zip(yy,starts,ends,c['inputs'])):
                ck('clock',f'{c["id"]}_{i}_persistent_memory',start==c['initial_clock'] if i==0 else start==ends[i-1])
                parts=[r for r in ss if r[0]==i];totalspan=Decimal(0);energies=[Decimal(0)]*9;losses=[Decimal(0)]*3
                for n,r in enumerate(parts):
                    z=r[2:30];s=r[30:52];allmodes.add(int(z[0]));name=f'{c["id"]}_{i}_{n}'
                    ck('numeric',name+'_finite_trace',all(v is not None and math.isfinite(v) for j,v in enumerate(z) if j!=14) and all(v is not None for j,v in enumerate(s) if j!=7))
                    ck('numeric',name+'_positive_duration',z[1]>0 and z[1]==s[0])
                    ck('numeric',name+'_energy_handoff',abs(z[3]-previousE)<=etol)
                    ck('numeric',name+'_TES_bounds',min(z[3:5])>=-etol and max(z[3:5])<=p[1]+etol and (z[7]==0 or min(z[3:5])>=p[7]-etol))
                    ck('numeric',name+'_nonnegative_limits',min(z[5:14])>=0 and z[6]<=p[2] and z[7]<=p[3] and z[8]<=p[10] and z[6]*z[7]==0)
                    ck('numeric',name+'_mode',int(z[0])==(5 if z[9]>0 else 4 if z[8]>0 else 3 if z[7]>0 else 2 if z[6]>0 else 1 if z[5]>0 else 0))
                    span=dec(z[1]);power=dec(p[4])*dec(z[6])-dec(z[7])/dec(p[5]);rate=dec(p[6]);E=dec(z[3])
                    retain=(-rate*span).exp();integral=(1-retain)/rate if rate else span;ideal=E*retain+power*integral
                    ck('equation',name+'_Decimal_ODE',abs(dec(z[4])-ideal)<=dec(etol))
                    ck('equation',name+'_standing_loss',abs(dec(z[16])-(E+power*span-ideal))<=dec(etol))
                    ck('equation',name+'_charge_loss',abs(dec(z[17])-(1-dec(p[4]))*dec(z[6])*span)<=dec(etol))
                    ck('equation',name+'_discharge_loss',abs(dec(z[18])-(1/dec(p[5])-1)*dec(z[7])*span)<=dec(etol))
                    equations+=4
                    ck('equation',name+'_HP_firstlaw',abs(dec(z[10])-dec(z[11])-dec(z[12]))<=dec(8*max(math.ulp(v) for v in z[10:13])))
                    ck('equation',name+'_demand_service',abs(dec(x[3])-sum(map(dec,(z[5],z[7],z[8],z[9]))))<=dec(1e-9+128*math.ulp(max(1.,x[3]))))
                    residual=E+(dec(z[11])+dec(z[12])+dec(z[8])-dec(z[19]))*span-dec(z[4])-sum(map(dec,z[16:19]))
                    maxbalance=max(maxbalance,abs(float(residual)))
                    ck('equation',name+'_system_firstlaw',abs(residual)<=dec(etol))
                    if z[10]>0:
                        nominal=min(h[3],h[1]*(x[2]+273.15)/(x[2]-x[1]) if h[5]==0 else h[6]+h[7]*(x[2]-x[1])+h[8]*(x[2]-x[1])**2)
                        idealCOP=dec(nominal)*(1-dec(h[4])+dec(h[4])*dec(z[10])/dec(h[0]))
                        ck('equation',name+'_normalized_COP',z[14] is not None and abs(dec(z[14])-idealCOP)<=dec(1e-10))
                    else:ck('equation',name+'_OFF_COP',z[14] is None and z[24]==0)
                    latch=z[25]
                    if latch!=previousLatch:
                        ck('clock',name+'_reset_all_parts',s[15]==s[18]==s[20]==0)
                        if latch==1:ck('clock',name+'_OFF_dwell',trueAge>=dec(c['c'][2])-dec(1e-8) and s[16]==3 and s[1]<=c['c'][0]+128*math.ulp(p[1]))
                        else:ck('clock',name+'_ON_dwell_or_safety',s[16]==1 or trueAge>=dec(c['c'][1])-dec(1e-8))
                        trueAge=Decimal(0);previousBound=0.
                    ck('clock',name+'_start_expansion',abs(dec(s[15])+dec(s[18])-trueAge)<=dec(s[20])+Decimal('1e-90'))
                    trueAge+=span;expandedError=abs(dec(s[17])+dec(s[19])-trueAge);highError=abs(dec(z[27])-trueAge)
                    expandedErrors.append(float(expandedError));highErrors.append(float(highError))
                    ck('clock',name+'_certified_expansion_error',expandedError<=dec(s[21])+Decimal('1e-90'))
                    ck('clock',name+'_cumulative_report_accuracy',highError<=dec(1e-8) and abs(s[19])+s[21]<=1e-8)
                    ck('clock',name+'_nondecreasing_error_bound',s[21]>=s[20]>=previousBound)
                    previousBound=s[21];previousLatch=latch;previousE=z[4]
                    totalspan+=span
                    for k in range(9):energies[k]+=dec(z[5+k])*span
                    for k in range(3):losses[k]+=dec(z[16+k])
                ck('clock',f'{c["id"]}_{i}_complete_partition',abs(totalspan-dec(p[0]))<=dec(128*math.ulp(max(1.,p[0]))))
                ck('clock',f'{c["id"]}_{i}_final_clock',end[0]==previousLatch and abs(dec(end[1])+dec(end[2])-trueAge)<=dec(end[3])+Decimal('1e-90'))
                ck('numeric',f'{c["id"]}_{i}_final_energy',abs(y[7]-previousE)<=etol)
                for k in range(5):ck('equation',f'{c["id"]}_{i}_integrated_port_{k}',abs(dec(y[1+k])-energies[k]/dec(p[0]))<=dec(1e-9+128*math.ulp(max(1.,float(energies[k]/dec(p[0]))))))
                for k in range(3):ck('equation',f'{c["id"]}_{i}_integrated_loss_{k}',abs(dec(y[8+k])-losses[k])<=dec(etol))
            clockledger.append(dict(id=c['id'],max_report_error_h=max(highErrors,default=0),max_expansion_error_h=max(expandedErrors,default=0),final_clock=ends[-1]))
            if c['kind']=='clock' or c['kind']=='nonadvancing':
                ideal=dec(c['initial_clock'][1])+dec(c['initial_clock'][2])+len(ends)*dec(p[0]);last=ends[-1]
                ck('clock',c['id']+'_exact_macro_duration',abs(dec(last[1])+dec(last[2])-ideal)<=dec(last[3])+Decimal('1e-90'))
        if c['kind']=='reference':
            expected=[r for r in vectors if r['scenario_id']==c['id']]
            ck('reference',c['id']+'_independent_count',len(expected)==len(yy))
            for i,(y,r) in enumerate(zip(yy,expected)):
                for value,(key,expectedvalue) in zip(y,list(r.items())[2:]):
                    b=float(expectedvalue);ck('reference',f'{c["id"]}_{i}_{key}',value is None and math.isnan(b) or value is not None and abs(value-b)<=2e-9+2e-11*abs(b))
        if c['kind'] in ('band','cutoff_band'):ck('domain',c['id']+'_exact_OFF_control',all(m[0]==0 for m in ends) and all(y[7]==10. and y[18]==0. for y in yy))
        if c['kind']=='dwell':
            ck('clock',c['id']+'_residual_controls_first_latch',ss[0][2+25]==(0 if c['initial_clock'][2]<0 else 1))
    ck('numeric','all_six_executed_modes',allmodes==set(range(6)))
    probes=read(folder/'hp_components_v38.json');savedprobes=saved['component_probes'];flags=metadata['component_flags']
    ck('HP','all_probes_count',len(probes)==len(spec['hp_probes'])==len(flags))
    for q,a,b,flag in zip(spec['hp_probes'],probes,savedprobes,flags):
        ck('artifact',q['id']+'_component_MAT_binding',a==b)
        ck('HP',q['id']+'_domain',a['rejected']==q['expected_reject'])
        if a['rejected']:
            ck('HP',q['id']+'_explicit_underflow','HPResolution' in a['error_identifier']);continue
        hp=a['output'];ideal=hp_oracle(q)
        ck('HP',q['id']+'_availability',hp['available']==(ideal is not None))
        if ideal is None:
            ck('HP',q['id']+'_OFF',hp['heat_output_MW']==hp['electric_MW']==hp['source_used_MW']==0 and flag['COP_is_nan']);continue
        output,cop,electric,source=ideal
        ck('HP',q['id']+'_finite_COP',flag['COP_is_finite'] and not flag['COP_is_inf'] and not flag['COP_is_nan'])
        ck('HP',q['id']+'_analytic_output',nearflow(hp['heat_output_MW'],output))
        ck('HP',q['id']+'_analytic_COP',abs(hp['cop_operating']-cop)<=1e-12+128*math.ulp(cop))
        ck('HP',q['id']+'_analytic_electric',nearflow(hp['electric_MW'],electric))
        ck('HP',q['id']+'_analytic_source',nearflow(hp['source_used_MW'],source))
        ck('HP',q['id']+'_source_request_capacity',hp['source_used_MW']<=q['source_MW']+math.ulp(q['source_MW'])*2 and hp['heat_output_MW']<=min(q['request_MW'],q['cap_MW']))
        ledger.append(dict(id=q['id'],expected_analytic_output_MW=output,actual_output_MW=hp['heat_output_MW'],expected_COP=cop,actual_COP=hp['cop_operating']))
    comparisons=read(folder/'comparison_v36.json');ck('reference','ten_fresh_saved_v36_comparisons',len(comparisons)==10)
    for c in comparisons:
        ck('reference',c['id']+'_actual_v36_MAT',(folder/(c['id']+'_v36_comparison.mat')).is_file())
        for i,(a,b) in enumerate(zip(rows(c['old_dispatch'],25),rows(c['new_dispatch'],25))):
            for j,(v,w) in enumerate(zip(a,b)):ck('reference',f'{c["id"]}_{i}_{j}_fresh_saved_v36',approx(v,w))
    faults=read(folder/'runtime_faults_v38.json');ck('fault','30_actual_rejections',len(faults)==30 and all(f['rejected'] for f in faults))
    for f in faults:
        ck('fault',f['id']+'_saved_error',mats[f['id']+'_fault']['rejected'] and mats[f['id']+'_fault']['error_message']==f['error_message'] and f['phase']=='Execution')
    pre=mats['pre_fault_clean'];post=mats['post_fault_clean'];pre=dict(pre,id='restored');post=dict(post,id='restored')
    ck('fault','restored_model_exact_trace',pre==post)
    for p in (folder/'source_snapshot').glob('*'):
        if not p.is_file():continue
        current=ROOT/('audit' if p.suffix=='.py' else 'matlab/simulink')/p.name
        if not current.exists():current=ROOT/'matlab/+dchr/+components'/p.name
        ck('artifact',p.name+'_source_binding',current.is_file() and sha(current)==sha(p))
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v38.slx'
    with zipfile.ZipFile(model) as z:
        xml='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith('.xml'))
        ck('archive','new_host_HP_planner','dchr_segment_plan_v38' in xml and 'dchr_segment_plan_v36' not in xml)
        ck('archive','actual_supervisor_compensated_calls','stateflow_clock_add_v38(age,low,bound,s(1))' in xml)
        ck('archive','actual_residual_clock_memory','dchr_m0_v38' in xml and '[4 1]' in xml)
        ck('archive','no_unconditional_mode_transitions','stateflow_choose_mode_v38(segmentInput,parameters)' in xml)
    previous={}
    for pattern in ('Stateflow_manifest_v*.json','Stateflow_admissibility_manifest_v*.json','Stateflow_fallback_manifest_v*.json','Stateflow_postclose_manifest_v37_*.json','TES_event_manifest_v31_*.json'):
        for manifest in (ROOT/'audit').glob(pattern):
            for item in read(manifest)['files']:previous[item['path']]=item
    for name,item in previous.items():
        p=Path(name);p=p if p.is_absolute() else ROOT/p
        size=item.get('bytes',item.get('size_bytes'))
        ck('preservation',name,p.is_file() and p.stat().st_size==size and sha(p)==item['sha256'])
    ck('preservation','saved_v36_hash',sha(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v36.slx')==read(ROOT/'STATUS_stateflow_v36.json')['model_sha256'])
    synthetic=dict(cap_MW=8.,request_MW=8.,source_MW=6.,penalty=.3,cop_min=1.2)
    ck('synthetic','analytic_full_load_oracle',hp_oracle(synthetic)==(8.,4.,2.,6.))
    synthetic.update(source_MW=.75,penalty=0.)
    ck('synthetic','analytic_source_limit_oracle',hp_oracle(synthetic)==(1.,4.,.25,.75))
    synthetic.update(request_MW=1.,source_MW=8.,penalty=.3,cop_min=3.5)
    ck('synthetic','analytic_cutoff_OFF_oracle',hp_oracle(synthetic) is None)
    counts={g:dict(passed=sum(t['passed'] for t in tests),failed=sum(not t['passed'] for t in tests)) for g,tests in groups.items()}
    report=dict(version='0.38',evidence_class='independent_algorithm_and_artifact_QA_same_agent',timestamp_utc=datetime.now(timezone.utc).isoformat(),counts=counts,
        model_sha256=sha(model),result_directory=str(folder.relative_to(ROOT)),previous_immutable_entries=len(previous),clock_ledger=clockledger,
        HP_analytic_ledger=ledger,max_independent_balance_residual_MWh=maxbalance,checks=groups,physical_validation=False,article_replication=False)
    path=folder/('independent_QA_v38_'+stamp+'.json');path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('QA='+str(path.relative_to(ROOT)));print(json.dumps(counts))
    for g,tests in groups.items():
        fails=[t['name'] for t in tests if not t['passed']]
        if fails:print(g+' FAIL='+json.dumps(fails[:30]))
    assert not sum(v['failed'] for v in counts.values())
if __name__=='__main__':main()
