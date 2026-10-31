"""Original-MAT QA independent of the production energy and temporal monitors.

Fraction temporal identities and 120/160-digit closed exp/log equations.
Same-agent algorithmic QA; no independent personnel or MAT-parser claim.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import localcontext
import copy, csv, hashlib, json, shutil, struct, sys, zipfile
import xml.etree.ElementTree as ET
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from standing_loss_checks_v80 import loss_checks
from temporal_reporting_v76 import temporal_checks, FILES as PRIOR_FILES
from earliest_closed_form_v73 import analyze, rows
from verify_held_schedule_v74 import total_earliest, review_report
ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx'
NEW=['matlab/simulink/monitor_standing_loss_v80.m','matlab/simulink/build_standing_loss_v80.m',
     'matlab/run_standing_loss_v80.m','audit/run_standing_loss_v80.ps1',
     'audit/scaffold_standing_loss_v80.py','audit/standing_loss_v80.py',
     'audit/standing_loss_checks_v80.py','audit/Standing_loss_derivation_v80.md',
     'audit/hp_partition_checks_v79.py','matlab/simulink/monitor_hp_partition_v79.m']
LEDGERS=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']
def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepare():
    spec=json.loads((ROOT/'results/hp_partition_v79_20261013T053839_629571Z/spec.json').read_text())
    base=copy.deepcopy(next(c for c in spec['cases'] if c['id']=='zero_demand'))
    for lam in [0.,.01,.5,1.]:
        for E in [0.,3.,9.]:
            c=copy.deepcopy(base);c['id']=f'passive_lambda{lam}_E{E}'
            c['p'][5]=lam;c['initial'][0]=E
            c['schedule']=[[1.,1.,0.,0.,0.,0.]]
            c['family']='loss_rate_axes';spec['cases'].append(c)
    spec['faults']=[
        dict(id='invented_loss_zero_lambda',base_id='passive_lambda0.0_E3.0',endpoint=2.,loss=1.,expected='zero coefficient standing loss'),
        dict(id='suppressed_positive_decay',base_id='passive_lambda0.5_E3.0',endpoint=3.,loss=0.,expected='standing loss rate'),
        dict(id='excess_positive_decay',base_id='passive_lambda0.01_E3.0',endpoint=2.,loss=1.,expected='standing loss rate'),
        dict(id='deficient_positive_decay',base_id='passive_lambda0.5_E3.0',endpoint=2.875,loss=.125,expected='standing loss rate')]
    spec.update(version='0.80',scope='SAVED_STATEFLOW_NECESSARY_TES_CONSTITUTIVE_LOSS')
    folder=ROOT/'results'/('standing_loss_v80_'+stamp());folder.mkdir();dump(folder/'spec.json',spec)
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved if 'v80' not in p.name])
    dump(folder/'ledger_prefixes.json',[dict(path=r,size=(ROOT/r).stat().st_size,sha256=sha(ROOT/r)) for r in LEDGERS])
    hashes=[]
    for rel in sorted(set(NEW+PRIOR_FILES+['audit/temporal_reporting_v76.py','matlab/simulink/monitor_temporal_commit_v77.m','matlab/simulink/monitor_energy_commit_v78.m','audit/strict_capacity_v78.py'])):
        src=ROOT/rel;dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        hashes.append(dict(path=rel,sha256=sha(src)))
    dump(folder/'source_hashes.json',hashes);print(folder.relative_to(ROOT).as_posix())
def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];selfchecks=[];aggregates={}
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'standing_loss_v80.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        raw=(folder/e['file']).read_bytes();vals=[x[0] for x in struct.iter_unpack('<d',raw)];n=e['columns'];m=e['rows']
        matrix=[vals[j:j+n] for j in range(0,len(vals),n)];value=matrix[0] if m==1 else matrix
        obj=report[e['group']][e['index']-1];check('binary',e['file'],len(vals)==m*n and value==obj[e['field']]);obj[e['field']]=value
    with localcontext() as ctx:
        ctx.prec=160
        event_types=set()
        for r in report['runs']:
            tr=rows(r['trace']);check('parity',r['id'],tr==rows(r['prior_trace']))
            for c in loss_checks(r)+hp_checks(r)+energy_checks(r)+temporal_checks(r):check('exact_binary_protocol',c['name'],c['passed'])
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
        for col in [123,129,131,137,149,151,14,30,50,52]:
            bad=copy.deepcopy(by_id['temporal_chain']);bad['trace'][1][col]+=1
            selfchecks.append(dict(name=f'synthetic_energy_{col+1}',passed=any(not c['passed'] for c in energy_checks(bad))))
        for f in report['faults']:
            base=by_id[f['base_id']];bad=copy.deepcopy(base);bad['trace']=f['trace']
            a=copy.deepcopy(base['adapter']);a['schedule']=rows(a['schedule'])[:f['row']];bad['adapter']=a
            cs=loss_checks(bad);changed=[]
            original=rows(base['trace'])[:f['row']];mutated=rows(f['trace'])
            for k,(old,new) in enumerate(zip(original,mutated)):
                changed += [(k+1,j+1) for j,(x,y) in enumerate(zip(old,new)) if x!=y]
            cols=f['columns'] if isinstance(f['columns'],list) else [f['columns']]
            check('runtime_fault',f['id'],f['runtime_rejected'] and f['expected_text'] in f['error_text'] and any(not c['passed'] for c in cs))
            check('legacy_energy_HP_temporal_checks',f['id'],all(c['passed'] for c in energy_checks(bad)+hp_checks(bad)+temporal_checks(bad)))
            check('exact_fault_trace',f['id'],mutated==rows(f['expected_trace']))
            mapped=copy.deepcopy(bad)
            for rr in rows(mapped['trace']):rr[1]=73;rr[72:75]=[0,0,0]
            nonlinear,_=analyze(mapped)
            check('independent_ODE_rejection',f['id'],any(not c['passed'] for c in nonlinear if c['name'].endswith('_inventory_end') or c['name'].endswith('_energy_3')))
            check('legacy_acceptance',f['id'],rows(f['legacy_trace'])==mutated)
            check('isolated_bypass',f['id'],set(changed)=={(f['row'],int(c)) for c in cols})
            check('runtime_log',f['id'],(folder/(f['id']+'_runtime_fault.txt')).read_text()==f['error_text']+'\n')
        target=by_id['temporal_chain']
        for col in [6,7,58]:
            bad=copy.deepcopy(target);bad['trace'][1][col]+=1
            selfchecks.append(dict(name=f'synthetic_temporal_{col+1}',passed=any(not c['passed'] for c in temporal_checks(bad))))
        for key in ['hp_heat','delivered_service','compressor_work']:
            bad=copy.deepcopy(target);bad['summary'][key+'_MWh_hull']=[-2,-1]
            selfchecks.append(dict(name='synthetic_report_'+key,passed=not all(review_report(bad,aggregates[target['id']]).values())))
    # Separate reviewer controls: zero lambda, positive lambda and a wide
    # overlapping hull acceptance witness document the necessary-only scope.
    for name in ['invented_loss_zero_lambda','suppressed_positive_decay']:
        f=next(x for x in report['faults'] if x['id']==name)
        bad=copy.deepcopy(by_id[f['base_id']]);bad['trace']=copy.deepcopy(f['trace'])
        selfchecks.append(dict(name='loss_control_'+name,passed=any(not c['passed'] for c in loss_checks(bad))))
    bad=copy.deepcopy(by_id['passive_lambda0.5_E3.0'])
    rows(bad['trace'])[0][137:139]=[0.,3.]
    selfchecks.append(dict(name='wide_loss_overlap_scope_witness',passed=all(c['passed'] for c in loss_checks(bad))))
    check('Stateflow','six_actual_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','actual_api',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    with zipfile.ZipFile(ROOT/MODEL) as archive:
        props=[]
        for name in archive.namelist():
            if name.startswith('simulink/stateflow') and name.endswith('.xml'):
                props += list(ET.fromstring(archive.read(name)).iter('P'))
        scripts=[p.text or '' for p in props if p.attrib.get('Name')=='script']
        for rel in ['matlab/simulink/monitor_standing_loss_v80.m','matlab/simulink/monitor_energy_commit_v78.m','matlab/simulink/monitor_hp_partition_v79.m','matlab/simulink/monitor_temporal_commit_v77.m','matlab/simulink/earliest_dispatch_kernel_v75.m']:
            check('SLX',rel,(ROOT/rel).read_text().replace('\r\n','\n') in [s.replace('\r\n','\n') for s in scripts])
        labels=[p.text or '' for p in props if p.attrib.get('Name')=='labelString']
        gate='monitor_standing_loss_v80(horizon_input,policy_input,retained_memory,core);'
        for state in report['metadata']['states']:
            label=next((s for s in labels if s.startswith(state+'\n')),'')
            check('SLX',state+'_precommit',label.count(gate)==2 and label.count(gate+'\ntrace=core;\nretained_memory=core;')==2)
        check('SLX','no_test_injection',not any('u(3)==' in s or 'hp_fault_mul' in s for s in scripts))
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','batch_success',any(v['exit_code']==0 for v in receipts))
    for e in json.loads((folder/'preservation.json').read_text()):check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'])
    for e in json.loads((folder/'source_hashes.json').read_text()):check('sources',e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'source_snapshot'/e['path'])==e['sha256'])
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledgers',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    ts=stamp();csvpath=folder/f'closed_traces_v80_{ts}.csv'
    with csvpath.open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.80',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(ROOT/MODEL),checks=checks,reviewer_selfchecks=selfchecks,numeric_csv=csvpath.name,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    path=folder/f'independent_QA_v80_{ts}.json';dump(path,result)
    log=dict(qa=path.relative_to(ROOT).as_posix(),summary=result['summary'],reviewer_selfchecks=selfchecks,failed=[c for c in checks if not c['passed']][:50]);dump(folder/f'independent_QA_v80_{ts}.log',log);print(json.dumps(log))
    return int(result['summary']['failed']>0 or not all(c['passed'] for c in selfchecks))
if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':
        folder=(ROOT/sys.argv[2]).resolve();assert folder.is_relative_to(ROOT/'results');sys.exit(verify(folder))
