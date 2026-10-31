"""Fresh saved-v75 execution QA. Independent exact-binary/closed exp/log lane.

Does not import or execute production MATLAB functions. Temporal identities use
Fraction endpoints; nonlinear energy/event QA uses inherited 120/160-digit
closed equations. Binary exports are made after MATLAB reopens original MAT.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
from decimal import localcontext
import copy, csv, hashlib, json, shutil, struct, sys, zipfile
from earliest_closed_form_v73 import analyze, rows
from verify_held_schedule_v74 import total_earliest, review_report

ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v75.slx'
FILES=['matlab/+dchr/validate_temporal_trace_v76.m','matlab/+dchr/report_held_schedule_v76.m',
       'matlab/run_temporal_reporting_v76.m','audit/run_temporal_reporting_v76.ps1','audit/temporal_reporting_v76.py',
       'matlab/+dchr/validate_reporting_trace_v75.m','matlab/+dchr/report_held_schedule_v75.m',
       'matlab/+dchr/adapt_held_schedule_v74.m','matlab/simulink/earliest_dispatch_kernel_v75.m',
       'audit/earliest_closed_form_v73.py','audit/verify_held_schedule_v74.py',
       'audit/verify_interval_dispatch_v66.py','audit/verify_stateflow_finite_v57.py',
       'audit/verify_restart_chain_v64.py','audit/verify_capacity_chain_v63.py',
       'audit/verify_interval_dispatch_v65.py','audit/earliest_service_reference_v66.py']
LEDGERS=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']
def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepare():
    spec=json.loads((ROOT/'results/reporting_provenance_v75_20261012T081420_308048Z/spec.json').read_text())
    c=copy.deepcopy(next(c for c in spec['cases'] if c['id']=='HP_only'));c['id']='temporal_chain'
    c['schedule']=[[.1,.1*(j+1),.5,20,1,0] for j in range(4)]
    # Canonical binary cumsum differs from multiplication for some durations.
    end=0.
    for s in c['schedule']:end+=s[0];s[1]=end
    spec['cases'].append(c);spec['version']='0.76';spec['scope']='SAVED_V75_TEMPORAL_REPORTING_IMPLEMENTATION_NO_NEW_SLX'
    folder=ROOT/'results'/('temporal_reporting_v76_'+stamp());folder.mkdir();dump(folder/'spec.json',spec)
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved if 'v76' not in p.name])
    dump(folder/'ledger_prefixes.json',[dict(path=r,size=(ROOT/r).stat().st_size,sha256=sha(ROOT/r)) for r in LEDGERS])
    hashes=[]
    for r in FILES:
        src=ROOT/r;dst=folder/'source_snapshot'/r;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        hashes.append(dict(path=r,sha256=sha(src)))
    dump(folder/'source_hashes.json',hashes);print(folder.relative_to(ROOT).as_posix())

def encloses(box,lo,hi):return F(box[0])<=lo<=hi<=F(box[1])
def temporal_checks(r):
    checks=[]
    def check(name,ok):checks.append(dict(name=r['id']+'_'+name,passed=bool(ok)))
    a=r['adapter'];E=[a['initial'][0]]*2;on=a['initial'][1];age=[a['initial'][2]]*2;tag=0;clock=[0.,0.]
    for k,row in enumerate(rows(r['trace'])):
        dt=F(rows(a['schedule'])[k][0]);start=row[57:59];boundary=row[59:61]
        check(f'{k}_macro_links',row[2:4]==E and start==clock and row[9:11]==boundary)
        check(f'{k}_macro_duration',encloses(boundary,F(clock[0])+dt,F(clock[1])+dt))
        t=[0.,0.]
        for j in range(int(row[12])):
            z=row[100+80*j:180+80*j];d=z[6:8];elapsed=z[8:10];reason=z[22];event=z[2]
            check(f'{k}_{j}_segment_links',z[4:6]==t and z[10:12]==E and z[77]==on and z[78:80]==age and z[20]==tag)
            check(f'{k}_{j}_elapsed',encloses(elapsed,F(t[0])+F(d[0]),F(t[1])+F(d[1])))
            check(f'{k}_{j}_domain',reason in range(4) and z[3] in [0,1])
            current_on=on;current_age=age
            if reason:
                check(f'{k}_{j}_boundary_reason',(reason==1 and on==0) or (reason in [2,3] and on==1))
                current_on=int(reason==1);current_age=[0.,0.]
            check(f'{k}_{j}_boundary_memory',z[18]==current_on and z[14:16]==current_age)
            next_on=current_on;next_tag=0
            if event in [1,3]:
                next_on=int(event==3);check(f'{k}_{j}_event_age_reset',z[16:18]==[0.,0.]);next_tag=1 if event==1 else 3*z[3]
            else:
                check(f'{k}_{j}_event_age',encloses(z[16:18],F(current_age[0])+F(d[0]),F(current_age[1])+F(d[1])))
                next_tag=2 if event==2 else 0
            check(f'{k}_{j}_event_latch_tag',z[19]==next_on and z[21]==next_tag)
            check(f'{k}_{j}_thermal_flag',(event==0 and z[3]==0) or (event in [1,2] and z[3]==1) or event==3)
            if j==int(row[12])-1:
                check(f'{k}_{j}_held_remainder',event==0 and encloses(d,dt-F(t[1]),dt-F(t[0])))
            else:check(f'{k}_{j}_interior_event',event in [1,2,3])
            E=z[12:14];on=next_on;age=z[16:18];tag=next_tag;t=elapsed
        check(f'{k}_endpoint_links',row[4:6]==E and row[6]==on and row[7:9]==age and row[11]==tag)
        clock=boundary
    return checks

def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];aggregates={};selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'temporal_reporting_v76.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        vals=[x[0] for x in struct.iter_unpack('<d',(folder/e['file']).read_bytes())];n=e['columns'];m=e['rows']
        matrix=[vals[j:j+n] for j in range(0,len(vals),n)];value=matrix[0] if m==1 else matrix
        obj=report[e['group']][e['index']-1];check('binary',e['file'],len(vals)==m*n and value==obj[e['field']]);obj[e['field']]=value
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            for c in temporal_checks(r):check('exact_binary_protocol',c['name'],c['passed'])
            original=copy.deepcopy(r);tr=rows(r['trace']);u=rows(r['input']);a=r['adapter']
            for k,(row,ui,s) in enumerate(zip(tr,u,rows(a['schedule']))):
                check('input_binding',r['id']+f'_{k}',row[1]==75 and row[72:75]==[ui[4],ui[6],ui[7]+2*ui[8]] and ui==[1,0,s[1],0,s[0],*s[2:],*a['initial']])
            mapped=copy.deepcopy(tr)
            for row in mapped:row[1]=73;row[72:75]=[0,0,0]
            original['trace']=mapped;cs,ns=analyze(original);numeric+=ns
            for c in cs:check('closed_equations',c['name'],c['passed'])
            with localcontext() as lower:
                lower.prec=120;again,_=analyze(original)
            check('precision',r['id'],[c['passed'] for c in cs]==[c['passed'] for c in again])
            totals=total_earliest(original,ns);aggregates[r['id']]=totals
            for name,ok in review_report(r,totals).items():check('report',r['id']+'_'+name,ok)
            check('MAT',r['id'],(folder/(r['id']+'.mat')).stat().st_size>1000)
        by_id={r['id']:r for r in report['runs']}
        for m in report['mutations']:
            bad=copy.deepcopy(by_id[m['base_id']]);bad['trace']=m['trace'];cs=temporal_checks(bad)
            check('actual_reporting_controls',m['id'],any(not c['passed'] for c in cs) and m['legacy_accepted'] and m['new_error']==m['expected_error'])
        target=by_id['temporal_chain']
        for col in [6,7,58]:
            bad=copy.deepcopy(target);bad['trace'][1][col]+=1
            selfchecks.append(dict(name=f'synthetic_temporal_column_{col+1}',passed=any(not c['passed'] for c in temporal_checks(bad))))
        for name in ['hp_heat','delivered_service','compressor_work']:
            bad=copy.deepcopy(target);bad['summary'][name+'_MWh_hull']=[-2,-1]
            selfchecks.append(dict(name='synthetic_report_'+name,passed=not all(review_report(bad,aggregates[target['id']]).values())))
    check('Stateflow','six_actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','observed_api',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    with zipfile.ZipFile(ROOT/MODEL) as archive:
        xml=''.join(archive.read(n).decode('utf-8') for n in archive.namelist() if n.startswith('simulink/stateflow') and n.endswith('.xml'))
        for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']:check('SLX',name,name in xml)
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','successful_batch',any(v['exit_code']==0 for v in receipts))
    for e in json.loads((folder/'preservation.json').read_text()):check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'])
    for e in json.loads((folder/'source_hashes.json').read_text()):check('sources',e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'source_snapshot'/e['path'])==e['sha256'])
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledgers',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    ts=stamp();csvpath=folder/f'closed_traces_v76_{ts}.csv'
    with csvpath.open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.76',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(ROOT/MODEL),checks=checks,reviewer_selfchecks=selfchecks,
        aggregates={id:{k:str(v) for k,v in totals.items()} for id,totals in aggregates.items()},numeric_csv=csvpath.name,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    path=folder/f'independent_QA_v76_{ts}.json';dump(path,result)
    log=dict(qa=path.relative_to(ROOT).as_posix(),summary=result['summary'],reviewer_selfchecks=selfchecks,failed=[c for c in checks if not c['passed']][:50]);dump(folder/f'independent_QA_v76_{ts}.log',log);print(json.dumps(log))
    return int(result['summary']['failed']>0 or not all(c['passed'] for c in selfchecks))
if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':
        folder=(ROOT/sys.argv[2]).resolve();assert folder.is_relative_to(ROOT/'results');sys.exit(verify(folder))
