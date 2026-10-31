"""Prepare immutable fixtures and verify actual MAT/binary evidence independently.

No production controller or reporter is called in Python. Inherited independent
closed equations consume exact-binary operands at 120/160 digits. The v75 schema
is checked first; its three provenance columns are excluded only when comparing
the unchanged thermal algorithm to the saved v73r2 schema.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
import copy, csv, hashlib, json, shutil, struct, sys, zipfile
import xml.etree.ElementTree as ET
from earliest_closed_form_v73 import analyze, contains, dec, rows
from verify_held_schedule_v74 import total_earliest, review_report

ROOT=Path(__file__).resolve().parents[1]
MODEL='matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v75.slx'
FILES=['audit/scaffold_reporting_v75.py','audit/reporting_provenance_v75.py',
       'audit/run_reporting_provenance_v75.ps1','matlab/run_reporting_provenance_v75.m',
       'matlab/simulink/earliest_dispatch_kernel_v75.m','matlab/simulink/build_earliest_dispatch_v75.m',
       'matlab/+dchr/report_held_schedule_v75.m','matlab/+dchr/validate_reporting_trace_v75.m']
REVIEWERS=['audit/earliest_closed_form_v73.py','audit/verify_held_schedule_v74.py',
           'audit/verify_interval_dispatch_v66.py','audit/verify_stateflow_finite_v57.py',
           'audit/verify_restart_chain_v64.py','audit/verify_capacity_chain_v63.py',
           'audit/verify_interval_dispatch_v65.py','audit/earliest_service_reference_v66.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stamp():return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def prepare():
    prior=json.loads((ROOT/'results/held_schedule_v74_20261012T075732_044061Z/spec.json').read_text())
    selected=[c for c in prior['cases'] if c['family']=='six_mode' or c['id'] in ['seasonal_0p5','variable_holds','enable_changes']]
    folder=ROOT/'results'/('reporting_provenance_v75_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.75',cases=selected,scope='SYNTHETIC_INPUT_PROVENANCE_AND_REPORT_INTEGRITY_REPAIR'))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))+list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved if 'v75' not in p.name])
    dump(folder/'ledger_prefixes.json',[dict(path=rel,size=(ROOT/rel).stat().st_size,sha256=sha(ROOT/rel)) for rel in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']])
    snapshot(folder)
    print(folder.relative_to(ROOT).as_posix())
def snapshot(folder):
    rec=[]
    for rel in FILES+REVIEWERS:
        src=ROOT/rel;dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        rec.append(dict(path=rel,sha256=sha(src)))
    dump(folder/'source_hashes.json',rec)
def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];numeric=[];aggregates={};mutation_checks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_report_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_report_present',(folder/'reporting_provenance_v75.mat').stat().st_size>1000)
    original=copy.deepcopy(report)
    for entry in json.loads((folder/'binary_manifest.json').read_text()):
        values=[v[0] for v in struct.iter_unpack('<d',(folder/entry['file']).read_bytes())];n=entry['columns'];m=entry['rows']
        matrix=[values[k:k+n] for k in range(0,len(values),n)] if n else []
        obj=report[entry['group']][entry['index']-1];jvalue=obj[entry['field']]
        value=matrix[0] if m==1 else matrix
        check('binary',entry['file'],len(values)==m*n and value==jvalue)
        original[entry['group']][entry['index']-1][entry['field']]=value
    with localcontext() as ctx:
        ctx.prec=160
        for r in original['runs']:
            real=copy.deepcopy(r);tr=rows(r['trace']);u=rows(r['input']);a=r['adapter'];cumsum=0.
            for k,(row,ui,s) in enumerate(zip(tr,u,rows(a['schedule']))):
                cumsum+=s[0]
                check('provenance',r['id']+f'_{k}',row[1]==75 and row[72:75]==[ui[4],ui[6],ui[7]+2*ui[8]] and ui==[1,0,s[1],0,s[0],*s[2:],*a['initial']] and s[1]==cumsum)
            inherited=copy.deepcopy(tr)
            for row in inherited:row[1]=73;row[72:75]=[0,0,0]
            real['trace']=inherited
            cs,ns=analyze(real);numeric+=ns
            for c in cs:check('closed_equations',c['name'],c['passed'])
            with localcontext() as less:
                less.prec=120;again,_=analyze(real)
            check('precision',r['id'],[c['passed'] for c in cs]==[c['passed'] for c in again])
            totals=total_earliest(real,ns);aggregates[r['id']]=totals
            for name,ok in review_report(r,totals).items():check('report',r['id']+'_'+name,ok)
            check('MAT',r['id'],(folder/(r['id']+'.mat')).stat().st_size>1000)
            if r['prior_trace']:
                check('dispatch_preservation',r['id'],inherited==rows(r['prior_trace']))
        base_by_id={r['id']:r for r in original['runs']}
        # Independent detection uses closed equations/report containment for
        # changed energies, exact operand identities for source/commands, and
        # explicit scalar header invariants for metadata. No MATLAB validator.
        for m in original['mutations']:
            r=base_by_id[m['base_id']];tr=rows(m['trace']);id=m['id'];failures=[]
            if m['kind']=='trace':
                if id in ['service_header','source_header','work_header','negative_aux_header','reversed_service_header','unmet_header','backup_header']:
                    names={'service_header':('delivered_service',43),'source_header':('recovered_source',33),'work_header':('compressor_work',35),
                           'negative_aux_header':('auxiliary_work',49),'reversed_service_header':('delivered_service',43),'unmet_header':('unmet_demand',47),'backup_header':('backup_heat',45)}
                    key,end=names[id];box=tr[-1][end-1:end+1]
                    failures.append(not (0<=box[0]<=box[1] and contains(box,aggregates[r['id']][key])))
                elif 'segment_count' in id:
                    count=tr[-1][12];failures.append(not (count==int(count) and 1<=count<=16))
                elif id=='mode_header':
                    row=tr[-1];failures.append(row[0]!=row[100+80*(int(row[12])-1)+1])
                elif id=='event_header':
                    row=tr[-1];failures.append(row[13]!=sum(row[100+80*j+2]>0 for j in range(int(row[12]))))
                elif id=='origin_header':failures.append(tr[-1][50:52]!=[r['adapter']['initial'][0]]*2)
                elif id=='residual_header':failures.append(tr[-1][52:54]!=rows(r['trace'])[-1][52:54])
            elif m['kind']=='input_only':failures.append(m['adapter']['input']!=r['adapter']['input'])
            else:
                ui=rows(m['input'])[0];failures.append(tr[0][72:75]!=[ui[4],ui[6],ui[7]+2*ui[8]])
            check('actual_corruption',id,any(failures) and m['legacy_accepted'] and m['new_error']==m['expected_error'])
        # Separate synthetic reviewer self-checks, never counted as actual
        # saved-model execution. Each corrupt report must lose containment.
        target=next(r for r in original['runs'] if r['id']=='seasonal_0p5')
        for key in ['hp_heat','recovered_source','compressor_work','delivered_service','unmet_demand','auxiliary_work']:
            bad=copy.deepcopy(target);bad['summary'][key+'_MWh_hull']=[-2,-1]
            mutation_checks.append(dict(name=key+'_report_corruption',passed=not all(review_report(bad,aggregates[target['id']]).values())))
    model=ROOT/MODEL
    with zipfile.ZipFile(model) as archive:
        xml=''.join(archive.read(n).decode('utf-8') for n in archive.namelist() if n.startswith('simulink/stateflow') and n.endswith('.xml'))
        for name in ['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']:check('SLX',name,name in xml)
        scripts=[]
        for n in archive.namelist():
            if n.startswith('simulink/stateflow') and n.endswith('.xml'):
                scripts += [e.text or '' for e in ET.fromstring(archive.read(n)).iter('P') if e.attrib.get('Name')=='script']
        kernel=(ROOT/'matlab/simulink/earliest_dispatch_kernel_v75.m').read_text().replace('\r\n','\n')
        check('SLX','embedded_exact_kernel',kernel in [s.replace('\r\n','\n') for s in scripts])
    check('Stateflow','six_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','observed_license',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','successful_batch',any(v['exit_code']==0 for v in receipts))
    for entry in json.loads((folder/'preservation.json').read_text()):check('preservation',entry['path'],sha(ROOT/entry['path'])==entry['sha256'])
    for entry in json.loads((folder/'source_hashes.json').read_text()):check('source',entry['path'],sha(ROOT/entry['path'])==entry['sha256'] and sha(folder/'source_snapshot'/entry['path'])==entry['sha256'])
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledger',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    ts=stamp();csvpath=folder/f'closed_traces_v75_{ts}.csv'
    with csvpath.open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.75',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(model),checks=checks,reviewer_selfchecks=mutation_checks,
                aggregates={id:{k:str(v) for k,v in totals.items()} for id,totals in aggregates.items()},numeric_csv=csvpath.name,
                summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    path=folder/f'independent_QA_v75_{ts}.json';dump(path,result)
    log=dict(qa=path.relative_to(ROOT).as_posix(),summary=result['summary'],reviewer_selfchecks=mutation_checks,failed=[c for c in checks if not c['passed']][:100])
    dump(folder/f'independent_QA_v75_{ts}.log',log);print(json.dumps(log))
    return int(result['summary']['failed']>0 or not all(m['passed'] for m in mutation_checks))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':
        folder=(ROOT/sys.argv[2]).resolve();assert folder.is_relative_to(ROOT/'results');sys.exit(verify(folder))
