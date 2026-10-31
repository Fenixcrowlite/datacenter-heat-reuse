"""Independent targeted numeric, physical-time, MAT and preservation QA.
Implementation acceptance only; no primary replication or physical validation.
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


def time_near(a,b):
    a=float(a);b=float(b)
    budget=64*math.ulp(max(1,abs(a),abs(b)))
    return math.isfinite(a) and math.isfinite(b) and budget<=1e-8 and abs(a-b)<=budget

def laws(s,x,p):
    if not time_near(s['HP_Age_End_h'],float(s['HP_Age_Start_h'])+float(s['Duration_h'])):return False
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
    tt=rows(folder/'trace_v36.csv');ss=rows(folder/'segments_v36.csv');bad=rows(folder/'accepted_corrupted_segments_v36.csv')
    mats={v['file']:v for v in json.loads((folder/'mat_audit_v36.json').read_text())}
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
            offset=0.;previousE=float(r['Storage_E_Start_MWh']);on,age=clock
            pm=matrix(mat['plan'],n)[i]
            for j,s in enumerate(slots):
                newon=float(s['HP_Latch']);start=float(s['HP_Age_Start_h']);reason=pm[j*18+16]
                ck('time',f'{c["id"]}_{i}_{j}_offset',time_near(s['Offset_h'],offset))
                ck('numeric',f'{c["id"]}_{i}_{j}_energy_handoff',near(s['Energy_Start_MWh'],previousE))
                if on==newon:ck('time',f'{c["id"]}_{i}_{j}_timer_handoff',reason==0 and time_near(start,age))
                else:
                    etol=64*math.ulp(max(1,p[1]));ttol=64*math.ulp(max(1,age,c['c'][1],c['c'][2]))
                    allowed=(newon==1 and reason==3 and previousE<=c['c'][0]+etol and age>=c['c'][2]-ttol) or (newon==0 and (reason==1 or (reason==2 and previousE>=p[1]-etol and age>=c['c'][1]-ttol)))
                    ck('time',f'{c["id"]}_{i}_{j}_dwell_transition',allowed and start==0)
                offset+=float(s['Duration_h']);previousE=float(s['Energy_Next_MWh']);on=newon;age=float(s['HP_Age_End_h'])
            ck('time',f'{c["id"]}_{i}_partition',time_near(offset,p[0]))
            ck('time',f'{c["id"]}_{i}_final_clock',float(r['HP_Latch_End'])==on and time_near(r['HP_Age_End_h'],age))
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
    faults=json.loads((folder/'fault_evidence_v36.json').read_text())
    guards=json.loads((folder/'guard_evidence_v36.json').read_text())
    runtime=json.loads((folder/'runtime_fault_evidence_v36.json').read_text())
    extended=json.loads((folder/'dimensional_fault_evidence_v36.json').read_text())
    ck('faults','four_clock_faults',len(faults)==4)
    ck('faults','30_general_faults',len(runtime)==30)
    ck('faults','21_dimensional_faults',len(extended)==21)
    for group,suffix in [(faults,'_corruption_simulation.mat'),(runtime,'_fault_simulation.mat'),(extended,'_dimensional_simulation.mat')]:
        for f in group:
            actual=mats[f['id']+suffix]
            ck('artifact',f['id']+'_diagnostic_binding',actual['error_message']==f['error_message'] and actual['phase']==f['phase'] and actual['time_h']==f['time_h'])
            ck('faults',f['id']+'_runtime_reject',f['rejected'] and f['phase']=='Execution' and bool(actual['error_message']))
            if group is faults:ck('faults',f['id']+'_physical_clock_gate','Physical-hour clock failure' in actual['error_message'])
            if f['id'].endswith('early_restart'):ck('faults',f['id']+'_guard_gate','Unauthorized HP latch transition' in actual['error_message'])
    ck('faults','no_corrupt_trace_accepted',not bad)
    ck('faults','four_early_guard_probes',len(guards)==4)
    for g in guards:
        ck('time',f'guard_{g["capacity_MWh"]}',g['age_h']==.24 and g['required_off_h']==.25 and not g['permitted'])
    resolution=json.loads((folder/'time_resolution_evidence_v36.json').read_text())
    ck('time','30_component_probes',len(resolution)==30 and all(r['passed'] for r in resolution))
    for r in resolution:
        if r['name'].startswith('time_resolution_'):
            tol=64*math.ulp(max(1,r['age_h']))
            ck('time',r['name']+'_independent',r['tolerance_h'] is None if tol>1e-8 else r['tolerance_h']==tol)
    base=mats[cases[-1]['id']+'_simulation.mat'];restored=mats['restored_simulation.mat']
    ck('artifact','restored_saved_model',restored['segments']==base['segments'] and restored['clock_end']==base['clock_end'] and not restored['error_message'])
    a=mats['pre_fault_clean_simulation.mat'];b=mats['post_fault_clean_simulation.mat']
    ck('artifact','general_fault_restoration',a['segments']==b['segments'] and a['clock_end']==b['clock_end'] and not b['error_message'])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v36.slx'
    ck('archive','saved_SLX_snapshot',digest(model)==digest(folder/'source_snapshot'/model.name))
    with ZipFile(model) as z:
        charts=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
        systems=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/systems/') and n.endswith('.xml')]
    prop=lambda e,n:e.findtext(f"P[@Name='{n}']",default='')
    scripts=[prop(e,'script').strip() for ch in charts for e in ch.iter('eml')]
    for name in ['stateflow_supervisor_guard_v36','stateflow_contract_gate_v36','stateflow_allocate_v36','stateflow_time_tolerance_v36']:
        ck('archive',name+'_embedded_source',(ROOT/'matlab/simulink'/f'{name}.m').read_text().strip() in scripts)
    for path,names in [('Execute_Segments/Thermal_Dispatch',{'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'}),('Execute_Segments/HP_Supervisor',{'HP_OFF','HP_ON'})]:
        ch=next(ch for ch in charts if prop(ch,'name')==path);child=ch.find('Children')
        states=[e for e in child.findall('state') if prop(e,'type')=='OR_STATE']
        ck('archive',path+'_states',{prop(e,'labelString').splitlines()[0] for e in states}==names)
        labels=[prop(e,'labelString') for e in child.findall('transition')]
        if 'Supervisor' in path:
            ck('archive','physical_hour_updates',all('age=age+s(1);' in prop(e,'labelString') for e in states))
            for target in [0,1]:ck('archive',f'guarded_latch_{target}',f'[s(15)=={target} && stateflow_supervisor_guard_v36({target},s,p,c,age)]' in labels)
        else:ck('archive','all_thermal_guards',len(labels)==37 and all(labels.count(f'[stateflow_choose_mode_v36(segmentInput,parameters)=={k}]')==6 for k in range(6)))
    blocks={b.attrib.get('Name'):b for sy in systems for b in sy.findall('Block')}
    edges={(prop(line,'Src'),q.text) for sy in systems for line in sy.findall('Line') for q in line.iter('P') if q.attrib.get('Name')=='Dst'}
    for source,sp,dest,dp in [('HP_Clock_Memory',1,'Segment_HP_Plan',6),('Execute_Segments',2,'Runtime_Contract_Gate',7),('Runtime_Contract_Gate',3,'HP_Clock_Memory',1),('HP_Supervisor',1,'Thermal_Dispatch',4),('Next_TES_Energy',1,'TES_Energy_Memory',1)]:
        ck('archive',source+'_to_'+dest,(blocks[source].attrib['SID']+f'#out:{sp}',blocks[dest].attrib['SID']+f'#in:{dp}') in edges)
    ck('archive','bounded_64_iterator',prop(blocks['For Iterator'],'IterationLimit')=='64')
    gate=(ROOT/'matlab/simulink/stateflow_contract_gate_v36.m').read_text()
    guard=(ROOT/'matlab/simulink/stateflow_supervisor_guard_v36.m').read_text()
    ck('archive','dimensioned_time_guard','age>=c(3)-ttol' in guard and 'age>=c(2)-ttol' in guard)
    ck('archive','dimensioned_time_monitor',all(v in gate for v in ['abs(z(28)-z(27)-span)<=ttol','abs(z(3)-offset)<=ttol','abs(offset-dt)<=ttol','abs(clock(2)-prevAge)<=ttol']))
    ck('archive','dimensioned_COP_temperature_monitor','abs(z(15)-expectedCOP)<=ctol' in gate and 'abs(z(22)-(cfg(10)+z(4)/cfg(9)))<=ktol' in gate)
    # Representative physical flows and energies vs preserved newer verified v32.
    legacy=json.loads((folder/'legacy_mat_audit_v36.json').read_text())
    lm={r['file']:r for r in legacy}
    ck('legacy','six_saved_v32_comparisons',len(legacy)==6)
    for c in cases[:6]:
        value=lm[c['id']+'_v32_comparison.mat'];old=matrix(value['dispatch'],len(c['inputs']))
        ck('legacy',c['id']+'_v32_success',not value['error_message'])
        for i,yy in enumerate(old):
            actual=ti[c['id'],i]
            ck('legacy',f'{c["id"]}_{i}_verified_reference',all(near(actual[name],yy[k]) for k,name in enumerate(PORTS+HP) if k!=21))
    # Re-evaluate closed-cycle partition invariance using observed traces.
    for family in ['fallback','initial_capacity']:
        base=ledger[family+'_h_4']
        for dt in [2,1,.5,.25,.125]:
            value=ledger[f'{family}_h_{dt:g}']
            ck('partition',f'{family}_{dt}',all(near(value[k],base[k]) for k in ['E','electric','unmet']) and all(time_near(a,b) for a,b in zip(value['clock'],base['clock'])))
        ck('partition',family+'_zero_unmet',near(base['unmet'],0))
    # Synthetic QA challenges, never counted as actual model fault execution.
    import copy
    for c in [cases[0],cases[-1]]:
        anchor=next(r for r in ss if r['scenario_id']==c['id'] and float(r['Duration_h'])>0)
        ck('synthetic',c['id']+'_clean',laws(anchor,c['inputs'][0],c['p']))
        badcopy=copy.deepcopy(anchor);badcopy['HP_Age_End_h']=float(anchor['HP_Age_End_h'])+.01
        ck('synthetic',c['id']+'_reject_time',not laws(badcopy,c['inputs'][0],c['p']))
    for path in (folder/'source_snapshot').glob('*.m'):
        current=ROOT/'matlab/simulink'/path.name
        if not current.is_file():current=ROOT/'matlab/+dchr/+components'/path.name
        ck('artifact',path.name+'_source_binding',digest(path)==digest(current))
    summary=json.loads((folder/'summary_v36.json').read_text());checks=rows(folder/'assertions_v36.csv')
    ck('artifact','observed_batch_exit',receipt['exit_code']==0 and 'run_stateflow_admissibility_v36' in receipt['command'])
    ck('artifact','summary_assertions',summary['failed']==0 and summary['passed']==len(checks) and all(r['passed'] in ['1','true'] for r in checks))
    ck('artifact','summary_counts',summary['scenarios']==len(cases) and summary['intervals']==len(tt) and summary['positive_segments']==sum(float(s['Duration_h'])>0 for s in ss))
    previous={}
    for pattern in ['Stateflow_admissibility_manifest_v35_*.json','Stateflow_manifest_v34_*.json','Stateflow_fallback_manifest_v33_*.json','Stateflow_manifest_v32_*.json',
                    'TES_event_manifest_v31_*.json','Stateflow_manifest_v30_*.json','Stateflow_fault_manifest_v29_*.json']:
        for path in (ROOT/'audit').glob(pattern):
            for item in json.loads(path.read_text(encoding='utf-8-sig'))['files']:previous[item['path']]=item
    for name,item in previous.items():
        path=Path(name);path=path if path.is_absolute() else ROOT/path
        ck('preservation',name,path.is_file() and digest(path)==item['sha256'] and path.stat().st_size==item['bytes'])
    counts={g:dict(passed=sum(c['passed'] for c in cc),failed=sum(not c['passed'] for c in cc)) for g,cc in groups.items()}
    out=folder/('independent_QA_v36_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json')
    report=dict(version='0.36',model_version='0.36',counts=counts,checks=groups,experiment_ledger=ledger,
        model_sha256=digest(model),reviewer_sha256=digest(Path(__file__)),previous_unique_entries=len(previous),
        conclusion='Dimensional tolerance repair passes executed implementation QA',
        evidence_class='independent_algorithm_artifact_QA_not_separate_agent_review',physical_validation=False,article_replication=False)
    out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(counts,indent=2));print('QA='+str(out.relative_to(ROOT)))
    assert not sum(v['failed'] for v in counts.values()),'Independent QA failure'


if __name__=='__main__':main()
