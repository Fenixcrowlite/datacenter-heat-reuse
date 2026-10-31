"""Independent exact-input interval timing, Decimal ODE, MAT/archive QA.

QA pass verifies an audit's evidence, not repaired dwell acceptance.
Unresolved interval transitions are a separate implementation defect ledger.
"""
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path
import hashlib, json, math, shutil, sys, zipfile
from stateflow_reference_v34 import dispatch as baseline
ROOT=Path(__file__).resolve().parents[1]
D=lambda x:Decimal.from_float(float(x))
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def matrix(v):return [] if not v else v if isinstance(v[0],list) else [v]
def objects(v):return [v] if isinstance(v,dict) else v
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def classify(hi,lo,bound,dwell):
    center=D(hi)+D(lo);lower=center-D(bound);upper=center+D(bound);target=D(dwell)
    return 'guaranteed' if lower>=target else 'premature' if upper<target else 'unresolved'

def main():
    folder=ROOT/Path(sys.argv[1]);supplement=ROOT/Path(sys.argv[2]);receipts=[read(ROOT/Path(p)) for p in sys.argv[3:]]
    spec=read(folder/'source_snapshot/spec/cases.json');actual=objects(read(folder/'execution_v41.json'))
    exported=objects(read(folder/'mat_audit_v41.json'));meta=read(folder/'metadata_v41.json');summary=read(folder/'summary_v41.json')
    supplementary_spec=read(supplement/'source_snapshot/spec/cases.json')
    supplementary_actual=objects(read(supplement/'execution_v41.json'));supplementary_export=objects(read(supplement/'mat_audit_v41.json'))
    supplementary_summary=read(supplement/'summary_v41.json')
    assert supplementary_spec['supplement_for']==folder.relative_to(ROOT).as_posix()
    locations={a['id']:folder for a in actual}
    locations.update({a['id']:supplement for a in supplementary_actual})
    spec['cases']+=supplementary_spec['cases'];actual+=supplementary_actual;exported+=supplementary_export
    for key in ('scenarios','completed_scenarios','intervals','positive_segments','harness_passed','harness_failed'):
        summary[key]+=supplementary_summary[key]
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ');snap=folder/'qa_source'/stamp;snap.mkdir(parents=True)
    shutil.copy2(__file__,snap/Path(__file__).name)
    shutil.copy2(ROOT/'audit/stateflow_reference_v34.py',snap/'stateflow_reference_v34.py')
    groups={};defects=[];transitions=[];max_residual=0.;modes=set()
    def ck(group,name,ok):groups.setdefault(group,[]).append(dict(name=name,passed=bool(ok)))
    ck('artifact','four_fresh_successful_batches',len(receipts)==4 and all(p['exit_code']==0 for p in receipts))
    ck('artifact','saved_model_execution_receipt','run_stateflow_clock_v41' in receipts[0]['command'])
    ck('artifact','independent_saved_MAT_export_receipt','export_stateflow_clock_v41' in receipts[1]['command'])
    ck('artifact','targeted_supplement_execution','run_stateflow_clock_v41' in receipts[2]['command'])
    ck('artifact','supplement_saved_MAT_export','export_stateflow_clock_v41' in receipts[3]['command'])
    for receipt in receipts:ck('artifact','timestamped_log_'+receipt['log_path'],(ROOT/receipt['log_path']).stat().st_size>0)
    ck('artifact','Stateflow_license_observed',meta['stateflow_license_test']==1)
    supplementary_meta=read(supplement/'metadata_v41.json')
    ck('artifact','supplement_Stateflow_license',supplementary_meta['stateflow_license_test']==1)
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
                        if category!='guaranteed':defects.append(record)
                    changed=s[14]!=clock[0]
                    if changed:
                        ck('numeric',tag+'_reset',s[15]==s[18]==s[20]==0)
                    else:
                        ck('numeric',tag+'_clock_carry',s[15]==clock[1] and s[18]==clock[2] and s[20]==clock[3])
                    exact_center=D(s[15])+D(s[18])+span
                    reported_center=D(s[17])+D(s[19]);reported_bound=D(s[21])
                    ck('equation',tag+'_compensated_add_enclosure',abs(reported_center-exact_center)+D(s[20])<=reported_bound)
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
                ck('execution',name+'_event_precedence',hit[30+12]==expected_kind)
                # At full capacity with no direct heat/loss request, unavailable
                # HP is a documented safety override of ON dwell (reason 1).
                allowed=(1,2) if event_kind==1 else (3,)
                ck('execution',name+'_boundary_then_latch',any(r[30+16] in allowed for r in segments[1:]))
        ck('execution','six_modes_executed',modes==set(range(6)))
        for on in ('on','off'):
            for label in ('uncertain_equal','uncertain_before','uncertain_after','low_bound'):
                ck('defect_reproduction',on+'_'+label+'_unresolved',any(a['case']==on+'_'+label and a['classification']=='unresolved' for a in defects))
            for label in ('exact','certain_after','negative_residual','positive_residual'):
                ck('controls',on+'_'+label+'_guaranteed',all(a['classification']=='guaranteed' for a in transitions if a['case']==on+'_'+label) and any(a['case']==on+'_'+label for a in transitions))
        # Reviewer self-checks are synthetic and explicitly outside actual evidence counts.
        ck('synthetic','interval_before',classify(.5,0.,1e-9,1.)=='premature')
        ck('synthetic','interval_equal_uncertain',classify(1.,0.,1e-9,1.)=='unresolved')
        ck('synthetic','interval_after',classify(2.,0.,1e-9,1.)=='guaranteed')
        ck('synthetic','small_positive_bound',classify(1.,0.,math.ldexp(1.,-80),1.)=='unresolved')
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx'
    ck('artifact','model_snapshot',digest(model)==digest(folder/'source_snapshot'/model.name))
    ck('artifact','supplement_model_snapshot',digest(model)==digest(supplement/'source_snapshot'/model.name))
    with zipfile.ZipFile(model) as archive:
        ck('artifact','SLX_integrity',archive.testzip() is None)
        source='\n'.join(archive.read(n).decode('utf-8',errors='replace') for n in archive.namelist() if n.endswith('.xml'))
        ck('artifact','saved_supervisor_guard_present','stateflow_supervisor_guard_v40' in source)
    preserve=read(folder/'source_snapshot/spec/preservation.json')['files']
    for f in preserve:
        path=ROOT/f['path'];ck('preservation',f['path'],path.is_file() and path.stat().st_size==f['bytes'] and digest(path)==f['sha256'])
    for name in ('Stateflow_HP_manifest_v40_20261010T124921_176639Z.json','Stateflow_HP_postclose_manifest_v40_20261010T124954_227715Z.json'):
        for f in read(ROOT/'audit'/name)['files']:
            path=ROOT/f['path'];ck('preservation','sealed40_'+f['path'],path.stat().st_size==f['bytes'] and digest(path)==f['sha256'])
    totals={g:dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)) for g,checks in groups.items()}
    report=dict(version='0.41',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_version='0.40',new_model=False,
        summary=summary,supplement_directory=supplement.relative_to(ROOT).as_posix(),
        qa_passed=sum(v['passed'] for g,v in totals.items() if g!='synthetic'),qa_failed=sum(v['failed'] for g,v in totals.items() if g!='synthetic'),
        synthetic=totals['synthetic'],breakdown=totals,unresolved_transitions=sum(a['classification']=='unresolved' for a in defects),
        certainly_premature_transitions=sum(a['classification']=='premature' for a in defects),defect_status='OPEN_UNCERTAINTY_DWELL_GUARD',
        max_balance_residual_MWh=max_residual,defects=defects,all_dwell_transitions=transitions,checks=groups)
    path=folder/('independent_QA_v41_'+stamp+'.json');path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('qa_passed','qa_failed','synthetic','unresolved_transitions','certainly_premature_transitions','max_balance_residual_MWh')}))
    print('QA='+path.relative_to(ROOT).as_posix())
    if report['qa_failed'] or totals['synthetic']['failed']:sys.exit(1)
if __name__=='__main__':main()
