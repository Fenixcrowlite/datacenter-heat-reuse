"""Independent saved-model numeric, clock, archive and MAT evidence QA.
No production MATLAB imports. Synthetic reviewer checks are labelled separately.
"""
import argparse,copy,csv,hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from stateflow_reference_v34 import dispatch,SEG34,PORTS,HP,legacy_dispatch
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvrows(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def near(a,b):
    a=math.nan if a is None else float(a);b=math.nan if b is None else float(b)
    return math.isnan(a) and math.isnan(b) or math.isfinite(a) and math.isfinite(b) and abs(a-b)<=2e-9+2e-11*abs(b)
def prop(e,n):return e.findtext(f"P[@Name='{n}']",default='')
def matrix(v,n):return [v] if n==1 and v and not isinstance(v[0],list) else v
def segment_laws(s,x,p):
    if any(not math.isfinite(float(s[k])) for k in SEG34 if k!='COP'):return False
    v=lambda k:float(s[k]);span=v('Duration_h');e=v('Energy_Start_MWh');end=v('Energy_Next_MWh')
    qc=v('Storage_Charge_MW');qd=v('Storage_Discharge_MW');gas=v('Gas_Heat_MW');direct=v('HP_Direct_MW')
    mode=v('Mode');on=v('HP_Latch');age=v('HP_Age_Start_h')
    if not (mode==int(mode) and 0<=mode<=5 and on in (0,1) and span>=0 and age>=0):return False
    if not near(v('HP_Age_End_h'),age+span):return False
    if not (-2e-9<=e<=p[1]+2e-9 and -2e-9<=end<=p[1]+2e-9):return False
    if not (0<=qc<=p[2]+2e-9 and 0<=qd<=p[3]+2e-9 and 0<=gas<=p[10]+2e-9 and qc*qd==0):return False
    if span==0:return mode==0 and all(v(k)==0 for k in SEG34[5:14]+SEG34[16:21]) and e==end
    wanted=5 if v('Unmet_Heat_MW')>0 else 4 if gas>0 else 3 if qd>0 else 2 if qc>0 else 1 if direct>0 else 0
    if mode!=wanted or (not on and v('HP_Heat_MW')!=0) or (on and v('HP_Heat_MW')<=0):return False
    if not near(x[3],direct+qd+gas+v('Unmet_Heat_MW')):return False
    if not near(v('HP_Heat_MW'),v('HP_Electric_MW')+v('HP_Source_Used_MW')):return False
    if not near(v('HP_Heat_MW'),direct+qc):return False
    power=p[4]*qc-qd/p[5]
    for j in range(9):
        t=span*j/8;r=math.exp(-p[6]*t);phi=t if not p[6] else -math.expm1(-p[6]*t)/p[6]
        epath=e*r+power*phi
        if not (-2e-9<=epath<=p[1]+2e-9 and (not qd or epath>=p[7]-2e-9)):return False
    if not near(v('Storage_Standing_Loss_MWh'),e+power*span-end):return False
    closure=e+(v('HP_Electric_MW')+v('HP_Source_Used_MW')+gas-v('Supplied_Heat_MW'))*span-end-sum(v(k) for k in SEG34[16:19])
    return near(closure,0) and near(v('System_Balance_Residual_MWh'),closure)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder');parser.add_argument('receipt');args=parser.parse_args()
    folder=Path(args.folder).resolve();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    spec=json.loads((folder/'source_snapshot/spec/cases.json').read_text());cases=spec['cases']
    totals=csvrows(folder/'stateflow_trace_v34.csv');segments=csvrows(folder/'stateflow_segments_v34.csv')
    legacy=csvrows(folder/'stateflow_v32_comparison.csv');mat=json.loads((folder/'mat_audit_v34.json').read_text())
    summary=json.loads((folder/'acceptance_summary_v34.json').read_text());groups={}
    def ck(group,name,ok):groups.setdefault(group,[]).append(dict(name=name,passed=bool(ok)))
    keys=[(c['id'],i) for c in cases for i in range(len(c['inputs']))]
    ck('numeric','ordered_interval_keys',[(r['scenario_id'],int(r['step'])) for r in totals]==keys)
    ck('numeric','ordered_slot_keys',[(r['scenario_id'],int(r['step']),int(r['segment'])) for r in segments]==[(a,i,s) for a,i in keys for s in range(1,65)])
    modes=set();ledger={};validmat={r['id']:r for r in mat['valid_cases']};oldmat={r['id']:r for r in mat['legacy_cases']}
    segindex={(a,i):[] for a,i in keys}
    for s in segments:segindex[(s['scenario_id'],int(s['step']))].append(s)
    totalindex={(r['scenario_id'],int(r['step'])):r for r in totals}
    for c in cases:
        e=c['initial_energy_MWh'];m=c['initial_clock'];p=c['p'];n=len(c['inputs']);vr=validmat[c['id']]
        ck('artifact',c['id']+'_MAT_success',vr['error_message']=='')
        ym=matrix(vr['y'],n);sm=matrix(vr['segments'],n);pm=matrix(vr['plan'],n)
        cm=matrix(vr['clock_start'],n);ce=matrix(vr['clock_end'],n)
        for i,x in enumerate(c['inputs']):
            row=totalindex[(c['id'],i)];ss=segindex[(c['id'],i)];y,expected,endclock=dispatch(e,x,p,c['h'],m,c['c']);prefix=f'{c["id"]}_{i}'
            for j,name in enumerate(PORTS+HP):
                ck('numeric',prefix+'_'+name,near(row[name],y[j]));ck('artifact',prefix+'_MAT_'+name,near(row[name],ym[i][j]))
            ck('numeric',prefix+'_energy_memory',near(row['Storage_E_Start_MWh'],e))
            ck('numeric',prefix+'_time',near(row['Time_h'],i*p[0]))
            ck('artifact',prefix+'_MAT_time_energy',near(vr['time_h'][i] if isinstance(vr['time_h'],list) else vr['time_h'],i*p[0]) and near(vr['energy_start'][i] if isinstance(vr['energy_start'],list) else vr['energy_start'],e))
            for j,name in enumerate(['HP_Latch_Start','HP_Age_Start_h','HP_Latch_End','HP_Age_End_h']):
                value=(m+endclock)[j];ck('numeric',prefix+'_'+name,near(row[name],value))
                ck('artifact',prefix+'_MAT_'+name,near(row[name],(cm[i]+ce[i])[j]))
            positive=[s for s in ss if float(s['Duration_h'])>0]
            ck('numeric',prefix+'_positive_count',len(positive)==len(expected))
            offset=0.;a=e;state,age=m
            for j,s in enumerate(ss):
                ck('numeric',prefix+f'_slot{j}_laws',segment_laws(s,x,p))
                ck('artifact',prefix+f'_slot{j}_MAT',all(near(s[name],sm[i][j*28+k]) for k,name in enumerate(SEG34)))
                ck('numeric',prefix+f'_slot{j}_handoff',near(s['Offset_h'],offset) and near(s['Energy_Start_MWh'],a))
                duration=float(s['Duration_h']);on=float(s['HP_Latch']);startage=float(s['HP_Age_Start_h'])
                reason=pm[i][j*18+16]
                if on!=state:
                    allowed=(on==1 and reason==3 and float(s['Energy_Start_MWh'])<=c['c'][0]+2e-9 and age>=c['c'][2]-2e-9) or (
                        on==0 and ((reason==2 and float(s['Energy_Start_MWh'])>=p[1]-2e-9 and age>=c['c'][1]-2e-9) or reason==1))
                    ck('numeric',prefix+f'_slot{j}_transition',allowed and startage==0)
                else:ck('numeric',prefix+f'_slot{j}_clock_continuity',near(startage,age) and reason==0)
                if duration:
                    modes.add(int(float(s['Mode'])));exp=expected[j]
                    ck('numeric',prefix+f'_slot{j}_oracle',all(near(s[name],want) for name,want in zip(SEG34,exp)))
                state=on;age=float(s['HP_Age_End_h']);offset+=duration;a=float(s['Energy_Next_MWh'])
            ck('numeric',prefix+'_complete_partition',near(offset,p[0]))
            ck('numeric',prefix+'_integrated_powers',all(near(row[name],sum(float(s[name])*float(s['Duration_h']) for s in ss)/p[0]) for name in ['HP_Electric_MW','HP_Heat_MW','Unmet_Heat_MW','Storage_Discharge_MW','Gas_Heat_MW']))
            e=y[7];m=endclock
        ledger[c['id']]=dict(E=e,clock=m,electric=sum(float(totalindex[(c['id'],i)]['HP_Electric_MW'])*p[0] for i in range(n)),
             unmet=sum(float(totalindex[(c['id'],i)]['Unmet_Heat_MW'])*p[0] for i in range(n)),
             discharge=sum(float(totalindex[(c['id'],i)]['Storage_Discharge_MW'])*p[0] for i in range(n)))
        oldrows=[r for r in legacy if r['scenario_id']==c['id']]
        if oldrows:
            a=c['initial_energy_MWh'];om=matrix(oldmat[c['id']]['y'],n)
            for i,(x,row) in enumerate(zip(c['inputs'],oldrows)):
                old,_=legacy_dispatch(a,x,p,c['h']);a=old[7]
                ck('legacy',c['id']+f'_{i}_saved_v32',all(near(row[name],want) and near(row[name],om[i][j]) for j,(name,want) in enumerate(zip(PORTS+HP,old))))
    ck('numeric','six_modes',modes==set(range(6)))
    # Alternate closed-cycle recurrence, no generic event loop or root bisection.
    for family,e0 in [('fallback',9.9),('initial_capacity',10.)]:
        ref=ledger[family+'_h_4']
        for dt in (2,1,.5,.25,.125):
            a=ledger[f'{family}_h_{dt:g}']
            ck('alternate',f'{family}_partition_{dt}',all(near(a[k],ref[k]) for k in ['E','electric','unmet','discharge']) and all(near(u,v) for u,v in zip(a['clock'],ref['clock'])))
        R=cases[10]['c'][0];lam=.1;Aon=27.;Aoff=-37.5
        first=math.log((Aon-e0)/(Aon-10))/lam if e0<10 else 0.
        off=math.log((10-Aoff)/(R-Aoff))/lam;on=math.log((Aon-R)/(Aon-10))/lam
        remaining=4.-first;on_time=first;off_time=0.;state=0;age=0.;e=10.
        while remaining>1e-12:
            length=off if state==0 else on;spent=min(remaining,length)
            e=(Aoff+(10-Aoff)*math.exp(-lam*spent)) if state==0 else (Aon+(R-Aon)*math.exp(-lam*spent))
            if state:on_time+=spent
            else:off_time+=spent
            remaining-=spent;age=spent
            if remaining>1e-12:state=1-state
        ck('alternate',family+'_closed_cycle',near(ref['E'],e) and near(ref['electric'],on_time*6/3.7) and near(ref['discharge'],off_time*3) and near(ref['unmet'],0) and near(ref['clock'][1],age) and ref['clock'][0]==state)
        oldsum=sum(float(r['Unmet_Heat_MW'])*4 for r in legacy if r['scenario_id']==family+'_h_4')
        ck('alternate',family+'_defect_removed',ref['unmet']==0 and oldsum>0)
    # Saved archive structure, functions and connection bindings.
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v34.slx'
    with ZipFile(model) as z:
        systems=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/systems/') and n.endswith('.xml')]
        charts=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
    blocks={b.attrib.get('Name'):b for s in systems for b in s.findall('Block')}
    edges={(prop(line,'Src'),q.text) for s in systems for line in s.findall('Line') for q in line.iter('P') if q.attrib.get('Name')=='Dst'}
    for source,sp,dest,dp in [('HP_Clock_Memory',1,'Segment_HP_Plan',6),('Execute_Segments',2,'Runtime_Contract_Gate',7),('Runtime_Contract_Gate',3,'HP_Clock_Memory',1),('HP_Supervisor',1,'Thermal_Dispatch',4),('HP_Supervisor',1,'Clock',1),('Select_Segment',1,'HP_Supervisor',1),('Thermal_Dispatch',1,'Trace',1),('Next_TES_Energy',1,'TES_Energy_Memory',1)]:
        ck('archive',source+'_to_'+dest,(blocks[source].attrib['SID']+f'#out:{sp}',blocks[dest].attrib['SID']+f'#in:{dp}') in edges)
    ck('archive','bounded_held_iterator',prop(blocks['For Iterator'],'IterationLimit')=='64' and (prop(blocks['For Iterator'],'ResetStates') or 'held')=='held')
    ck('archive','clock_memory',blocks['HP_Clock_Memory'].attrib['BlockType']=='UnitDelay')
    bindings=set()
    for chartname,names in [('Execute_Segments/Thermal_Dispatch',{'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'}),('Execute_Segments/HP_Supervisor',{'HP_ON','HP_OFF'})]:
        chart=next(ch for ch in charts if prop(ch,'name')==chartname)
        child=chart.find('Children');states=[s for s in child.findall('state') if prop(s,'type')=='OR_STATE']
        ck('archive',chartname+'_states',{prop(s,'labelString').splitlines()[0] for s in states}==names)
        if 'HP_Supervisor' in chartname:
            ck('archive','physical_hours_not_tick',all('age=age+s(1);' in prop(s,'labelString') and 'age=age+1;' not in prop(s,'labelString') for s in states))
            ck('archive','five_supervisor_transitions',len(child.findall('transition'))==5)
            labels=[prop(t,'labelString') for t in child.findall('transition')]
            for target in (0,1):
                ck('archive',f'HP_target_{target}_guard',
                   f'[s(15)=={target} && stateflow_supervisor_guard_v34({target},s,p,c,age)]' in labels)
        else:
            labels=[prop(t,'labelString') for t in child.findall('transition')]
            ck('archive','37_thermal_transitions',len(labels)==37)
            ck('archive','every_thermal_transition_guarded',sum(not v for v in labels)==1 and
               all(labels.count(f'[stateflow_choose_mode_v34(segmentInput,parameters)=={k}]')==6 for k in range(6)))
        for function in child.findall('state'):
            eml=function.find('eml')
            if eml is not None:
                script=prop(eml,'script')
                if not script:continue  # ordinary states also contain empty eml tags
                # Identify by signature rather than SLX label formatting.
                for fname in ['stateflow_allocate_v34','stateflow_collect_v34','stateflow_choose_mode_v34','stateflow_supervisor_guard_v34']:
                    if fname in script.splitlines()[0]:
                        bindings.add(fname)
                        ck('archive',fname+'_source_binding',script.strip()==(ROOT/'matlab/simulink'/f'{fname}.m').read_text().strip())
    ck('archive','all_four_embedded_functions_bound',bindings=={'stateflow_allocate_v34','stateflow_collect_v34','stateflow_choose_mode_v34','stateflow_supervisor_guard_v34'})
    scripts=[prop(e,'script') for chart in charts for e in chart.iter('eml')]
    ck('archive','runtime_monitor_embedded_source',
       (ROOT/'matlab/simulink/stateflow_contract_gate_v34.m').read_text().strip() in [s.strip() for s in scripts])
    ck('archive','normal_mode_host_planner',any("coder.extrinsic('dchr_segment_plan_v34')" in s for s in scripts))
    for name in ['dchr_segment_plan_v34.m','stateflow_supervisor_guard_v34.m','stateflow_contract_gate_v34.m',
                 'stateflow_allocate_v34.m','stateflow_collect_v34.m','stateflow_choose_mode_v34.m','build_dispatch_stateflow_v34.m',
                 'dchr_stateflow_hp_v30.m']:
        ck('artifact',name+'_executed_source_snapshot',digest(ROOT/'matlab/simulink'/name)==digest(folder/'source_snapshot'/name))
    ck('archive','model_snapshot_digest',digest(model)==digest(folder/'source_snapshot'/model.name))
    faults=json.loads((folder/'fault_evidence_v34.json').read_text());mf={f['id']:f for f in mat['faults']}
    ck('faults','30_actual_faults',len(faults)==30 and len(mf)==30)
    for f in faults:
        actual=mf[f['id']]
        ck('faults',f['id'],f['rejected'] and actual['phase']=='Execution' and actual['error_message']==f['error_message'] and actual['time_h']==f['time_h'])
    ck('faults','restored_saved_simulations',mat['restored_segments_equal'] and mat['restored_clock_equal'] and not mat['restored_error'])
    receipt=json.loads(Path(args.receipt).read_text(encoding='utf-8-sig'))
    ck('artifact','observed_batch_zero_exit',receipt['exit_code']==0 and 'run_stateflow_acceptance_v34' in receipt['command'])
    assertions=csvrows(folder/'stateflow_assertions_v34.csv')
    ck('artifact','assertion_summary',len(assertions)==summary['passed'] and summary['failed']==0 and all(r['passed'] in ['1','true'] for r in assertions))
    ck('artifact','scenario_interval_slot_counts',summary['scenarios']==len(cases) and summary['intervals']==len(totals) and summary['slots']==len(segments))
    # Synthetic reviewer challenges are not actual-model tests.
    anchor=next(s for s in segments if float(s['Duration_h'])>0 and float(s['HP_Heat_MW'])>0)
    case=next(c for c in cases if c['id']==anchor['scenario_id']);x=case['inputs'][int(anchor['step'])]
    ck('synthetic','clean_reviewer_anchor',segment_laws(anchor,x,case['p']))
    for key,value in [('Mode',.5),('HP_Latch',.5),('HP_Age_End_h',float(anchor['HP_Age_End_h'])+1),('HP_Heat_MW',float(anchor['HP_Heat_MW'])+1),('Duration_h',math.nan),('Energy_Next_MWh',11),('Storage_Discharge_MW',1)]:
        bad=copy.deepcopy(anchor);bad[key]=value;ck('synthetic','reject_'+key,not segment_laws(bad,x,case['p']))
    # Earlier immutable evidence preservation using all saved prior manifests.
    previous={}
    prior=['Stateflow_fallback_manifest_v33_20261010T024241_191718Z.json',
           'Stateflow_manifest_v32_20261010T023036_007737Z.json',
           'TES_event_manifest_v31_20261009T214244_178000Z.json',
           'Stateflow_manifest_v30_20261009T213038_443584Z.json',
           'Stateflow_fault_manifest_v29_20261009T204014_224631Z.json']
    for name in prior:
        path=ROOT/'audit'/name
        manifest=json.loads(path.read_text(encoding='utf-8-sig'))
        for item in manifest.get('files',[]):
            if 'sha256' in item and 'path' in item:previous[item['path']]=item
    for name,item in previous.items():
        path=Path(name);path=path if path.is_absolute() else ROOT/path
        ck('preservation',name,path.is_file() and digest(path)==item['sha256'])
    counts={g:dict(passed=sum(c['passed'] for c in vv),failed=sum(not c['passed'] for c in vv)) for g,vv in groups.items()}
    report=dict(version='0.34',timestamp_utc=stamp,result_directory=str(folder.relative_to(ROOT)),model_sha256=digest(model),
        evidence_class='independent_algorithm_artifact_QA_not_separate_human_or_agent_review',counts=counts,checks=groups,
        experiment_ledger=ledger,previous_unique_entries=len(previous),physical_validation=False,article_replication=False,
        reviewer_sha256=digest(Path(__file__)))
    out=ROOT/'audit'/f'Stateflow_QA_v34_{stamp}.json';out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(counts,indent=2));print('QA_OUTPUT='+str(out.relative_to(ROOT)))
    assert not sum(v['failed'] for v in counts.values()),'Independent QA failure'
if __name__=='__main__':main()
