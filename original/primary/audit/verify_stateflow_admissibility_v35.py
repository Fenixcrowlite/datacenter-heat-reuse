"""Independent targeted numeric, physical-time, MAT and preservation QA.
Reproducing a monitor failure does not confer model acceptance.
"""
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from stateflow_reference_v34 import dispatch, PORTS, HP, SEG34
from verify_stateflow_v34 import segment_laws

ROOT=Path(__file__).resolve().parents[1]


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def near(a,b):
    a=math.nan if a is None else float(a);b=math.nan if b is None else float(b)
    return math.isnan(a) and math.isnan(b) or math.isfinite(a) and math.isfinite(b) and abs(a-b)<=2e-9+2e-11*abs(b)
def matrix(v,n):return [v] if n==1 and v and not isinstance(v[0],list) else v


def laws(s,x,p):
    if p[1]<1e7:return segment_laws(s,x,p)
    # Large-energy cancellation needs energy ulps, never an energy-scaled clock tolerance.
    v=lambda k:float(s[k]);span=v('Duration_h');a=v('Energy_Start_MWh');b=v('Energy_Next_MWh')
    if any(not math.isfinite(v(k)) for k in SEG34 if k!='COP'):return False
    if not near(v('HP_Age_End_h'),v('HP_Age_Start_h')+span):return False
    if span==0:
        return v('Mode')==0 and a==b and all(v(k)==0 for k in SEG34[5:14]+SEG34[16:21])
    tolE=64*math.ulp(max(1,abs(a),abs(b),p[1]))
    qc=v('Storage_Charge_MW');qd=v('Storage_Discharge_MW');gas=v('Gas_Heat_MW');direct=v('HP_Direct_MW')
    if not (span>0 and 0<=a<=p[1]+tolE and 0<=b<=p[1]+tolE and 0<=qc<=p[2] and 0<=qd<=p[3] and 0<=gas<=p[10] and qc*qd==0):return False
    if v('HP_Latch') not in (0,1) or v('HP_Age_Start_h')<0:return False
    if not near(x[3],direct+qd+gas+v('Unmet_Heat_MW')):return False
    if not near(v('HP_Heat_MW'),v('HP_Electric_MW')+v('HP_Source_Used_MW')):return False
    if not near(v('HP_Heat_MW'),direct+qc):return False
    if not near(v('HP_Electric_MW')*v('COP'),v('HP_Heat_MW')):return False
    power=p[4]*qc-qd/p[5];phi=span if not p[6] else -math.expm1(-p[6]*span)/p[6]
    if abs(b-(a*math.exp(-p[6]*span)+power*phi))>tolE:return False
    if abs(v('Storage_Standing_Loss_MWh')-(a+power*span-b))>tolE:return False
    closure=a+(v('HP_Electric_MW')+v('HP_Source_Used_MW')+gas-v('Supplied_Heat_MW'))*span-b-sum(v(k) for k in SEG34[16:19])
    return abs(closure)<=tolE and abs(v('System_Balance_Residual_MWh')-closure)<=tolE


def main():
    folder=Path(sys.argv[1]).resolve();receipt=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
    spec=json.loads((folder/'source_snapshot/spec/cases.json').read_text());cases=spec['cases']
    tt=rows(folder/'trace_v35.csv');ss=rows(folder/'segments_v35.csv');bad=rows(folder/'accepted_corrupted_segments_v35.csv')
    mats={v['file']:v for v in json.loads((folder/'mat_audit_v35.json').read_text())}
    groups={}
    def ck(g,n,ok):groups.setdefault(g,[]).append(dict(name=n,passed=bool(ok)))
    keys=[(c['id'],i) for c in cases for i in range(len(c['inputs']))]
    ck('numeric','ordered_interval_keys',[(r['scenario_id'],int(r['step'])) for r in tt]==keys)
    ck('numeric','ordered_slot_keys',[(r['scenario_id'],int(r['step']),int(r['segment'])) for r in ss]==[(a,i,s) for a,i in keys for s in range(1,65)])
    ti={(r['scenario_id'],int(r['step'])):r for r in tt};si={k:[] for k in keys}
    for r in ss:si[(r['scenario_id'],int(r['step']))].append(r)
    ledger={};modes=set()
    for c in cases:
        n=len(c['inputs']);p=c['p'];e=c['initial_energy_MWh'];clock=c['initial_clock']
        mat=mats[c['id']+'_simulation.mat'];ym=matrix(mat['dispatch'],n);sm=matrix(mat['segments'],n)
        cm=matrix(mat['clock_start'],n);em=matrix(mat['clock_end'],n)
        ck('artifact',c['id']+'_MAT_success',not mat['error_message'])
        for i,x in enumerate(c['inputs']):
            r=ti[c['id'],i];slots=si[c['id'],i];y,expected,end=dispatch(e,x,p,c['h'],clock,c['c'])
            for j,name in enumerate(PORTS+HP):
                ck('numeric',f'{c["id"]}_{i}_{name}',near(r[name],y[j]))
                ck('artifact',f'{c["id"]}_{i}_MAT_{name}',near(r[name],ym[i][j]))
            for j,name in enumerate(['HP_Latch_Start','HP_Age_Start_h','HP_Latch_End','HP_Age_End_h']):
                ck('numeric',f'{c["id"]}_{i}_{name}',near(r[name],(clock+end)[j]))
                ck('artifact',f'{c["id"]}_{i}_MAT_{name}',near(r[name],(cm[i]+em[i])[j]))
            ck('numeric',f'{c["id"]}_{i}_energy_memory',near(r['Storage_E_Start_MWh'],e))
            ck('numeric',f'{c["id"]}_{i}_time',near(r['Time_h'],i*p[0]))
            positive=[s for s in slots if float(s['Duration_h'])>0]
            ck('numeric',f'{c["id"]}_{i}_segment_count',len(positive)==len(expected))
            for j,s in enumerate(slots):
                ck('artifact',f'{c["id"]}_{i}_{j}_MAT_segments',all(near(s[name],sm[i][28*j+k]) for k,name in enumerate(SEG34)))
                ck('numeric',f'{c["id"]}_{i}_{j}_laws',laws(s,x,p))
                if float(s['Duration_h'])>0:
                    modes.add(int(float(s['Mode'])))
                    ck('numeric',f'{c["id"]}_{i}_{j}_oracle',j<len(expected) and all(near(s[k],v) for k,v in zip(SEG34,expected[j])))
            ck('numeric',f'{c["id"]}_{i}_partition',near(sum(float(s['Duration_h']) for s in slots),p[0]))
            e=y[7];clock=end
        ledger[c['id']]=dict(E=e,clock=clock,electric=sum(float(ti[c['id'],i]['HP_Electric_MW'])*p[0] for i in range(n)),
            unmet=sum(float(ti[c['id'],i]['Unmet_Heat_MW'])*p[0] for i in range(n)))
    ck('numeric','six_modes',modes==set(range(6)))
    for family in ('demand_step','source_step','safe_held'):
        base=ledger[family+'_h_0.5']
        for dt in (.25,.125):
            value=ledger[f'{family}_h_{dt:g}']
            ck('partition',f'{family}_{dt}',all(near(value[k],base[k]) for k in ['E','electric','unmet']) and all(near(a,b) for a,b in zip(value['clock'],base['clock'])))
    # Demand > discharge limit + backup while OFF necessarily leaves unmet heat.
    ck('partition','step_while_ON_zero_unmet',near(ledger['demand_step_h_0.5']['unmet'],0))
    ck('partition','OFF_dwell_overload_counterexample',near(ledger['off_dwell_overload']['unmet'],.875))
    ck('partition','safe_held_zero_unmet',near(ledger['safe_held_h_0.5']['unmet'],0))
    faults=json.loads((folder/'fault_evidence_v35.json').read_text());guards=json.loads((folder/'guard_evidence_v35.json').read_text())
    ck('defect','four_executed_faults',len(faults)==4)
    for f in faults:
        actual=mats[f['id']+'_corruption_simulation.mat']
        ck('artifact',f['id']+'_diagnostic_binding',actual['error_message']==f['error_message'] and actual['phase']==f['phase'] and actual['time_h']==f['time_h'])
        ck('defect',f['id']+'_observed_scale_response',f['rejected']==(f['capacity_MWh']<1e9))
        if f['rejected']:ck('defect',f['id']+'_runtime_gate_reject',f['phase']=='Execution' and 'Runtime_Contract_Gate' in f['error_message'])
        else:
            br=[r for r in bad if r['scenario_id']==f['id']];c=next(c for c in cases if c['id']==f['id'])
            bm=matrix(actual['segments'],len(c['inputs']))
            ck('defect','accepted_corrupt_trace_size',len(br)==len(c['inputs'])*64)
            for r in br:
                i=int(r['step']);j=int(r['segment'])-1
                ck('artifact',f'accepted_{i}_{j}_MAT',all(near(r[name],bm[i][j*28+k]) for k,name in enumerate(SEG34)))
                delta=float(r['HP_Age_End_h'])-float(r['HP_Age_Start_h'])-float(r['Duration_h'])
                ck('defect',f'accepted_{i}_{j}_time_error',near(delta,spec['clock_corruption_h']) and not laws(r,c['inputs'][i],c['p']))
    for g in guards:
        ck('defect',f'guard_{g["capacity_MWh"]}',g['age_h']<g['required_off_h'] and g['permitted']==(g['capacity_MWh']>=1e9))
    base=mats[cases[-1]['id']+'_simulation.mat'];restored=mats['restored_simulation.mat']
    ck('artifact','restored_saved_model',restored['segments']==base['segments'] and restored['clock_end']==base['clock_end'] and not restored['error_message'])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v34.slx'
    ck('archive','saved_SLX_snapshot',digest(model)==digest(folder/'source_snapshot'/model.name))
    # Confirm vulnerable tolerance code really exists in the executed saved archive.
    with ZipFile(model) as z:
        scripts=[]
        for name in z.namelist():
            if name.startswith('simulink/stateflow/chart_') and name.endswith('.xml'):
                chart=ET.fromstring(z.read(name))
                scripts.extend(e.findtext("P[@Name='script']",default='').strip() for e in chart.iter('eml'))
    for name in ['stateflow_supervisor_guard_v34','stateflow_contract_gate_v34','stateflow_allocate_v34']:
        path=ROOT/'matlab/simulink'/f'{name}.m'
        ck('archive',name+'_embedded_source',path.read_text().strip() in scripts)
    ck('archive','dimensional_tol_in_guard',any('tol=1e-10*max(1,p(2))' in s and 'age>=c(3)-tol' in s for s in scripts))
    ck('archive','dimensional_tol_in_clock_monitor',any('tol=1e-9*max(1,cap+' in s and 'abs(z(28)-z(27)-span)<=tol' in s for s in scripts))
    for path in (folder/'source_snapshot').glob('*.m'):
        current=ROOT/'matlab/simulink'/path.name
        if not current.is_file():current=ROOT/'matlab/+dchr/+components'/path.name
        ck('artifact',path.name+'_source_binding',digest(path)==digest(current))
    summary=json.loads((folder/'summary_v35.json').read_text());checks=rows(folder/'assertions_v35.csv')
    ck('artifact','observed_batch_exit',receipt['exit_code']==0 and 'run_stateflow_admissibility_v35' in receipt['command'])
    ck('artifact','summary_assertions',summary['failed']==0 and summary['passed']==len(checks) and all(r['passed'] in ['1','true'] for r in checks))
    ck('artifact','summary_counts',summary['scenarios']==len(cases) and summary['intervals']==len(tt) and summary['positive_segments']==sum(float(s['Duration_h'])>0 for s in ss))
    previous={}
    for pattern in ['Stateflow_manifest_v34_*.json','Stateflow_fallback_manifest_v33_*.json','Stateflow_manifest_v32_*.json',
                    'TES_event_manifest_v31_*.json','Stateflow_manifest_v30_*.json','Stateflow_fault_manifest_v29_*.json']:
        for path in (ROOT/'audit').glob(pattern):
            for item in json.loads(path.read_text(encoding='utf-8-sig'))['files']:previous[item['path']]=item
    for name,item in previous.items():
        path=Path(name);path=path if path.is_absolute() else ROOT/path
        ck('preservation',name,path.is_file() and digest(path)==item['sha256'] and path.stat().st_size==item['bytes'])
    counts={g:dict(passed=sum(c['passed'] for c in cc),failed=sum(not c['passed'] for c in cc)) for g,cc in groups.items()}
    out=folder/('independent_QA_v35_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
    report=dict(version='0.35',model_version='0.34',counts=counts,checks=groups,experiment_ledger=ledger,
        model_sha256=digest(model),reviewer_sha256=digest(Path(__file__)),previous_unique_entries=len(previous),
        conclusion='OPEN dimensional clock tolerance defect independently reproduced',
        evidence_class='independent_algorithm_artifact_QA_not_separate_agent_review',physical_validation=False,article_replication=False)
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(counts,indent=2));print('QA='+str(out.relative_to(ROOT)))
    assert not sum(v['failed'] for v in counts.values()),'Independent QA failure'


if __name__=='__main__':main()
