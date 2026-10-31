"""Independent review of actual event MATLAB, saved SLX and MAT/CSV evidence."""
import argparse
import copy
import csv
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
from TES_event_reference_v31 import event_tank, service, NAMES, component_cases, comparison_cases
from stateflow_reference_v30 import dispatch, PORTS, HP
from verify_stateflow_v30 import structure_checks

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def readcsv(path):
    with path.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def near(a,b):
    a,b=float(a),float(b)
    return (math.isnan(a) and math.isnan(b)) or (math.isfinite(a) and math.isfinite(b) and abs(a-b)<=2e-9+2e-11*abs(b))

def component_checks(rows,cases):
    checks=[]
    def ck(n,ok):checks.append(dict(name=n,passed=bool(ok)))
    ck('component_exact_ids',[r['id'] for r in rows]==[c['id'] for c in cases])
    for row,case in zip(rows,cases):
        expected=event_tank(case['a'],case['charge'],case['discharge'],case['p'])
        for n,v in zip(NAMES,expected):ck(case['id']+':'+n,near(row[n],v))
        balance=case['a']+float(row['charge_MWh'])-float(row['discharge_MWh'])-float(row['next_MWh'])
        ck(case['id']+':external_first_law',abs(balance-sum(float(row[n]) for n in NAMES[4:7]))<2e-9)
    return checks

def saved_trace_checks(rows,cases):
    checks=[]
    def ck(n,ok):checks.append(dict(name=n,passed=bool(ok)))
    expected_ids=[(c['id'],i*c['p'][0]) for c in cases for i in range(len(c['inputs']))]
    ck('v30_exact_ordered_rows',[(r['scenario_id'],float(r['Time_h'])) for r in rows]==expected_ids)
    modes=set()
    for c in cases:
        a=c['initial_energy_MWh'];group=[r for r in rows if r['scenario_id']==c['id']]
        ck(c['id']+':complete',len(group)==len(c['inputs']))
        for i,(row,x) in enumerate(zip(group,c['inputs'])):
            y,u=dispatch(a,x,c['p'],c['h']);prefix=f"{c['id']}:{i}:"
            for n,v in zip(PORTS+HP,y+u):ck(prefix+n,near(row[n],v))
            ck(prefix+'start_MWh',near(row['Storage_E_Start_MWh'],a))
            ck(prefix+'actual_first_law',abs(float(row['System_Balance_Residual_MWh']))<2e-9)
            a=y[7];modes.add(int(float(row['Mode'])))
    ck('all_six_actual_saved_modes',modes==set(range(6)))
    return checks

def event_checks(rows,cases):
    checks=[];totals={}
    def ck(n,ok):checks.append(dict(name=n,passed=bool(ok)))
    ck('event_exact_ordered_rows',[(r['scenario_id'],float(r['Time_h'])) for r in rows]==
       [(c['id'],i*c['p'][0]) for c in cases for i in range(len(c['inputs']))])
    for c in cases:
        a=c['initial_energy_MWh'];p=c['p'];dt=p[0];group=[r for r in rows if r['scenario_id']==c['id']]
        totals[c['id']]=dict(charge=0.,discharge=0.,gas=0.,unmet=0.,standing=0.,endpoint=None)
        ck(c['id']+':complete_event_rows',len(group)==len(c['inputs']))
        for i,row in enumerate(group):
            z=event_tank(a,c['charge_request_MW'],c['discharge_request_MW'],p)
            prefix=f"{c['id']}:{i}:"
            for n,v in zip(NAMES,z):ck(prefix+n,near(row[n],v))
            gas,unmet=service(z,dt,c['inputs'][i][3]-c['hp_direct_MW'],p[10])
            ck(prefix+'segment_gas',near(row['gas_MWh'],gas));ck(prefix+'segment_unmet',near(row['unmet_MWh'],unmet))
            ck(prefix+'memory',near(row['start_MWh'],a))
            ce=float(row['charge_MWh']);de=float(row['discharge_MWh']);end=float(row['next_MWh'])
            ck(prefix+'actual_external_first_law',abs(a+ce-de-end-sum(float(row[n]) for n in NAMES[4:7]))<2e-9)
            ck(prefix+'actual_demand_closure',abs(de+float(row['gas_MWh'])+float(row['unmet_MWh'])+
               dt*c['hp_direct_MW']-dt*c['inputs'][i][3])<2e-9)
            # Actual segment commands, rather than average powers, drive bounds.
            event_time=float(row['event_time_h']);fullp=p[4]*float(row['full_charge_MW'])-float(row['full_discharge_MW'])/p[5]
            tailp=p[4]*float(row['tail_charge_MW'])-float(row['tail_discharge_MW'])/p[5]
            for point in range(17):
                t=point*dt/16
                if t<=event_time:start=a;span=t;power=fullp;dis=float(row['full_discharge_MW'])
                else:start=float(row['event_energy_MWh']);span=t-event_time;power=tailp;dis=float(row['tail_discharge_MW'])
                phi=span if p[6]==0 else -math.expm1(-p[6]*span)/p[6]
                state=start*math.exp(-p[6]*span)+power*phi
                ck(prefix+f'actual_piecewise_bound_{point}',-2e-9<=state<=p[1]+2e-9 and (dis==0 or state>=p[7]-2e-9))
            total=totals[c['id']]
            for key,v in [('charge',z[18]),('discharge',z[19]),('gas',gas),('unmet',unmet),('standing',z[4])]:total[key]+=v
            a=z[3];total['endpoint']=a
    return checks,totals

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('result_directory',type=Path);ap.add_argument('receipt',type=Path)
    args=ap.parse_args();folder=args.result_directory.resolve();snap=folder/'source_snapshot'
    spec=json.loads((snap/'spec/cases.json').read_text());cases=spec['comparison_cases'];components=spec['component_cases']
    actual=component_checks(readcsv(folder/'component_trace_v31.csv'),components)
    saved=readcsv(folder/'saved_v30_trace.csv');actual+=saved_trace_checks(saved,cases)
    events=readcsv(folder/'event_trace_v31.csv');event_numeric,totals=event_checks(events,cases);actual+=event_numeric
    static=structure_checks(snap/'DCHR_Dispatch_Stateflow_v30.slx',snap)
    evidence=[]
    def ck(n,ok):evidence.append(dict(name=n,passed=bool(ok)))
    ck('independent_spec_cases',components==component_cases() and cases==comparison_cases())
    for path in snap.glob('*.m'):
        matches=list((ROOT/'matlab').rglob(path.name));ck('executed_source_'+path.name,len(matches)==1 and digest(path)==digest(matches[0]))
    for name in ['TES_event_reference_v31.py','stateflow_reference_v30.py']:
        ck('oracle_snapshot_'+name,digest(snap/name)==digest(ROOT/'audit'/name))
    exporter='export_TES_event_mat_audit_v31.m'
    ck('MAT_exporter_source',digest(folder/'mat_audit_source'/exporter)==digest(ROOT/'matlab/simulink'/exporter))
    ck('saved_model_binding',digest(snap/'DCHR_Dispatch_Stateflow_v30.slx')==digest(ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v30.slx'))
    eq=json.loads((snap/'spec/equation_qa.json').read_text())
    ck('independent_equation_receipt',eq['failed']==0 and eq['passed']==len(eq['checks'])==566 and
       all(c['passed'] for c in eq['checks']) and eq['oracle_sha256']==digest(ROOT/'audit/TES_event_reference_v31.py'))
    assertions=readcsv(folder/'assertions_v31.csv');summary=json.loads((folder/'summary_v31.json').read_text())
    ck('MATLAB_assertion_counts',summary['failed']==0 and summary['checks']==summary['passed']==len(assertions) and all(r['passed']=='1' for r in assertions))
    ck('MATLAB_declared_coverage',summary['saved_model_scenarios']==len(cases)==50 and summary['saved_model_intervals']==len(saved)==310 and summary['component_cases']==len(components)==141)
    ck('honest_model_release',summary['model_release']=='0.30' and summary['new_stateflow_model'] is False and summary['event_component_embedded_in_stateflow'] is False and summary['physical_validation'] is False and summary['article_replication'] is False)
    domains=json.loads((folder/'component_domain_v31.json').read_text())
    ck('component_domain_cases',[d['id'] for d in domains]==['negative_state','above_capacity_state','nan_state','infinite_request','simultaneous_ports','zero_interval','negative_loss_rate','cutoff_above_capacity','zero_efficiency','zero_heat_capacity','negative_limit','negative_request'])
    for d in domains:ck('actual_component_domain_'+d['id'],d['passed'] and d['identifier']=='DCHR:v31:Domain' and bool(d['diagnostic']))
    runtime=json.loads((folder/'mat_audit_v31.json').read_text())['cases']
    ck('MAT_case_coverage',[r['id'] for r in runtime]==[c['id'] for c in cases])
    for c,m in zip(cases,runtime):
        path=folder/(c['id']+'_simulation.mat');ck(c['id']+':saved_MAT',path.is_file() and path.stat().st_size>1024)
        ck(c['id']+':clean_simulation',m['error_message']=='' and m['stop_event']=='ReachedStopTime')
        group=[r for r in saved if r['scenario_id']==c['id']];n=len(group)
        ys,us,starts,times=m['y'],m['u'],m['energy_start'],m['time_h']
        if n==1:ys,us,starts,times=[ys],[us],[starts],[times]
        ck(c['id']+':MAT_shapes',len(ys)==len(us)==len(starts)==len(times)==n and all(len(y)==17 for y in ys) and all(len(u)==8 for u in us))
        for i,(row,y,u,a,t) in enumerate(zip(group,ys,us,starts,times)):
            for name,v in zip(PORTS+HP+['Storage_E_Start_MWh','Time_h'],y+u+[a,t]):
                ck(f"{c['id']}:{i}:MAT_{name}",near(row[name],math.nan if v is None else v))
    comparisons=readcsv(folder/'policy_comparison_v31.csv');ck('comparison_ids',[r['scenario_id'] for r in comparisons]==[c['id'] for c in cases])
    for c,row in zip(cases,comparisons):
        group=[r for r in saved if r['scenario_id']==c['id']];dt=c['p'][0]
        for key,source in [('charge','Storage_Charge_MW'),('discharge','Storage_Discharge_MW'),('gas','Gas_Heat_MW'),('unmet','Unmet_Heat_MW'),('standing','Storage_Standing_Loss_MWh')]:
            expected=sum(float(r[source]) for r in group)*(1. if key=='standing' else dt)
            ck(c['id']+':comparison_v30_'+key,near(row[f'v30_{key}_MWh'],expected))
        ck(c['id']+':comparison_v30_endpoint',near(row['v30_endpoint_MWh'],group[-1]['Storage_E_Next_MWh']))
        for key,v in totals[c['id']].items():ck(c['id']+':comparison_event_'+key,near(row[f'event_{key}_MWh'],v))
    for family in sorted({c['family'] for c in cases}):
        group=[r for r in comparisons if r['family']==family]
        ck(family+':five_timesteps',[float(r['dt_h']) for r in group]==[2.,1.,.5,.25,.125])
        for key in ['charge','discharge','gas','unmet','endpoint','standing']:
            values=[float(r[f'event_{key}_MWh']) for r in group]
            ck(family+':event_partition_'+key,max(values)-min(values)<2e-9)
    receipt=json.loads(args.receipt.read_text(encoding='utf-8-sig'));log=ROOT/receipt['log_path']
    logtext=log.read_text(encoding='utf-8-sig',errors='replace')
    ck('observed_zero_batch_exit',receipt['exit_code']==0 and 'EXIT_CODE=0' in logtext)
    ck('exact_completed_result_directory',str(folder) in logtext and 'TES_EVENT_OUTPUT=' in logtext and 'MAT_AUDIT_OUTPUT=' in logtext)
    # All immutable files from both accepted previous checkpoints are preserved.
    preservation=0
    for manifest_name in ['Stateflow_manifest_v30_20261009T213038_443584Z.json','Stateflow_fault_manifest_v29_20261009T204014_224631Z.json']:
        manifest=json.loads((ROOT/'audit'/manifest_name).read_text())
        for item in manifest['files']:
            path=ROOT/item['path'];ok=path.is_file() and path.stat().st_size==item['bytes'] and digest(path)==item['sha256']
            ck('preserved:'+item['path'],ok);preservation+=1
    synthetic=[]
    for name,index,column,delta in [('event_endpoint',0,'next_MWh',.1),('event_time',0,'event_time_h',.1),('event_backup',35,'gas_MWh',.1)]:
        bad=copy.deepcopy(events);bad[index][column]=str(float(bad[index][column])+delta)
        failures=sum(not c['passed'] for c in event_checks(bad,cases)[0])
        synthetic.append(dict(name='detect_'+name,passed=failures>0,evidence_class='synthetic_reviewer_self_check'))
    bad=copy.deepcopy(saved);bad[0]['Storage_E_Next_MWh']=str(float(bad[0]['Storage_E_Next_MWh'])+.1)
    synthetic.append(dict(name='detect_saved_trace_corruption',passed=any(not c['passed'] for c in saved_trace_checks(bad,cases)),evidence_class='synthetic_reviewer_self_check'))
    groups={'actual_numeric':actual,'static_saved_v30_model':static,'artifact_runtime_and_preservation':evidence,'synthetic_reviewer_self_checks':synthetic}
    breakdown={k:dict(passed=sum(c['passed'] for c in v),failed=sum(not c['passed'] for c in v)) for k,v in groups.items()}
    failed=sum(v['failed'] for v in breakdown.values());stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    report=dict(timestamp_utc=stamp,result_directory=str(folder.relative_to(ROOT)),model_release='0.30',checkpoint_version='0.31',
                breakdown=breakdown,failed=failed,checks=groups,previous_immutable_entries_checked=preservation,
                receipt_path=str(args.receipt),receipt_sha256=digest(args.receipt),execution_log_sha256=digest(log),
                reviewer_sha256=digest(Path(__file__)),physical_validation=False,article_replication=False,
                independent_scope='Python equation/numeric/artifact reviewer, no separate human/agent review')
    path=ROOT/'audit'/f'TES_event_independent_QA_v31_{stamp}.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report_path=str(path.relative_to(ROOT)),breakdown=breakdown,failed=failed)))
    for category,items in groups.items():
        for item in items:
            if not item['passed']:print('FAIL',category,item['name'])
    return int(failed>0)

if __name__=='__main__':raise SystemExit(main())
