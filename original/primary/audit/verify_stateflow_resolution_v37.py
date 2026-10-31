"""Independent exact-input Decimal clock/normalized-load HP and artifact QA.

Success here accepts defect reproduction, not a corrected model. No MATLAB
code is imported; legacy dispatch vectors have their own independent oracle.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import csv, hashlib, json, math, sys, zipfile, shutil
from stateflow_reference_v30 import PORTS, HP

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def rows(v,width):
    if not v:return []
    return v if isinstance(v[0],list) else [v] if width>1 else [[x] for x in v]
def main():
    folder=ROOT/Path(sys.argv[1]);receipt=read(ROOT/Path(sys.argv[2]));export_receipt=read(ROOT/Path(sys.argv[3]))
    spec=read(folder/'source_snapshot/spec/cases.json');actual={x['id']:x for x in read(folder/'execution_v37.json')}
    saved=read(folder/'mat_audit_v37.json');mats={x['id']:x for x in saved['simulations']}
    probes=read(folder/'hp_components_v37.json');groups={};ledger=[]
    metadata=read(folder/'numeric_metadata_v37.json')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    reviewer_snapshot=folder/'qa_source'/stamp
    reviewer_snapshot.mkdir(parents=True);shutil.copy2(Path(__file__),reviewer_snapshot/Path(__file__).name)
    def ck(group,name,ok):groups.setdefault(group,[]).append(dict(name=name,passed=bool(ok)))
    def near(a,b):return a==b or a is None and math.isnan(b) or a is not None and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=2e-9+2e-11*abs(b)
    def clocks(entry,name):return rows(entry[name],2)
    ck('artifact','actual_simulation_exit0',receipt['exit_code']==0 and 'run_stateflow_resolution_v37' in receipt['command'])
    ck('artifact','separate_MAT_export_exit0',export_receipt['exit_code']==0 and 'export_stateflow_resolution_v37' in export_receipt['command'])
    ck('artifact','actual_Stateflow_license',metadata['stateflow_license_test']==1)
    ck('artifact','six_saved_thermal_states',set(metadata['thermal_state_names'])=={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'})
    ck('artifact','saved_HP_supervisor',set(metadata['supervisor_state_names'])=={'HP_OFF','HP_ON'})
    baseline=list(csv.DictReader((folder/'source_snapshot/spec/baseline_vectors.csv').open(encoding='utf-8')))
    for c in spec['cases']:
        a=actual[c['id']];b=mats[c['id']]
        for key in b:ck('artifact',c['id']+'_'+key,a[key]==b[key])
        ck('artifact',c['id']+'_saved_MAT',(folder/(c['id']+'_simulation.mat')).stat().st_size>0)
        if c['kind']=='baseline':
            ck('baseline',c['id']+'_executes',not a['rejected'])
            expected=[r for r in baseline if r['scenario_id']==c['id']]
            yy=rows(a['dispatch'],25);ck('baseline',c['id']+'_sample_count',len(yy)==len(expected))
            for i,(y,r) in enumerate(zip(yy,expected)):
                for key,value in zip(PORTS+HP,y):ck('baseline',f'{c["id"]}_{i}_{key}',near(value,float(r[key])))
        elif c['kind']=='clock':
            ck('clock',c['id']+'_executes',not a['rejected'])
            starts=clocks(a,'clock_start');ends=clocks(a,'clock_end');n=len(c['inputs'])
            ck('clock',c['id']+'_samples',len(ends)==n)
            errors=[]
            with localcontext() as ctx:
                ctx.prec=90
                age=Decimal.from_float(c['initial_clock'][1]);dt=Decimal.from_float(c['p'][0])
                for i,(start,end) in enumerate(zip(starts,ends)):
                    ideal=age+(i+1)*dt
                    errors.append(float(Decimal.from_float(end[1])-ideal))
                    ck('clock',f'{c["id"]}_{i}_positive_elapsed',end[1]>start[1] and end[0]==start[0]==0)
                    ck('clock',f'{c["id"]}_{i}_latch_continuity',i==0 or start==ends[i-1])
                maxerr=max(abs(e) for e in errors);tol=64*math.ulp(max(1.,c['initial_clock'][1]+n*c['p'][0]))
            ledger.append(dict(id=c['id'],dt_h=c['p'][0],intervals=n,initial_age_h=c['initial_clock'][1],
                final_age_h=ends[-1][1],exact_input_elapsed_h=float(dt*n),clock_error_h=errors[-1],max_abs_error_h=maxerr,
                local_tolerance_h=tol,comparison_budget_h=1e-8,global_budget_exceeded=maxerr>1e-8))
            # Independent ODE: zero losses, absent HP, known held/changing demand.
            ee=Decimal.from_float(c['initial_energy_MWh']);eta=Decimal.from_float(c['p'][5])
            for i,(x,y) in enumerate(zip(c['inputs'],rows(a['dispatch'],25))):
                ee-=Decimal.from_float(x[3])*dt/eta
                ck('equation',f'{c["id"]}_{i}_energy',abs(y[7]-float(ee))<1e-10)
                ck('equation',f'{c["id"]}_{i}_service',y[3]==x[3] and y[4]==0 and y[5]==0 and y[18]==0)
        elif c['kind']=='band':
            # Exact OFF physical trajectory: no loss/demand, E=capacity>restart forever.
            should_reject=c['gap_ulps']<=64
            ck('band',c['id']+'_observed_rejection',a['rejected']==should_reject)
            if should_reject:
                ck('band',c['id']+'_runtime_progress_defect',a['phase']=='Execution' and 'Nonpositive event progress' in a['error_message'])
            else:
                ck('band',c['id']+'_exact_OFF',all(m[0]==0 for m in clocks(a,'clock_end')) and all(y[7]==10. and y[18]==0. for y in rows(a['dispatch'],25)))
            ledger.append(dict(id=c['id'],gap_MWh=10.-c['c'][0],energy_tolerance_MWh=64*math.ulp(10.),
                exact_policy='HP remains OFF, constant capacity energy',runtime_rejected=a['rejected'],phase=a['phase']))
        elif c['kind']=='nonadvancing':
            ck('resolution',c['id'],a['rejected'] and a['phase']=='Execution' and 'advance representable physical clocks' in a['error_message'])
        elif c['kind']=='hp_runtime':
            reject=c['h'][0]<1e-308
            ck('HP',c['id']+'_actual_saved_model',a['rejected']==reject)
            if reject:ck('HP',c['id']+'_COP_gate',a['phase']=='Execution' and 'COP failure' in a['error_message'])
    for q,a,b,flags in zip(spec['hp_probes'],probes,saved['component_probes'],metadata['component_flags']):
        ck('artifact',q['id']+'_component_MAT_binding',a==b)
        hp=a['output'];cap=Decimal.from_float(q['cap_MW']);request=Decimal.from_float(q['request_MW'])
        # Full normalized load C=N(1-penalty+penalty*Q/cap)=N. Exact C=4.
        expected=4.*(1.-.3+.3*float(request/cap))
        overflow=q['cap_MW']<1e-308
        ck('HP',q['id']+'_does_not_reject',not a['rejected'])
        ck('HP',q['id']+'_availability',hp['available'] and hp['heat_output_MW']==q['cap_MW'])
        if overflow:
            ck('HP',q['id']+'_invalid_COP_return',hp['cop_operating'] is None and hp['electric_MW']==0)
            ck('HP',q['id']+'_MAT_Inf_not_NaN',flags['COP_is_inf'] and not flags['COP_is_nan'] and flags['slope_is_inf'])
        else:ck('HP',q['id']+'_normalized_COP',near(hp['cop_operating'],expected))
        if not overflow:
            with localcontext() as ctx:
                ctx.prec=90
                ideal_w=Decimal.from_float(q['cap_MW'])/Decimal(4)
                ideal_ev=Decimal.from_float(q['cap_MW'])*Decimal(3)/Decimal(4)
                ck('equation',q['id']+'_electric',abs(Decimal.from_float(hp['electric_MW'])-ideal_w)<=Decimal.from_float(math.ulp(hp['electric_MW'])))
                ck('equation',q['id']+'_evaporator',abs(Decimal.from_float(hp['source_used_MW'])-ideal_ev)<=Decimal.from_float(math.ulp(hp['source_used_MW'])))
        ledger.append(dict(id=q['id'],expected_normalized_COP=expected,component_rejected=a['rejected'],
            actual_COP=hp['cop_operating'],actual_electric_MW=hp['electric_MW'],invalid_finite_input_result=overflow))
    clockledger=[e for e in ledger if 'clock_error_h' in e]
    ck('defect','held_1024_global_clock_budget_exceeded',any(e['id']=='clock_age_1e+06_n_1024' and e['global_budget_exceeded'] for e in clockledger))
    ck('defect','changing_1024_global_clock_budget_exceeded',any(e['id']=='clock_changing_demand_n_1024' and e['global_budget_exceeded'] for e in clockledger))
    ck('defect','coarse_partition_control_within_budget',all(not e['global_budget_exceeded'] for e in clockledger if e['intervals']==1 or e['initial_age_h']==0))
    sources=folder/'source_snapshot'
    for p in sources.glob('*'):
        if not p.is_file():continue
        if p.name==Path(__file__).name:continue # original reviewer snapshot retained; final revision bound below
        current=ROOT/('audit' if p.suffix=='.py' else 'matlab/simulink')/p.name
        if not current.is_file():current=ROOT/'matlab/+dchr/+components'/p.name
        ck('artifact',p.name+'_source_binding',current.is_file() and digest(p)==digest(current))
    ck('artifact','final_reviewer_binding',digest(reviewer_snapshot/Path(__file__).name)==digest(Path(__file__)))
    ck('artifact','numeric_metadata_source_binding',digest(folder/'metadata_source/export_stateflow_numeric_metadata_v37.m')==digest(ROOT/'matlab/simulink/export_stateflow_numeric_metadata_v37.m'))
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v36.slx'
    ck('artifact','preserved_model_status_SHA',digest(model)==read(ROOT/'STATUS_stateflow_v36.json')['model_sha256'])
    with zipfile.ZipFile(model) as z:
        xml='\n'.join(z.read(n).decode('utf-8') for n in z.namelist() if n.endswith('.xml'))
        ck('archive','persistent_supervisor_additive_age','age=age+s(1)' in xml)
        ck('archive','normal_host_planner','dchr_segment_plan_v36' in xml)
    previous={}
    for pattern in ['Stateflow_manifest_v36_*.json','Stateflow_admissibility_manifest_v35_*.json','Stateflow_manifest_v34_*.json','Stateflow_fallback_manifest_v33_*.json','Stateflow_manifest_v32_*.json','TES_event_manifest_v31_*.json','Stateflow_manifest_v30_*.json','Stateflow_fault_manifest_v29_*.json']:
        for manifest in (ROOT/'audit').glob(pattern):
            for item in read(manifest)['files']:previous[item['path']]=item
    for name,item in previous.items():
        p=Path(name);p=p if p.is_absolute() else ROOT/p
        ck('preservation',name,p.is_file() and digest(p)==item['sha256'] and p.stat().st_size==item['bytes'])
    counts={k:dict(passed=sum(c['passed'] for c in v),failed=sum(not c['passed'] for c in v)) for k,v in groups.items()}
    report=dict(version='0.37',model_version='0.36',counts=counts,checks=groups,experiment_ledger=ledger,
        previous_immutable_entries=len(previous),model_sha256=digest(model),reviewer_sha256=digest(Path(__file__)),
        reviewer_snapshot=str(reviewer_snapshot.relative_to(ROOT)),original_reviewer_sha256=digest(sources/Path(__file__).name),
        conclusion='Numerical-domain defects reproduced; no corrected model acceptance',
        evidence_class='independent_algorithm_artifact_QA_not_separate_agent_or_physical_review',physical_validation=False,article_replication=False)
    out=folder/('independent_QA_v37_'+stamp+'.json')
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(counts,indent=2));print('QA='+str(out.relative_to(ROOT)))
    for k,v in groups.items():
        for c in v:
            if not c['passed']:print('FAIL='+k+':'+c['name'])
    assert not sum(c['failed'] for c in counts.values())

if __name__=='__main__':main()
