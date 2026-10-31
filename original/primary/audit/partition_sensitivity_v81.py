"""Actual saved-v80 partition experiment with independent closed-equation QA."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
import copy, csv, hashlib, json, shutil, struct, sys
from earliest_closed_form_v73 import analyze, dec, rows
from verify_held_schedule_v74 import total_earliest, review_report, NAMES
from temporal_reporting_v76 import temporal_checks
from energy_checks_v78 import energy_checks
from hp_partition_checks_v79 import hp_checks
from standing_loss_checks_v80 import loss_checks

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v80.slx'
LEDGERS = ['automation/engineering_progress.md', 'automation/STATEFLOW_ACCEPTANCE.md',
           'audit/research_frontier_2026_10_08.md']

def stamp(): return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, v):
    with p.open('x', encoding='utf-8') as out:
        json.dump(v, out, indent=2); out.write('\n')

def split(c, factor, family):
    c = copy.deepcopy(c); schedule=[]; clock=0.
    for hold in c['schedule']:
        for _ in range(factor):
            duration=hold[0]/factor; clock+=duration
            schedule.append([duration, clock, *hold[2:]])
    c.update(id=family+'_split'+str(factor), family=family, factor=factor, schedule=schedule)
    return c

def prepare():
    prior=json.loads((ROOT/'results/standing_loss_v80_20261013T054910_671296Z/spec.json').read_text())
    by={c['id']:c for c in prior['cases']};cases=[]
    for name in ['zero_demand','HP_only','TES_charge','TES_discharge','boiler_limit','insufficient_heat']:
        cases.append(split(by[name],1,'fixture_'+name))
    families=['multiple_cycles_one_call','OFF_discharge_restart_0p01','seasonal_0p5',
              'enable_changes','passive_lambda0.5_E3.0']
    for name in families:
        cases.extend(split(by[name],factor,name) for factor in [1,2,4,8])
    folder=ROOT/'results'/('partition_sensitivity_v81_'+stamp());folder.mkdir()
    dump(folder/'spec.json',dict(version='0.81',model_version='0.80',cases=cases,
         factors=[1,2,4,8],comparison_relative_budget='1e-10',
         evidence_class='SYNTHETIC_SAVED_STATEFLOW_HELD_INPUT_PARTITION_EXPERIMENT'))
    preserved=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'matlab').rglob('*.slx'))
    preserved+=list(ROOT.glob('STATUS*.json'))+list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder/'preservation.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in preserved])
    dump(folder/'ledger_prefixes.json',[dict(path=p,size=(ROOT/p).stat().st_size,sha256=sha(ROOT/p)) for p in LEDGERS])
    # Seal the actual source tree used by MATLAB and all independent reviewer code.
    sources=list((ROOT/'matlab').rglob('*.m'))+list((ROOT/'audit').glob('*.py'))
    sources += [ROOT/'audit/run_partition_sensitivity_v81.ps1', ROOT/'audit/Partition_sensitivity_derivation_v81.md']
    records=[]
    for p in sources:
        rel=p.relative_to(ROOT);dst=folder/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dst);records.append(dict(path=rel.as_posix(),sha256=sha(p)))
    dump(folder/'source_hashes.json',records)
    print(folder.relative_to(ROOT).as_posix())

def canonical(schedule):
    """Exact operand history; combine adjacent holds with identical inputs."""
    result=[]
    for r in rows(schedule):
        v=list(map(F,r));payload=v[2:]
        if result and result[-1][1]==payload:result[-1][0]+=v[0]
        else:result.append([v[0],payload])
    return result

def close(x,y): return abs(x-y)<=D('1e-10')*max(D(1),abs(x),abs(y))
def overlap(x,y): return x[0]<=y[1] and y[0]<=x[1]

def verify(folder):
    report=json.loads((folder/'report.json').read_text());checks=[];sensitivity=[];numeric=[];selfchecks=[]
    def check(kind,name,ok):checks.append(dict(kind=kind,name=name,passed=bool(ok)))
    check('MAT','reopened_report_equal',report==json.loads((folder/'mat_reopen.json').read_text()))
    check('MAT','original_present',(folder/'partition_sensitivity_v81.mat').stat().st_size>1000)
    for e in json.loads((folder/'binary_manifest.json').read_text()):
        values=[v[0] for v in struct.iter_unpack('<d',(folder/e['file']).read_bytes())]
        m,n=e['rows'],e['columns'];matrix=[values[k:k+n] for k in range(0,len(values),n)]
        v=matrix[0] if m==1 else matrix;obj=report['runs'][e['index']-1]
        check('binary',e['file'],len(values)==m*n and v==obj[e['field']]);obj[e['field']]=v
    totals={};events={};runs={r['id']:r for r in report['runs']}
    with localcontext() as ctx:
        ctx.prec=160
        for r in report['runs']:
            for c in temporal_checks(r)+energy_checks(r)+hp_checks(r)+loss_checks(r):
                check('binary_equations',c['name'],c['passed'])
            mapped=copy.deepcopy(r)
            for row in rows(mapped['trace']):row[1]=73;row[72:75]=[0,0,0]
            cs,ns=analyze(mapped);numeric+=ns
            for c in cs:check('closed_equations',c['name'],c['passed'])
            with localcontext() as less:
                less.prec=120;again,ns120=analyze(mapped)
            check('precision',r['id'],[c['passed'] for c in cs]==[c['passed'] for c in again])
            t=total_earliest(mapped,ns);totals[r['id']]=t
            events[r['id']]=[dict(type=v['event'],time=v['time']) for v in ns if v['event']]
            for name,ok in review_report(r,t).items():check('report',r['id']+'_'+name,ok)
            check('MAT',r['id'],(folder/(r['id']+'.mat')).stat().st_size>1000)
            # Explicit separate MWh/MW bounds without a power-derived slack.
            p=list(map(F,r['p']));cap=p[0]*(p[2]-p[1])
            for k,row in enumerate(rows(r['trace'])):
                check('capacity',r['id']+f'_{k}_inventory',F(0)<=F(row[2])<=F(row[3])<cap and F(0)<=F(row[4])<=F(row[5])<cap)
                for j in range(int(row[12])):
                    z=list(map(F,row[100+80*j:180+80*j]));q=z[23:29]
                    check('capacity',r['id']+f'_{k}_{j}_ports',0<=q[0]<=F(row[56])<=p[10] and 0<=q[2]<=p[8] and 0<=q[3]<=p[9] and 0<=q[4]<=p[23] and all(v>=0 for v in q))
            a=r['adapter'];clock=0.
            for k,(s,u,row) in enumerate(zip(rows(a['schedule']),rows(r['input']),rows(r['trace']))):
                clock+=s[0]
                check('adapter',r['id']+f'_{k}',s[1]==clock and u==[1,0,s[1],0,s[0],*s[2:],*a['initial']] and row[72:75]==[u[4],u[6],u[7]+2*u[8]])
        for r in report['runs']:
            if r['factor']==1:continue
            base=runs.get(r['family']+'_split1')
            if base is None:
                sensitivity.append(dict(id=r['id'],passed=False,reason='BASE_RUN_REJECTED'));continue
            check('matched_inputs',r['id'],r['p']==base['p'] and r['adapter']['initial']==base['adapter']['initial'] and canonical(r['adapter']['schedule'])==canonical(base['adapter']['schedule']))
            differences={k:str(totals[r['id']][k]-totals[base['id']][k]) for k in totals[r['id']]}
            numeric_ok=all(close(totals[r['id']][k],totals[base['id']][k]) for k in totals[r['id']])
            ev,bev=events[r['id']],events[base['id']]
            event_ok=len(ev)==len(bev) and all(x['type']==y['type'] and close(D(x['time']),D(y['time'])) for x,y in zip(ev,bev))
            fields=[k+'_MWh_hull' for k in NAMES]+['final_inventory_hull']
            hulls={k:dict(overlap=overlap(r['summary'][k],base['summary'][k]),
                         base_width=base['summary'][k][1]-base['summary'][k][0],
                         split_width=r['summary'][k][1]-r['summary'][k][0]) for k in fields}
            sensitivity.append(dict(id=r['id'],family=r['family'],factor=r['factor'],
                passed=numeric_ok and event_ok and all(v['overlap'] for v in hulls.values()),
                numeric_within_budget=numeric_ok,event_sequence_within_budget=event_ok,
                events=ev,base_events=bev,differences=differences,hulls=hulls))
        target=copy.deepcopy(report['runs'][0]);target['trace']=rows(target['trace'])
        target['trace'][0][137:139]=[1.,1.]
        selfchecks.append(dict(name='invented_passive_loss_detected',passed=any(not c['passed'] for c in loss_checks(target))))
        target=copy.deepcopy(report['runs'][0]);target['trace']=rows(target['trace']);target['trace'][0][4:6]=[-1.,-1.]
        mapped=copy.deepcopy(target)
        for row in mapped['trace']:row[1]=73;row[72:75]=[0,0,0]
        cs,_=analyze(mapped);selfchecks.append(dict(name='wrong_ODE_endpoint_detected',passed=any(not c['passed'] for c in cs)))
        base=next(r for r in report['runs'] if r['family']=='multiple_cycles_one_call' and r['factor']==1)
        changed=copy.deepcopy(base['adapter']['schedule']);rows(changed)[0][2]+=1
        selfchecks.append(dict(name='changed_input_history_detected',passed=canonical(changed)!=canonical(base['adapter']['schedule'])))
        selfchecks.append(dict(name='large_energy_change_detected',passed=not close(D(1),D(2))))
    check('Stateflow','six_executed_modes',report['mode_coverage']==list(range(6)))
    check('Stateflow','observed_actual_API',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    for manifest in ['preservation.json','source_hashes.json']:
        for e in json.loads((folder/manifest).read_text()):
            ok=sha(ROOT/e['path'])==e['sha256']
            if manifest=='source_hashes.json':ok=ok and sha(folder/'source_snapshot'/e['path'])==e['sha256']
            check('artifact',manifest+'_'+e['path'],ok)
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):
        check('ledger',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    check('execution','observed_completed_batch',any(e['exit_code']==0 for e in receipts))
    check('MATLAB','assertions_passed',report['summary']['failed']==0)
    csvpath=folder/('closed_partition_traces_v81_'+stamp()+'.csv')
    with csvpath.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(numeric[0]));w.writeheader();w.writerows(numeric)
    result=dict(version='0.81',timestamp_utc=datetime.now(timezone.utc).isoformat(),
        saved_model_version='0.80',new_model=False,model_sha256=sha(ROOT/MODEL),
        checks=checks,sensitivity=sensitivity,reviewer_selfchecks=selfchecks,
        aggregates={k:{field:str(v) for field,v in t.items()} for k,t in totals.items()},
        events=events,numeric_csv=csvpath.name,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)),
        sensitivity_summary=dict(passed=sum(c['passed'] for c in sensitivity),failed=sum(not c['passed'] for c in sensitivity)))
    path=folder/('independent_QA_v81_'+stamp()+'.json');dump(path,result)
    log=dict(qa=path.relative_to(ROOT).as_posix(),summary=result['summary'],sensitivity_summary=result['sensitivity_summary'],
             selfchecks=selfchecks,failed=[c for c in checks if not c['passed']][:30],
             sensitivity_failed=[c['id'] for c in sensitivity if not c['passed']])
    dump(path.with_suffix('.log'),log);print(json.dumps(log))
    return int(result['summary']['failed']>0 or result['sensitivity_summary']['failed']>0 or not all(c['passed'] for c in selfchecks))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='verify':
        folder=(ROOT/sys.argv[2]).resolve();assert folder.is_relative_to(ROOT/'results');sys.exit(verify(folder))
