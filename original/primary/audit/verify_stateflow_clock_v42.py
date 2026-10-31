"""Independent exact-input interval timing, Decimal ODE, MAT/archive QA.

Repair acceptance needs exact-rational lower-age certification on every dwell transition.
ODE/reference/MAT/archive reviewer uses algorithms independent of the controller.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import hashlib, json, math, shutil, sys, zipfile
from fractions import Fraction
F=lambda x:Fraction.from_float(float(x))
from stateflow_reference_v34 import dispatch as baseline
ROOT=Path(__file__).resolve().parents[1]
D=lambda x:Decimal.from_float(float(x))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def matrix(v):return [] if not v else v if isinstance(v[0],list) else [v]
def objects(v):return [v] if isinstance(v,dict) else v
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def classify(hi,lo,bound,dwell):
    center=F(hi)+F(lo);lower=center-F(bound);upper=center+F(bound);target=F(dwell)
    return 'guaranteed' if lower>=target else 'premature' if upper<target else 'unresolved'

def main():
    folder=ROOT/Path(sys.argv[1]);probe_folder=ROOT/Path(sys.argv[2]);receipts=[read(ROOT/Path(p)) for p in sys.argv[3:]]
    spec=read(folder/'source_snapshot/spec/cases.json');actual=objects(read(folder/'execution_v42.json'))
    exported=objects(read(folder/'mat_audit_v42.json'));meta=read(folder/'metadata_v42.json');summary=read(folder/'summary_v42.json')
    locations={a['id']:folder for a in actual}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');snap=folder/'qa_source'/stamp;snap.mkdir(parents=True)
    shutil.copy2(__file__,snap/Path(__file__).name)
    shutil.copy2(ROOT/'audit/stateflow_reference_v34.py',snap/'stateflow_reference_v34.py')
    groups={};defects=[];transitions=[];max_residual=0.;modes=set()
    def ck(group,name,ok):groups.setdefault(group,[]).append(dict(name=name,passed=bool(ok)))
    ck('artifact','three_fresh_successful_batches',len(receipts)==3 and all(p['exit_code']==0 for p in receipts))
    ck('artifact','saved_model_execution_receipt','run_stateflow_clock_v42' in receipts[0]['command'])
    ck('artifact','independent_saved_MAT_export_receipt','export_stateflow_clock_v42' in receipts[1]['command'])
    ck('artifact','focused_cleanup_repair_rerun','run_stateflow_dwell_probes_v42' in receipts[2]['command'] and 'export_stateflow_dwell_v42' in receipts[2]['command'])
    ck('execution','cleanup_repair_no_deleted_handle_error','Invalid or deleted object' not in (ROOT/receipts[2]['log_path']).read_text(encoding='utf-8-sig',errors='replace'))
    for receipt in receipts:ck('artifact','timestamped_log_'+receipt['log_path'],(ROOT/receipt['log_path']).stat().st_size>0)
    ck('artifact','Stateflow_license_observed',meta['stateflow_license_test']==1)
    ck('artifact','six_saved_states',set(meta['thermal_state_names'])=={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'})
    ck('artifact','two_saved_supervisor_states',set(meta['supervisor_state_names'])=={'HP_OFF','HP_ON'})
    ck('execution','MATLAB_harness',summary['harness_failed']==0 and summary['harness_passed']>0)
    ck('execution','case_counts',len(actual)==len(exported)==len(spec['cases'])==summary['scenarios'])
    mats={a['id']:a for a in exported}
    with localcontext() as ctx:
        ctx.prec=120
        for case,item in zip(spec['cases'],actual):
            name=case['id'];p=case['p'];control=case['c'];clock=case['initial_clock'][:];previous_energy=case['initial_energy_MWh']
            ck('artifact',name+'_saved_MAT_binding',item==mats.get(name))
            ck('artifact',name+'_MAT_nonempty',(locations[name]/(name+'_simulation.mat')).stat().st_size>0)
            ck('execution',name+'_expected_domain',item['rejected']==case['expected_reject'])
            if item['rejected']:
                ck('execution',name+'_clock_budget_diagnostic','Clock cumulative accuracy budget exceeded' in item['error_message']);continue
            rows=matrix(item['dispatch']);segments=matrix(item['segments']);starts=matrix(item['clock_start']);ends=matrix(item['clock_end'])
            ck('execution',name+'_sample_count',len(rows)==len(case['inputs']))
            for i,y in enumerate(rows):
                ck('numeric',name+f'_{i}_initial_clock',starts[i]==clock)
                parts=[r for r in segments if r[0]==i];duration=sum(D(r[3]) for r in parts)
                ck('numeric',name+f'_{i}_partition',abs(duration-D(p[0]))<=D(1e-13))
                offset=Decimal(0)
                for k,r in enumerate(parts):
                    z=r[2:30];s=r[30:52];tag=name+f'_{i}_{k}';modes.add(int(z[0]))
                    ck('numeric',tag+'_ordered_offset',abs(D(s[13])-offset)<=D(1e-13))
                    ck('numeric',tag+'_energy_handoff',abs(z[3]-previous_energy)<1e-9)
                    ck('numeric',tag+'_TES_bounds',min(z[3:5])>=-1e-9 and max(z[3:5])<=p[1]+1e-9)
                    ck('numeric',tag+'_positive_span',z[1]>0)
                    ck('numeric',tag+'_port_bounds',min(z[5:14])>=0 and z[6]<=p[2] and z[7]<=p[3] and z[8]<=p[10] and z[6]*z[7]==0)
                    span=D(z[1]);E=D(z[3]);P=D(p[4])*D(z[6])-D(z[7])/D(p[5]);rate=D(p[6]);decay=(-rate*span).exp()
                    phi=(1-decay)/rate if rate else span;expected_E=E*decay+P*phi
                    ck('equation',tag+'_independent_ODE',abs(D(z[4])-expected_E)<=D(1e-9))
                    ck('equation',tag+'_HP_firstlaw',abs(z[10]-z[11]-z[12])<1e-12)
                    ck('equation',tag+'_service_closure',abs(case['inputs'][i][3]-sum(z[j] for j in (5,7,8,9)))<1e-12)
                    residual=E+(D(z[11])+D(z[12])+D(z[8])-D(z[19]))*span-D(z[4])-sum(D(v) for v in z[16:19]);max_residual=max(max_residual,float(abs(residual)))
                    ck('equation',tag+'_independent_firstlaw',abs(residual)<=D(1e-9))
                    if s[16] in (2,3):
                        target=control[1] if s[16]==2 else control[2]
                        category=classify(clock[1],clock[2],clock[3],target)
                        center=D(clock[1])+D(clock[2]);lower=center-D(clock[3]);upper=center+D(clock[3])
                        record=dict(case=name,sample=i,segment=k,reason=int(s[16]),offset_h=str(offset),
                            clock_before=clock,dwell_h=target,physical_age_lower_h=str(lower),physical_age_upper_h=str(upper),
                            lower_margin_h=str(lower-D(target)),classification=category)
                        transitions.append(record)
                        ck('execution',tag+'_transition_latch_direction',s[14]==(0 if s[16]==2 else 1))
                        ck('timing',tag+'_guaranteed_lower_age',category=='guaranteed')
                        if category!='guaranteed':defects.append(record)
                    changed=s[14]!=clock[0]
                    if changed:
                        ck('numeric',tag+'_reset',s[15]==s[18]==s[20]==0)
                    else:
                        ck('numeric',tag+'_clock_carry',s[15]==clock[1] and s[18]==clock[2] and s[20]==clock[3])
                    exact_center=D(s[15])+D(s[18])+span
                    reported_center=D(s[17])+D(s[19]);reported_bound=D(s[21])
                    ck('equation',tag+'_compensated_add_enclosure',abs((F(s[17])+F(s[19]))-(F(s[15])+F(s[18])+F(z[1])))+F(s[20])<=F(s[21]))
                    clock=[s[14],s[17],s[19],s[21]];previous_energy=z[4];offset+=span
                ck('numeric',name+f'_{i}_clock_output',ends[i]==clock)
            if case['kind']=='baseline':
                E=case['initial_energy_MWh'];m=case['initial_clock'][:2]
                for i,x in enumerate(case['inputs']):
                    expected,_,m=baseline(E,x,p,case['h'],m,control);E=expected[7]
                    for k,(a,b) in enumerate(zip(rows[i],expected)):
                        ck('reference',name+f'_{i}_{k}',a is None and math.isnan(b) or a is not None and abs(a-b)<=2e-9)
            if case['kind']=='event_tie':
                event_kind=1 if case['event']=='capacity' else 2
                hit=segments[0]
                z=hit[2:30];power=D(p[4])*D(z[6])-D(z[7])/D(p[5]);target=p[1] if event_kind==1 else p[7]
                independent_time=(D(target)-D(z[3]))/power
                if event_kind==2:independent_time=min(independent_time,D(control[2]))
                ck('equation',name+'_rational_or_dwell_first_time',abs(D(z[1])-independent_time)<=D(4*math.ulp(1.)))
                expected_kind=3 if event_kind==2 and case['dwell_direction']<0 else event_kind
                ck('execution',name+'_scoped_event_precedence',hit[30+12]==expected_kind or (case['event']=='cutoff' and abs(D(control[2])-Decimal(1))<=D(4*math.ulp(1.)) and hit[30+12]==2))
                # At full capacity with no direct heat/loss request, unavailable
                # HP is a documented safety override of ON dwell (reason 1).
                allowed=(1,2) if event_kind==1 else (3,)
                ck('execution',name+'_boundary_then_latch',any(r[30+16] in allowed for r in segments[1:]))
        ck('execution','six_modes_executed',modes==set(range(6)))
        for on in ('on','off'):
            for label in ('exact','uncertain_equal','uncertain_before','uncertain_after','certain_before','certain_after','negative_residual','positive_residual','low_bound'):
                relevant=[a for a in transitions if a['case']==on+'_'+label]
                ck('repair',on+'_'+label+'_certified_transition',bool(relevant) and all(a['classification']=='guaranteed' for a in relevant))
                if label in ('uncertain_equal','uncertain_before','uncertain_after','certain_before','negative_residual','low_bound'):
                    ck('repair',on+'_'+label+'_positive_wait',bool(relevant) and Decimal(relevant[0]['offset_h'])>0)
            ck('repair',on+'_persistent_bound',any(a['case']==on+'_persistent_wait' and a['classification']=='guaranteed' for a in transitions))
        # Reviewer self-checks are synthetic and explicitly outside actual evidence counts.
        ck('synthetic','interval_before',classify(.5,0.,1e-9,1.)=='premature')
        ck('synthetic','interval_equal_uncertain',classify(1.,0.,1e-9,1.)=='unresolved')
        ck('synthetic','interval_after',classify(2.,0.,1e-9,1.)=='guaranteed')
        ck('synthetic','small_positive_bound',classify(1.,0.,math.ldexp(1.,-80),1.)=='unresolved')
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'
    ck('artifact','model_snapshot',digest(model)==digest(folder/'source_snapshot'/model.name))
    for name in ('build_dispatch_stateflow','dchr_segment_plan','dchr_stateflow_hp','stateflow_allocate','stateflow_choose_mode','stateflow_collect','stateflow_clock_add','stateflow_supervisor_guard','stateflow_contract_gate','stateflow_dwell_ready','stateflow_dwell_wait','run_stateflow_clock','run_stateflow_faults'):
        filename=name+'_v42.m'
        ck('artifact','executed_source_'+filename,digest(ROOT/'matlab/simulink'/filename)==digest(folder/'source_snapshot'/filename))
    ck('artifact','retained_verified_HP_component',digest(ROOT/'matlab/+dchr/+components/heat_pump_step_v40.m')==digest(folder/'source_snapshot/heat_pump_step_v40.m'))
    ck('artifact','saved_MAT_export_source',digest(ROOT/'matlab/simulink/export_stateflow_clock_v42.m')==digest(folder/'mat_audit_source/export_stateflow_clock_v42.m'))
    ck('artifact','probe_attack_source',digest(ROOT/'matlab/simulink/run_stateflow_dwell_probes_v42.m')==digest(probe_folder/'dwell_probe_source/run_stateflow_dwell_probes_v42.m'))
    ck('artifact','focused_attack_export_source',digest(ROOT/'matlab/simulink/export_stateflow_dwell_v42.m')==digest(probe_folder/'mat_audit_source/export_stateflow_dwell_v42.m'))
    with zipfile.ZipFile(model) as archive:
        ck('artifact','SLX_integrity',archive.testzip() is None)
        source='\n'.join(archive.read(n).decode('utf-8',errors='replace') for n in archive.namelist() if n.endswith('.xml'))
        ck('artifact','saved_supervisor_guard_present','stateflow_supervisor_guard_v42' in source)
        ck('artifact','saved_lower_enclosure_guard','stateflow_dwell_ready_v42(age,low,bound' in source)
        ck('artifact','saved_transition_receives_bound','s,p,c,age,low,bound)' in source)
    preserve=read(folder/'source_snapshot/spec/preservation.json')['files']
    for f in preserve:
        path=ROOT/f['path'];ck('preservation',f['path'],path.is_file() and path.stat().st_size==f['bytes'] and digest(path)==f['sha256'])
    for name in ('Stateflow_HP_manifest_v40_20261010T124921_176639Z.json','Stateflow_HP_postclose_manifest_v40_20261010T124954_227715Z.json','Stateflow_clock_manifest_v41_20261010T130037_509896Z.json','Stateflow_clock_postclose_manifest_v41_20261010T130105_075393Z.json'):
        for f in read(ROOT/'audit'/name)['files']:
            path=ROOT/f['path'];ck('preservation','sealed40_'+f['path'],path.stat().st_size==f['bytes'] and digest(path)==f['sha256'])
    faults=read(folder/'faults_v42.json');fault_mats={a['id']:a for a in read(folder/'fault_mat_audit_v42.json')}
    ck('execution','thirty_actual_faults',len(faults)==30 and all(f['rejected'] for f in faults))
    for f in faults:
        actual_mat=fault_mats.get(f['id'],{})
        ck('artifact',f['id']+'_fault_MAT_binding',all(f.get(k)==actual_mat.get(k) for k in ('id','error_message','phase','time_h')))
        ck('execution',f['id']+'_actual_execution_rejection',f['rejected'] and f['phase']=='Execution' and bool(f['error_message']))
    probes=read(probe_folder/'dwell_probes_v42.json')['probes'];probe_spec=read(probe_folder/'dwell_probe_source/spec.json')['probes']
    ck('artifact','executed_function_probe_count',len(probes)==len(probe_spec)==1016)
    for k,(row,inputs) in enumerate(zip(probes,probe_spec)):
        hi,lo,bound,dwell,ready,margin,wait,H,L,B=row;exact=F(hi)+F(lo)-F(bound)-F(dwell)
        ck('function_probe',f'{k}_input_binding',row[:4]==inputs)
        ck('function_probe',f'{k}_outward_lower_margin',F(margin)<=exact)
        ck('function_probe',f'{k}_no_false_ready',not ready or exact>=0)
        ck('function_probe',f'{k}_certified_wait',wait>=0 and F(H)+F(L)-F(B)>=F(dwell))
        ck('function_probe',f'{k}_clock_enclosure',abs(F(H)+F(L)-(F(hi)+F(lo)+F(wait)))+F(bound)<=F(B))
        ck('function_probe',f'{k}_positive_unready_wait',bool(ready) or wait>0)
    attacks=read(probe_folder/'uncertainty_attacks_v42.json');attack_mats={a['id']:a for a in read(probe_folder/'attack_mat_audit_v42.json')}
    ck('execution','four_actual_uncertainty_attacks',len(attacks)==4)
    for a in attacks:
        ck('execution',a['id']+'_saved_gate_rejection',a['passed'] and a['phase']=='Execution' and a['time_h']==a['expected_time_h'] and a['expected_component'] in a['error_message'])
        ck('artifact',a['id']+'_saved_attack_MAT_binding',all(a.get(k)==attack_mats.get(a['id'],{}).get(k) for k in ('id','error_message','phase','time_h')))
    totals={g:dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)) for g,checks in groups.items()}
    report=dict(version='0.42',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_version='0.42',new_model=True,
        summary=summary,probe_directory=probe_folder.relative_to(ROOT).as_posix(),
        qa_passed=sum(v['passed'] for g,v in totals.items() if g!='synthetic'),qa_failed=sum(v['failed'] for g,v in totals.items() if g!='synthetic'),
        synthetic=totals['synthetic'],breakdown=totals,unresolved_transitions=sum(a['classification']=='unresolved' for a in defects),
        certainly_premature_transitions=sum(a['classification']=='premature' for a in defects),defect_status='REPAIRED_IN_TESTED_FIXTURES',
        max_balance_residual_MWh=max_residual,defects=defects,all_dwell_transitions=transitions,checks=groups)
    path=folder/('independent_QA_v42_'+stamp+'.json');path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('qa_passed','qa_failed','synthetic','unresolved_transitions','certainly_premature_transitions','max_balance_residual_MWh')}))
    print('QA='+path.relative_to(ROOT).as_posix())
    if report['qa_failed'] or totals['synthetic']['failed'] or defects:sys.exit(1)
if __name__=='__main__':main()
