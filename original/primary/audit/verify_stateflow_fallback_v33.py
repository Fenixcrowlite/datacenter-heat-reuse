"""Independent algorithm/artifact QA of targeted saved-v32 executions.

No MATLAB production imports. Separate agent/human review and physical validation
are not claimed. Generic oracle plus distinct targeted recurrence and MAT binding.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import re
import shutil
from stateflow_fallback_v33 import ROOT, stamp, sha, save, csvsave, pulse_recurrence
from stateflow_reference_v32 import PORTS, HP, SEG
from verify_stateflow_completion_v32 import numeric, structure, readcsv, near, matrix, vector

def targeted(rows,segments,cases):
    checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    for c in cases:
        rr=[r for r in rows if r['scenario_id']==c['id']]
        e=c['initial_energy_MWh'];dt=c['p'][0]
        for i,r in enumerate(rr):
            label=f'{c["id"]}_{i}'
            if c['family']=='unavailable_tail':
                e,on,off=pulse_recurrence(e,dt)
                ck(label+'_alternate_endpoint',near(r['Storage_E_Next_MWh'],e))
                ck(label+'_alternate_electric',near(float(r['HP_Electric_MW'])*dt,6/3.7*on))
                ck(label+'_alternate_unmet',near(float(r['Unmet_Heat_MW'])*dt,2.5*off))
                ss=[s for s in segments if s['scenario_id']==c['id'] and int(s['step'])==i]
                if off>1e-10:
                    tail=ss[1]
                    ck(label+'_unused_TES_in_tail',float(tail['Energy_Start_MWh'])>5 and
                        float(tail['Storage_Discharge_MW'])==0 and float(tail['Unmet_Heat_MW'])==2.5)
            elif c['family'] in ('source_limited_initial_capacity','passive_capacity'):
                eq=6. if c['family'].startswith('source') else 0.
                e=eq+(e-eq)*math.exp(-.1*dt)
                ck(label+'_alternate_endpoint',near(r['Storage_E_Next_MWh'],e))
                ck(label+'_no_reachable_capacity_event',all(float(s['Event_Kind'])==0 for s in segments
                    if s['scenario_id']==c['id'] and int(s['step'])==i))
            elif c['family']=='feasible_hold':
                # Initial top-up always reaches capacity within smallest fixture step.
                ck(label+'_capacity_held',near(r['Storage_E_Next_MWh'],10.))
                ck(label+'_no_unmet',float(r['Unmet_Heat_MW'])==0.)
        if c['family']=='unavailable_initial_capacity':
            first=next(s for s in segments if s['scenario_id']==c['id'] and int(s['step'])==0 and int(s['segment'])==1)
            ck(c['id']+'_initial_capacity_discharges',float(first['Storage_Discharge_MW'])==3 and float(first['HP_Heat_MW'])==0)
    return checks

def review(folder,receipt):
    folder=folder.resolve();receipt=receipt.resolve()
    qa_source=folder/('qa_source_'+stamp());qa_source.mkdir()
    for name in ('verify_stateflow_fallback_v33.py','verify_stateflow_completion_v32.py',
                 'stateflow_fallback_v33.py','stateflow_reference_v32.py',
                 'stateflow_reference_v30.py','TES_event_reference_v31.py'):
        shutil.copy2(ROOT/'audit'/name,qa_source/name)
    snap=folder/'source_snapshot';spec=json.loads((snap/'spec/cases.json').read_text());cases=spec['cases']
    rows=readcsv(folder/'stateflow_trace_v33.csv');segments=readcsv(folder/'stateflow_segments_v33.csv')
    # The targeted sweep does not repeat six-mode acceptance; that remains v32.
    generic=[c for c in numeric(rows,segments,cases) if c['name']!='all_six_positive_duration_modes']
    specific=targeted(rows,segments,cases)
    static=structure(snap/'DCHR_Dispatch_Stateflow_v32.slx',snap)
    artifacts=[]
    def ck(name,ok):artifacts.append(dict(name=name,passed=bool(ok)))
    s=json.loads((folder/'summary_v33.json').read_text());rc=json.loads(receipt.read_text(encoding='utf-8-sig'))
    log=(ROOT/rc['log_path']).read_text(encoding='utf-8-sig',errors='replace')
    ck('batch_zero_exit',rc['exit_code']==0)
    ck('batch_result_binding','FALLBACK_OUTPUT='+str(folder.resolve()) in log)
    match=re.fullmatch(r"addpath\('matlab/simulink'\); run_stateflow_fallback_v33\('([^']+)'\)",rc['command'])
    original=(ROOT/match.group(1)).resolve() if match else ROOT/'invalid_spec'
    expected={p.relative_to(snap/'spec').as_posix():sha(p) for p in (snap/'spec').rglob('*') if p.is_file()}
    actual={p.relative_to(original).as_posix():sha(p) for p in original.rglob('*') if p.is_file()}
    ck('batch_spec_binding',bool(match) and bool(expected) and expected==actual and original.is_relative_to(ROOT))
    ck('summary_counts',s['scenarios']==len(cases) and s['intervals']==len(rows) and s['segments']==len(segments) and s['failed']==0)
    ck('observed_stateflow',s['stateflow_license_observed']==1 and 'R2026a' in s['matlab_version'])
    aa=readcsv(folder/'assertions_v33.csv')
    ck('MATLAB_assertions',len(aa)==s['passed'] and all(r['passed'].lower() in ('true','1') for r in aa))
    mat=json.loads((folder/'mat_audit_v33.json').read_text())
    ck('MAT_complete_case_order',[v['id'] for v in mat['valid_cases']]==[c['id'] for c in cases])
    for c,m in zip(cases,mat['valid_cases']):
        rr=[r for r in rows if r['scenario_id']==c['id']];ss=[r for r in segments if r['scenario_id']==c['id']]
        ys=matrix(m['y'],25);zs=matrix(m['segments'],50)
        ck(c['id']+'_MAT_exists',(folder/(c['id']+'_simulation.mat')).stat().st_size>1024)
        ck(c['id']+'_MAT_complete',m['error_message']=='' and len(ys)==len(rr)==len(zs))
        for i,(r,y,z) in enumerate(zip(rr,ys,zs)):
            for key,value in zip(PORTS+HP,y):ck(f'{c["id"]}_{i}_MAT_{key}',near(r[key],value))
            for k in range(2):
                for key,value in zip(SEG,z[k*25:(k+1)*25]):ck(f'{c["id"]}_{i}_{k}_MAT_{key}',near(ss[2*i+k][key],value))
            ck(f'{c["id"]}_{i}_MAT_time',near(r['Time_h'],vector(m['time_h'])[i]))
            ck(f'{c["id"]}_{i}_MAT_memory',near(r['Storage_E_Start_MWh'],vector(m['energy_start'])[i]))
    for source in snap.glob('*'):
        # Reviewer was repaired after MATLAB took its pre-review snapshot. That
        # original stays untouched; exact executed reviewer is bound separately.
        if source.name=='verify_stateflow_fallback_v33.py':continue
        if source.suffix=='.m':matches=list((ROOT/'matlab').rglob(source.name))
        elif source.suffix=='.py':matches=[ROOT/'audit'/source.name]
        elif source.suffix=='.slx':matches=[ROOT/'matlab/simulink'/source.name]
        else:continue
        ck('source_binding_'+source.name,len(matches)==1 and sha(source)==sha(matches[0]))
    for source in qa_source.glob('*.py'):ck('executed_reviewer_binding_'+source.name,sha(source)==sha(ROOT/'audit'/source.name))
    prior=json.loads((snap/'spec/preservation.json').read_text())
    for item in prior:
        path=ROOT/item['path'];ck('preserved_'+item['path'],path.exists() and path.stat().st_size==item['bytes'] and sha(path)==item['sha256'])
    eq=json.loads((snap/'spec/equation_qa.json').read_text())
    ck('equation_report',eq['failed']==0 and eq['passed']==len(eq['checks']) and all(c['passed'] for c in eq['checks']))
    synthetic=[]
    for key in ('Storage_E_Next_MWh','HP_Electric_MW','Unmet_Heat_MW'):
        bad=copy.deepcopy(rows);bad[0][key]=float(bad[0][key])+1
        synthetic.append(dict(name='reject_'+key,passed=any(not c['passed'] for c in targeted(bad,segments,cases))))
    summary=[]
    for c in cases:
        rr=[r for r in rows if r['scenario_id']==c['id']];ss=[r for r in segments if r['scenario_id']==c['id'] and float(r['Duration_h'])>0]
        states=[int(float(r['HP_Available'])) for r in ss]
        summary.append(dict(scenario_id=c['id'],family=c['family'],dt_h=c['p'][0],horizon_h=len(rr)*c['p'][0],
            endpoint_MWh=float(rr[-1]['Storage_E_Next_MWh']),
            HP_on_h=sum(float(r['Duration_h']) for r in ss if float(r['HP_Available'])==1),
            HP_off_h=sum(float(r['Duration_h']) for r in ss if float(r['HP_Available'])==0),
            HP_state_changes=sum(a!=b for a,b in zip(states,states[1:])),
            electric_MWh=sum(float(r['HP_Electric_MW'])*c['p'][0] for r in rr),
            unmet_MWh=sum(float(r['Unmet_Heat_MW'])*c['p'][0] for r in rr),
            boiler_MWh=sum(float(r['Gas_Heat_MW'])*c['p'][0] for r in rr),
            TES_discharge_MWh=sum(float(r['Storage_Discharge_MW'])*c['p'][0] for r in rr)))
    sensitivity=folder/'fallback_sensitivity_v33.csv'
    if sensitivity.exists():
        previous=readcsv(sensitivity)
        ck('preserved_identical_sensitivity',previous==[{k:str(v) for k,v in r.items()} for r in summary])
    else:csvsave(sensitivity,summary)
    groups=dict(actual_generic_oracle=generic,alternate_targeted_recurrence=specific,
        static_saved_model=static,artifact_runtime_preservation=artifacts,synthetic_reviewer_checks=synthetic)
    report=dict(timestamp_utc=stamp(),result_directory=str(folder.relative_to(ROOT)),receipt=str(receipt.relative_to(ROOT)),
        model_sha256=sha(snap/'DCHR_Dispatch_Stateflow_v32.slx'),qa_source_directory=str(qa_source.relative_to(ROOT)),
        categories={k:dict(passed=sum(c['passed'] for c in v),failed=sum(not c['passed'] for c in v)) for k,v in groups.items()},
        failed=sum(not c['passed'] for v in groups.values() for c in v),checks=groups,previous_entries_preserved=len(prior),
        equation_checks_passed=eq['passed'],separate_agent_or_human_review=False,physical_validation=False,article_replication=False)
    path=ROOT/'audit'/f'Stateflow_fallback_QA_v33_{stamp()}.json';save(path,report)
    print(json.dumps(dict(report=str(path.relative_to(ROOT)),categories=report['categories'],failed=report['failed'])))
    for v in groups.values():
        for c in v:
            if not c['passed']:print('FAIL',c['name'])
    return int(report['failed']>0)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);p.add_argument('receipt',type=Path);a=p.parse_args()
    raise SystemExit(review(a.folder,a.receipt))
