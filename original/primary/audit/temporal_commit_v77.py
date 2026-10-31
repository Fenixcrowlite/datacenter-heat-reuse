"""Original-MAT QA independent of the production temporal monitor.

Fraction temporal identities and 120/160-digit closed exp/log equations.
Same-agent algorithmic QA; no independent personnel or MAT-parser claim.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import localcontext
import copy, csv, hashlib, json, shutil, struct, sys, zipfile
import xml.etree.ElementTree as ET
from temporal_reporting_v76 import temporal_checks, FILES as PRIOR_FILES
from earliest_closed_form_v73 import analyze, rows
from verify_held_schedule_v74 import total_earliest, review_report
ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v77.slx'
NEW=['matlab/simulink/monitor_temporal_commit_v77.m','matlab/simulink/build_temporal_commit_v77.m',
     'matlab/run_temporal_commit_v77.m','audit/run_temporal_commit_v77.ps1',
     'audit/scaffold_temporal_commit_v77.py','audit/temporal_commit_v77.py']
LEDGERS=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']
def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepare():
    spec=json.loads((ROOT/'results/temporal_reporting_v76_20261012T082629_130610Z/spec.json').read_text())
    prior=json.loads((ROOT/'results/earliest_repair_v73r2_20261012T073823_950801Z/spec.json').read_text())
    for name in ['multiple_cycles_one_call','OFF_discharge_restart_0p01','disable_exact_dwell']:
        c=next(c for c in prior['cases'] if c['id']==name);u=c['input']
        added=copy.deepcopy(spec['cases'][0])
        added.update(id=name,p=c['p'],initial=u[0][9:12],schedule=[[v[4],v[2],*v[5:9]] for v in u],family='event_or_boundary_monitor')
        spec['cases'].append(added)
    controls=[('endpoint_latch',[7],'toggle','endpoint memory'),('endpoint_age',[8,9],'shift','endpoint memory'),
        ('endpoint_contact',[12],'contact','endpoint memory'),('incoming_clock',[58,59],'shift','macro continuity'),
        ('boundary_clock',[60,61],'shift','macro continuity'),('reported_clock',[10,11],'widen','macro continuity'),
        ('segment_start',[105,106],'shift','segment clock'),('segment_elapsed',[109,110],'shift','segment clock'),
        ('segment_incoming_inventory',[111,112],'shift','incoming memory'),('segment_incoming_latch',[178],'toggle','incoming memory'),
        ('segment_incoming_age',[179,180],'shift','incoming memory'),('segment_incoming_contact',[121],'contact','incoming memory'),
        ('boundary_age',[115,116],'shift','boundary memory'),('boundary_latch',[119],'toggle','boundary memory'),
        ('segment_endpoint_latch',[120],'toggle','event memory'),('segment_endpoint_age',[117,118],'shift','event memory'),
        ('segment_endpoint_contact',[122],'contact','event memory'),('unknown_boundary_reason',[123],'unknown','transition domain'),
        ('segment_endpoint_inventory',[113,114],'shift','endpoint memory'),('final_duration',[107,108],'shift','segment clock')]
    faults=[dict(id=id,columns=cols,local_columns=[],operation=op,expected=expected,event=0) for id,cols,op,expected in controls]
    for event,label in [(1,'stop'),(2,'cutoff'),(3,'restart')]:
        for cols,op,name in [([17,18],'shift','age'),([20],'toggle','latch'),([22],'contact','contact')]:
            faults.append(dict(id=label+'_'+name,columns=[],local_columns=cols,operation=op,expected='event memory',event=event))
    spec.update(version='0.77',scope='SAVED_STATEFLOW_PRECOMMIT_TEMPORAL_MONITOR',faults=faults)
    folder=ROOT/'results'/('temporal_commit_v77_'+stamp());folder.mkdir();dump(folder/'spec.json',spec)
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved if 'v77' not in p.name])
    dump(folder/'ledger_prefixes.json',[dict(path=r,size=(ROOT/r).stat().st_size,sha256=sha(ROOT/r)) for r in LEDGERS])
    hashes=[]
    for rel in sorted(set(NEW+PRIOR_FILES+['audit/temporal_reporting_v76.py'])):
        src=ROOT/rel;dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        hashes.append(dict(path=rel,sha256=sha(src)))
    dump(folder/'source_hashes.json',hashes);print(folder.relative_to(ROOT).as_posix())
def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];selfchecks=[];aggregates={}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'temporal_commit_v77.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        raw=(folder/e['file']).read_bytes();vals=[x[0] for x in struct.iter_unpack('<d',raw)];n=e['columns'];m=e['rows']
        matrix=[vals[j:j+n] for j in range(0,len(vals),n)];value=matrix[0] if m==1 else matrix
        obj=report[e['group']][e['index']-1];check('binary',e['file'],len(vals)==m*n and value==obj[e['field']]);obj[e['field']]=value
    with localcontext() as ctx:
        ctx.prec=160
        event_types=set()
        for r in report['runs']:
            tr=rows(r['trace']);check('parity',r['id'],tr==rows(r['prior_trace']))
            for c in temporal_checks(r):check('exact_binary_protocol',c['name'],c['passed'])
            a=r['adapter'];u=rows(r['input'])
            for k,(row,ui,s) in enumerate(zip(tr,u,rows(a['schedule']))):
                check('provenance',r['id']+f'_{k}',row[1]==75 and row[72:75]==[ui[4],ui[6],ui[7]+2*ui[8]] and ui==[1,0,s[1],0,s[0],*s[2:],*a['initial']])
                event_types.update(row[100+80*j+2] for j in range(int(row[12])) if row[100+80*j+2]>0)
            mapped=copy.deepcopy(r)
            for row in rows(mapped['trace']):row[1]=73;row[72:75]=[0,0,0]
            cs,ns=analyze(mapped);numeric+=ns
            for c in cs:check('closed_equations',c['name'],c['passed'])
            with localcontext() as less:
                less.prec=120;again,_=analyze(mapped)
            check('precision',r['id'],[c['passed'] for c in cs]==[c['passed'] for c in again])
            totals=total_earliest(mapped,ns);aggregates[r['id']]=totals
            for name,ok in review_report(r,totals).items():check('report',r['id']+'_'+name,ok)
            check('MAT',r['id'],(folder/(r['id']+'.mat')).stat().st_size>1000)
        check('events','three_actual_event_types',event_types=={1,2,3})
        by_id={r['id']:r for r in report['runs']}
        for f in report['faults']:
            base=by_id[f['base_id']];bad=copy.deepcopy(base);bad['trace']=f['trace']
            a=copy.deepcopy(base['adapter']);a['schedule']=rows(a['schedule'])[:f['row']];bad['adapter']=a
            cs=temporal_checks(bad);changed=[]
            original=rows(base['trace'])[:f['row']];mutated=rows(f['trace'])
            for k,(old,new) in enumerate(zip(original,mutated)):
                changed += [(k+1,j+1) for j,(x,y) in enumerate(zip(old,new)) if x!=y]
            cols=f['columns'] if isinstance(f['columns'],list) else [f['columns']]
            check('runtime_fault',f['id'],f['runtime_rejected'] and f['expected_text'] in f['error_text'] and any(not c['passed'] for c in cs))
            check('isolated_bypass',f['id'],set(changed)=={(f['row'],int(c)) for c in cols})
            check('runtime_log',f['id'],(folder/(f['id']+'_runtime_fault.txt')).read_text()==f['error_text']+'\n')
        target=by_id['temporal_chain']
        for col in [6,7,58]:
            bad=copy.deepcopy(target);bad['trace'][1][col]+=1
            selfchecks.append(dict(name=f'synthetic_temporal_{col+1}',passed=any(not c['passed'] for c in temporal_checks(bad))))
        for key in ['hp_heat','delivered_service','compressor_work']:
            bad=copy.deepcopy(target);bad['summary'][key+'_MWh_hull']=[-2,-1]
            selfchecks.append(dict(name='synthetic_report_'+key,passed=not all(review_report(bad,aggregates[target['id']]).values())))
    check('Stateflow','six_actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','actual_api',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    with zipfile.ZipFile(ROOT/MODEL) as archive:
        props=[]
        for name in archive.namelist():
            if name.startswith('simulink/stateflow') and name.endswith('.xml'):
                props += list(ET.fromstring(archive.read(name)).iter('P'))
        scripts=[p.text or '' for p in props if p.attrib.get('Name')=='script']
        for rel in ['matlab/simulink/monitor_temporal_commit_v77.m','matlab/simulink/earliest_dispatch_kernel_v75.m']:
            check('SLX',rel,(ROOT/rel).read_text().replace('\r\n','\n') in [s.replace('\r\n','\n') for s in scripts])
        labels=[p.text or '' for p in props if p.attrib.get('Name')=='labelString']
        gate='monitor_temporal_commit_v77(horizon_input,policy_input,retained_memory,core);'
        for state in report['metadata']['states']:
            label=next((s for s in labels if s.startswith(state+'\n')),'')
            check('SLX',state+'_precommit',label.count(gate)==2 and label.count(gate+'\ntrace=core;\nretained_memory=core;')==2)
        check('SLX','no_test_injection',not any('u(3)==' in s for s in scripts))
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','batch_success',any(v['exit_code']==0 for v in receipts))
    for e in json.loads((folder/'preservation.json').read_text()):check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'])
    for e in json.loads((folder/'source_hashes.json').read_text()):check('sources',e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'source_snapshot'/e['path'])==e['sha256'])
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledgers',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    ts=stamp();csvpath=folder/f'closed_traces_v77_{ts}.csv'
    with csvpath.open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.77',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(ROOT/MODEL),checks=checks,reviewer_selfchecks=selfchecks,numeric_csv=csvpath.name,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    path=folder/f'independent_QA_v77_{ts}.json';dump(path,result)
    log=dict(qa=path.relative_to(ROOT).as_posix(),summary=result['summary'],reviewer_selfchecks=selfchecks,failed=[c for c in checks if not c['passed']][:50]);dump(folder/f'independent_QA_v77_{ts}.log',log);print(json.dumps(log))
    return int(result['summary']['failed']>0 or not all(c['passed'] for c in selfchecks))
if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':
        folder=(ROOT/sys.argv[2]).resolve();assert folder.is_relative_to(ROOT/'results');sys.exit(verify(folder))
