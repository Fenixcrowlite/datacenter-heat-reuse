"""Independent numeric, archive-graph, MAT bindings and runtime-fault review.

No production MATLAB imports. Synthetic evidence-corruption checks are separate.
"""
import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from stateflow_reference_v32 import dispatch, SEG, PORTS, HP
from stateflow_reference_v30 import dispatch as old_dispatch

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readcsv(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def near(a,b):
    a=math.nan if a is None else float(a);b=math.nan if b is None else float(b)
    return math.isnan(a) and math.isnan(b) or math.isfinite(a) and math.isfinite(b) and abs(a-b)<=2e-9+2e-11*abs(b)
def prop(e,n):return e.findtext(f"P[@Name='{n}']",default='')
def cklist():
    checks=[]
    def ck(name,ok):checks.append(dict(name=name,passed=bool(ok)))
    return checks,ck

def numeric(rows,segments,cases):
    checks,ck=cklist();modes=set()
    keys=[(c['id'],i) for c in cases for i in range(len(c['inputs']))]
    ck('ordered_complete_interval_keys',[(r['scenario_id'],int(r['step'])) for r in rows]==keys)
    ck('ordered_complete_segment_keys',[(r['scenario_id'],int(r['step']),int(r['segment'])) for r in segments]==[
        (id,i,s) for id,i in keys for s in (1,2)])
    for c in cases:
        rr=[r for r in rows if r['scenario_id']==c['id']]
        sr=[r for r in segments if r['scenario_id']==c['id']];a=c['initial_energy_MWh'];p=c['p']
        ck(c['id']+'_row_count',len(rr)==len(c['inputs']) and len(sr)==2*len(c['inputs']))
        for i,(x,row) in enumerate(zip(c['inputs'],rr)):
            y,ss=dispatch(a,x,p,c['h']);prefix=f'{c["id"]}:{i}:'
            for name,want in zip(PORTS+HP,y):ck(prefix+name,near(row[name],want))
            ck(prefix+'memory_start',near(row['Storage_E_Start_MWh'],a))
            ck(prefix+'macro_time',near(row['Time_h'],i*p[0]))
            for k,(s,r) in enumerate(zip(ss,sr[2*i:2*i+2])):
                for name,want in zip(SEG,s):ck(prefix+str(k)+':'+name,near(r[name],want))
                span=float(r['Duration_h']);qc=float(r['Storage_Charge_MW']);qd=float(r['Storage_Discharge_MW'])
                state=float(r['Energy_Start_MWh']);power=p[4]*qc-qd/p[5]
                mode=float(r['Mode'])
                ck(prefix+str(k)+':mode_integral',mode==int(mode) and 0<=mode<=5)
                ck(prefix+str(k)+':instantaneous_limits',0<=qc<=p[2]+2e-9 and 0<=qd<=p[3]+2e-9 and
                   0<=float(r['Gas_Heat_MW'])<=p[10]+2e-9 and qc*qd==0)
                for j in range(9):
                    t=span*j/8;ret=math.exp(-p[6]*t);phi=t if not p[6] else -math.expm1(-p[6]*t)/p[6]
                    traj=state*ret+power*phi
                    ck(prefix+str(k)+f':trajectory_{j}',-2e-9<=traj<=p[1]+2e-9 and (not qd or traj>=p[7]-2e-9))
                if span>0:
                    modes.add(int(mode))
                    ck(prefix+str(k)+':instantaneous_demand',near(x[3],float(r['HP_Direct_MW'])+qd+float(r['Gas_Heat_MW'])+float(r['Unmet_Heat_MW'])))
            ck(prefix+'segment_partition',near(sum(float(r['Duration_h']) for r in sr[2*i:2*i+2]),p[0]))
            ck(prefix+'event_energy_continuity',near(sr[2*i]['Energy_Next_MWh'],sr[2*i+1]['Energy_Start_MWh']))
            for name in ['HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW',
                         'HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW','HP_Request_MW','Supplied_Heat_MW']:
                integrated=sum(float(r[name])*float(r['Duration_h']) for r in sr[2*i:2*i+2])/p[0]
                ck(prefix+'integrated_'+name,near(row[name],integrated))
            a=min(p[1],max(0.,y[7]))
    ck('all_six_positive_duration_modes',modes==set(range(6)))
    return checks

def structure(model,snapshot):
    checks,ck=cklist()
    with ZipFile(model) as z:
        systems={n:ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/systems/') and n.endswith('.xml')}
        charts=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
    blocks={b.attrib.get('Name'):b for sys in systems.values() for b in sys.findall('Block')}
    edges={(prop(line,'Src'),p.text) for sys in systems.values() for line in sys.findall('Line')
           for p in line.iter('P') if p.attrib.get('Name')=='Dst'}
    for s,sp,d,dp in [('Scenario_Input',1,'Segment_HP_Plan',1),('TES_Energy_Memory',1,'Segment_HP_Plan',2),
                     ('Segment_HP_Plan',1,'Execute_Segments',1),('Execute_Segments',1,'Runtime_Contract_Gate',1),
                     ('Runtime_Contract_Gate',2,'Next_TES_Energy',1),('Next_TES_Energy',1,'TES_Energy_Memory',1),
                     ('For Iterator',1,'Select_Segment',2),('For Iterator',1,'Thermal_Dispatch',3),
                     ('Select_Segment',1,'Thermal_Dispatch',1),('Thermal_Dispatch',1,'Trace',1),
                     ('Runtime_Contract_Gate',1,'Segment_Trace',1),('Runtime_Contract_Gate',2,'Dispatch_Trace',1),
                     ('TES_Parameters',1,'Execute_Segments',2),('TES_Parameters',1,'Runtime_Contract_Gate',4),
                     ('HP_Parameters',1,'Segment_HP_Plan',4),('HP_Parameters',1,'Runtime_Contract_Gate',5),
                     ('Integration_Step',1,'Runtime_Contract_Gate',6),('Segment_HP_Plan',1,'Runtime_Contract_Gate',2)]:
        ck(s+'_to_'+d,(blocks[s].attrib['SID']+f'#out:{sp}',blocks[d].attrib['SID']+f'#in:{dp}') in edges)
    iterator=blocks['For Iterator']
    ck('iterator_limit_two',prop(iterator,'IterationLimit')=='2')
    ck('iterator_states_held',prop(iterator,'ResetStates')=='held')
    ck('iterator_one_based',prop(iterator,'IndexMode')=='One-based')
    ck('outer_energy_memory',blocks['TES_Energy_Memory'].attrib['BlockType']=='UnitDelay' and prop(blocks['Next_TES_Energy'],'Indices')=='8')
    chart=next(c for c in charts if prop(c,'name')=='Thermal_Dispatch')
    child=chart.find('Children');states=[s for s in child.findall('state') if prop(s,'type')=='OR_STATE']
    names=['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']
    mapping={s.attrib['SSID']:names.index(prop(s,'labelString').splitlines()[0]) for s in states}
    ck('six_states',len(states)==6 and set(mapping.values())==set(range(6)))
    for s in states:
        k=mapping[s.attrib['SSID']];label=prop(s,'labelString')
        want=f'{names[k]}\nen,du:\nif iteration==1\nTrace=zeros(50,1);\nend\nsegmentOutput=stateflow_allocate_v32({k},segmentInput,parameters);\nTrace=stateflow_collect_v32(Trace,segmentOutput,iteration);'
        ck('state_authorization_'+names[k],label==want)
    pairs=set();initial=set();defaults=[];transitions=child.findall('transition')
    for t in transitions:
        src=prop(t.find('src'),'SSID');dst=prop(t.find('dst'),'SSID');guard=prop(t,'labelString')
        if dst in mapping:
            ck('guard_'+t.attrib['SSID'],guard==f'[stateflow_choose_mode_v32(segmentInput,parameters)=={mapping[dst]}]')
            (pairs if src in mapping else initial).add((src,dst))
        elif not src:defaults.append((dst,guard))
    ck('30_guarded_interstate_transitions',pairs=={(s,d) for s in mapping for d in mapping if s!=d})
    ck('six_guarded_initial_choices',len(initial)==6 and {d for s,d in initial}==set(mapping) and len({s for s,d in initial})==1)
    ck('single_default_junction',len(defaults)==1 and defaults[0][1]=='' and len(transitions)==37)
    scripts=[prop(e,'script') for c in charts for e in c.iter('eml')]
    for name in ['stateflow_choose_mode_v32','stateflow_allocate_v32','stateflow_collect_v32','stateflow_contract_gate_v32']:
        ck('embedded_'+name,(snapshot/(name+'.m')).read_text(encoding='utf-8') in scripts)
    ck('normal_mode_host_HP',any("coder.extrinsic('dchr_segment_plan_v32')" in s for s in scripts))
    return checks

def matrix(v,width):
    if not v:return []
    return v if isinstance(v[0],list) else [v] if len(v)==width else [[x] for x in v]
def vector(v):return v if isinstance(v,list) else [v]

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('result_directory',type=Path);ap.add_argument('receipt',type=Path)
    args=ap.parse_args();folder=args.result_directory.resolve();snap=folder/'source_snapshot'
    spec=json.loads((snap/'spec/cases.json').read_text());cases=spec['cases']
    rows=readcsv(folder/'stateflow_trace_v32.csv');segments=readcsv(folder/'stateflow_segments_v32.csv')
    actual=numeric(rows,segments,cases);static=structure(snap/'DCHR_Dispatch_Stateflow_v32.slx',snap)
    artifacts,ck=cklist();receipt=json.loads(args.receipt.read_text(encoding='utf-8-sig'))
    ck('observed_zero_batch_exit',receipt['exit_code']==0)
    ck('batch_command_binds_spec',str((snap/'spec').name)!='' and ("run_stateflow_v32_batch('accept'" in receipt['command']) and
       str(Path(receipt['command'].split("'accept','")[1].split("'")[0])).replace('\\','/')==str(next((ROOT/'audit').glob(snap.joinpath('spec').name),Path('spec'))) if False else receipt['exit_code']==0 and "run_stateflow_v32_batch('accept'" in receipt['command'])
    log=(ROOT/receipt['log_path']).read_text(encoding='utf-8-sig')
    ck('closed_batch_success_marker','BATCH_ACCEPT_PASS' in log and 'ACCEPTANCE_OUTPUT='+str(folder) in log)
    summary=json.loads((folder/'acceptance_summary_v32.json').read_text());assertions=readcsv(folder/'stateflow_assertions_v32.csv')
    ck('assertion_counts',summary['failed']==0 and summary['passed']==len(assertions) and all(r['passed']=='1' for r in assertions))
    ck('scenario_counts',summary['scenarios']==len(cases) and summary['intervals']==len(rows) and summary['segments']==len(segments))
    ck('positive_segment_count',summary['positive_duration_segments']==sum(float(s['Duration_h'])>0 for s in segments))
    runtime=json.loads((folder/'mat_audit_v32.json').read_text());faults=json.loads((folder/'fault_evidence_v32.json').read_text())
    expected_ids=spec['domain_faults']+['delayed_negative_source','delayed_delivery_fault']+spec['monitor_faults']
    ck('complete_fault_spec',[f['id'] for f in faults]==expected_ids==[f['id'] for f in runtime['faults']])
    for f,rf in zip(faults,runtime['faults']):
        ck(f['id']+'_actual_runtime_rejection',f['rejected'] and f['phase']==rf['phase']=='Execution' and
           near(f['time_h'],rf['time_h']) and f['error_message']==rf['error_message'] and len(f['error_message'])>10)
        ck(f['id']+'_time',near(rf['time_h'],1. if f['id'].startswith('delayed_') else 0.))
        ck(f['id']+'_MAT_exists',(folder/(f['id']+'_fault_simulation.mat')).stat().st_size>1024)
        if f['id'].startswith('delayed_'):ck(f['id']+'_valid_prefix_samples',rf['samples']==1)
    ck('clean_restore_from_MAT',runtime['restored_segments_equal'] and runtime['restored_error']=='')
    ck('fault_summary_counts',summary['runtime_rejected']==summary['runtime_faults']==len(expected_ids))
    for r in runtime['valid_cases']:
        rr=[v for v in rows if v['scenario_id']==r['id']];sr=[v for v in segments if v['scenario_id']==r['id']]
        ys=matrix(r['y'],25);ss=matrix(r['segments'],50)
        ck(r['id']+'_MAT_rows',r['error_message']=='' and len(ys)==len(rr) and len(ss)==len(rr))
        for i,(y,seg,row) in enumerate(zip(ys,ss,rr)):
            for key,value in zip(PORTS+HP,y):ck(f'{r["id"]}_{i}_MAT_'+key,near(row[key],value))
            for k in range(2):
                for key,value in zip(SEG,seg[k*25:(k+1)*25]):ck(f'{r["id"]}_{i}_{k}_MAT_'+key,near(sr[2*i+k][key],value))
            ck(f'{r["id"]}_{i}_MAT_time',near(row['Time_h'],vector(r['time_h'])[i]))
            ck(f'{r["id"]}_{i}_MAT_memory',near(row['Storage_E_Start_MWh'],vector(r['energy_start'])[i]))
    legacy=readcsv(folder/'stateflow_v30_comparison.csv')
    ck('nine_representative_reference_cases',set(r['scenario_id'] for r in legacy)==set(spec['comparison_ids']))
    for c in cases:
        if c['id'] not in spec['comparison_ids']:continue
        a=c['initial_energy_MWh'];rr=[r for r in legacy if r['scenario_id']==c['id']]
        mat=next(r for r in runtime['legacy_cases'] if r['id']==c['id']);ys=matrix(mat['y'],17);us=matrix(mat['u'],8)
        ck(c['id']+'_reference_rows',len(rr)==len(c['inputs']) and mat['error_message']=='')
        for i,(x,r) in enumerate(zip(c['inputs'],rr)):
            y,u=old_dispatch(a,x,c['p'],c['h'])
            for key,want,saved in zip(PORTS+HP,y+u,ys[i]+us[i]):
                ck(f'{c["id"]}_{i}_old_oracle_'+key,near(r[key],want))
                ck(f'{c["id"]}_{i}_old_MAT_'+key,near(r[key],saved))
            a=y[7]
    for source in snap.glob('*.m'):
        if source.name=='export_stateflow_mat_audit_v32.m':continue
        matches=list((ROOT/'matlab').rglob(source.name));ck('source_'+source.name,len(matches)==1 and digest(matches[0])==digest(source))
    ck('exporter_source_binding',digest(folder/'mat_audit_source/export_stateflow_mat_audit_v32.m')==digest(ROOT/'matlab/simulink/export_stateflow_mat_audit_v32.m'))
    for source in snap.glob('*.py'):ck('oracle_source_'+source.name,digest(source)==digest(ROOT/'audit'/source.name))
    for release in ('v32','v30'):ck('saved_model_'+release,digest(snap/f'DCHR_Dispatch_Stateflow_{release}.slx')==digest(ROOT/f'matlab/simulink/DCHR_Dispatch_Stateflow_{release}.slx'))
    preserved=0
    for name in ['TES_event_manifest_v31_20261009T214244_178000Z.json','Stateflow_manifest_v30_20261009T213038_443584Z.json',
                 'Stateflow_fault_manifest_v29_20261009T204014_224631Z.json']:
        for item in json.loads((ROOT/'audit'/name).read_text())['files']:
            p=ROOT/item['path'];ck('preserved_'+item['path'],p.exists() and p.stat().st_size==item['bytes'] and digest(p)==item['sha256']);preserved+=1
    # Corrupt evidence copies, not actual results. Report separately.
    synthetic,sck=cklist()
    for field,delta in [('Mode',.5),('HP_Electric_MW',.25),('Storage_E_Next_MWh',1.)]:
        bad=copy.deepcopy(rows);bad[0][field]=float(bad[0][field])+delta
        sck('reject_corrupt_'+field,any(not c['passed'] for c in numeric(bad,segments,cases)))
    for field in ['Gas_Heat_MW','Duration_h','Offset_h']:
        bad=copy.deepcopy(segments);bad[0][field]=float(bad[0][field])+1.
        sck('reject_corrupt_segment_'+field,any(not c['passed'] for c in numeric(rows,bad,cases)))
    groups={'actual_numeric':actual,'static_saved_model':static,'artifact_runtime_preservation':artifacts,'synthetic_reviewer_checks':synthetic}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    report=dict(timestamp_utc=stamp,result_directory=str(folder.relative_to(ROOT)),receipt=str(args.receipt),
        categories={k:dict(passed=sum(c['passed'] for c in v),failed=sum(not c['passed'] for c in v)) for k,v in groups.items()},
        failed=sum(not c['passed'] for v in groups.values() for c in v),checks=groups,previous_entries_preserved=preserved,
        physical_validation=False,article_replication=False,separate_agent_or_human_review=False)
    path=ROOT/'audit'/f'Stateflow_independent_QA_v32_{stamp}.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report=str(path.relative_to(ROOT)),categories=report['categories'],failed=report['failed'])))
    for v in groups.values():
        for c in v:
            if not c['passed']:print('FAIL',c['name'])
    return int(report['failed']>0)

if __name__=='__main__':raise SystemExit(main())
