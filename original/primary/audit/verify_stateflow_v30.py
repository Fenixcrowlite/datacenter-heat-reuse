"""Independent numeric, saved-SLX graph and evidence-integrity review.

Imports only the independent Python oracle; no production MATLAB/kernel code.
Runtime phase and MAT-to-CSV bindings are read from a separate MAT audit export.
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
from stateflow_reference_v30 import dispatch, PORTS, HP

ROOT=Path(__file__).resolve().parents[1]
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def prop(e,name): return e.findtext(f"P[@Name='{name}']",default='')
def readcsv(path):
    with path.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))
def near(a,b):
    a,b=float(a),float(b)
    return (math.isnan(a) and math.isnan(b)) or (math.isfinite(a) and math.isfinite(b) and abs(a-b)<=2e-9+2e-11*abs(b))

def trace_checks(rows,cases):
    checks=[]
    def ck(n,ok): checks.append(dict(name=n,passed=bool(ok)))
    keys=[(c['id'],i) for c in cases for i in range(len(c['inputs']))]
    ck('complete_ordered_scenario_samples',[(r['scenario_id'],round(float(r['Time_h'])/next(c['p'][0] for c in cases if c['id']==r['scenario_id']))) for r in rows]==keys)
    ck('exact_total_intervals',len(rows)==len(keys))
    modes=set()
    for case in cases:
        group=[r for r in rows if r['scenario_id']==case['id']]
        ck(case['id']+'_complete',len(group)==len(case['inputs']))
        a=case['initial_energy_MWh'];p=case['p']
        for i,(x,row) in enumerate(zip(case['inputs'],group)):
            y,u=dispatch(a,x,p,case['h']);prefix=f"{case['id']}:{i}:"
            for name,expected in zip(PORTS+HP,y+u): ck(prefix+name,near(row[name],expected))
            ck(prefix+'time',near(row['Time_h'],i*p[0]))
            ck(prefix+'energy_memory',near(row['Storage_E_Start_MWh'],a))
            # Sample continuous trajectory at 17 intermediate times using actual ports.
            charge=float(row['Storage_Charge_MW']);dis=float(row['Storage_Discharge_MW'])
            power=p[4]*charge-dis/p[5]
            for point in range(17):
                t=point*p[0]/16;r=math.exp(-p[6]*t)
                phi=t if not p[6] else -math.expm1(-p[6]*t)/p[6]
                state=a*r+power*phi
                ck(prefix+f'trajectory_{point}',-2e-9<=state<=p[1]+2e-9 and (dis==0 or state>=p[7]-2e-9))
            external=a+(charge-dis)*p[0]-float(row['Storage_E_Next_MWh'])-sum(float(row[n]) for n in PORTS[8:11])
            ck(prefix+'external_port_first_law',abs(external)<2e-9)
            modes.add(int(float(row['Mode'])));a=y[7]
    ck('all_six_modes',modes==set(range(6)))
    return checks

def structure_checks(model,snapshot):
    checks=[]
    def ck(n,ok):checks.append(dict(name=n,passed=bool(ok)))
    with ZipFile(model) as z:
        system=ET.fromstring(z.read('simulink/systems/system_root.xml'))
        charts=[ET.fromstring(z.read(n)) for n in z.namelist() if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
    blocks={b.attrib['Name']:b for b in system.findall('Block')}
    edges={(prop(l,'Src'),p.text) for l in system.findall('Line') for p in l.iter('P') if p.attrib.get('Name')=='Dst'}
    connections=[('Scenario_Input',1,'Verified_HP_Component',1),('Verified_HP_Component',1,'Thermal_Dispatch',1),
                 ('TES_Energy_Memory',1,'Verified_HP_Component',2),('TES_Energy_Memory',1,'Thermal_Dispatch',2),
                 ('Thermal_Dispatch',1,'Runtime_Contract_Gate',1),('Verified_HP_Component',1,'Runtime_Contract_Gate',2),
                 ('TES_Energy_Memory',1,'Runtime_Contract_Gate',3),('TES_and_Boiler_Parameters',1,'Runtime_Contract_Gate',4),
                 ('Integration_Step',1,'Runtime_Contract_Gate',5),('Runtime_Contract_Gate',1,'Next_TES_Energy',1),
                 ('Runtime_Contract_Gate',1,'Dispatch_Trace',1),('Next_TES_Energy',1,'TES_Energy_Memory',1)]
    for s,sp,d,dp in connections:
        ck(f'{s}_to_{d}',(blocks[s].attrib['SID']+f'#out:{sp}',blocks[d].attrib['SID']+f'#in:{dp}') in edges)
    ck('unit_delay',blocks['TES_Energy_Memory'].attrib['BlockType']=='UnitDelay')
    ck('endpoint_energy_feedback',prop(blocks['Next_TES_Energy'],'Indices')=='8')
    ck('no_interpolation',prop(blocks['Scenario_Input'],'Interpolate')=='off')
    chart=next(c for c in charts if prop(c,'name')=='Thermal_Dispatch')
    child=chart.find('Children');states=[s for s in child.findall('state') if prop(s,'type')=='OR_STATE']
    names=['IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND']
    mapping={s.attrib['SSID']:names.index(prop(s,'labelString').splitlines()[0]) for s in states}
    ck('six_operating_states',len(states)==6 and set(mapping.values())==set(range(6)))
    for s in states:
        i=mapping[s.attrib['SSID']]
        ck(names[i]+'_entry_during_allocation',prop(s,'labelString')==f'{names[i]}\nen,du:\ny=stateflow_allocate_v30({i},u,E,p);')
    transitions=child.findall('transition');pairs=set();initial=set();default=[]
    for t in transitions:
        src=prop(t.find('src'),'SSID');dst=prop(t.find('dst'),'SSID');guard=prop(t,'labelString')
        if dst in mapping:
            ck('destination_guard_'+t.attrib['SSID'],guard==f'[stateflow_choose_mode_v30(u,E,p)=={mapping[dst]}]')
            (pairs if src in mapping else initial).add((src,dst))
        elif not src:default.append((dst,guard))
    ck('30_complete_guarded_transitions',pairs=={(s,d) for s in mapping for d in mapping if s!=d})
    ck('six_initial_choices',len(initial)==6 and len({s for s,d in initial})==1 and {d for s,d in initial}==set(mapping))
    ck('single_default_junction',len(default)==1 and default[0][1]=='' and {default[0][0]}=={s for s,d in initial} and len(transitions)==37)
    ck('discrete_common_interval',prop(chart,'sampleTime')==prop(blocks['TES_Energy_Memory'],'SampleTime')==prop(blocks['Scenario_Input'],'SampleTime')=='dchr_dt_v30')
    scripts=[prop(e,'script') for c in charts for e in c.iter('eml')]
    for name in ('stateflow_choose_mode_v30','stateflow_allocate_v30','storage_kernel_v30','stateflow_contract_gate_v30'):
        ck('embedded_'+name,(snapshot/(name+'.m')).read_text(encoding='utf-8') in scripts)
    return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('result_directory',type=Path)
    args=parser.parse_args();folder=args.result_directory.resolve();snap=folder/'source_snapshot'
    cases=json.loads((snap/'spec/cases.json').read_text())['cases']
    rows=readcsv(folder/'stateflow_trace_v30.csv');actual=trace_checks(rows,cases)
    static=structure_checks(snap/'DCHR_Dispatch_Stateflow_v30.slx',snap)
    integrity=[]
    def ck(name,ok):integrity.append(dict(name=name,passed=bool(ok)))
    for path in snap.glob('*.m'):
        if path.name=='export_stateflow_mat_audit_v30.m': continue # pre-run copy, not a simulation dependency
        matches=list((ROOT/'matlab').rglob(path.name));ck('source_binding_'+path.name,len(matches)==1 and digest(matches[0])==digest(path))
    ck('MAT_exporter_used_source_binding',digest(folder/'mat_audit_source/export_stateflow_mat_audit_v30.m')==digest(ROOT/'matlab/simulink/export_stateflow_mat_audit_v30.m'))
    for release in ('v30','v28'):
        name=f'DCHR_Dispatch_Stateflow_{release}.slx';ck('saved_model_hash_'+release,digest(snap/name)==digest(ROOT/'matlab/simulink'/name))
    ck('oracle_binding',digest(snap/'stateflow_reference_v30.py')==digest(ROOT/'audit/stateflow_reference_v30.py'))
    summary=json.loads((folder/'acceptance_summary_v30.json').read_text());assertions=readcsv(folder/'stateflow_assertions_v30.csv')
    ck('matlab_assertion_counts',summary['failed']==0 and summary['passed']==len(assertions)==summary['checks'] and all(r['passed']=='1' for r in assertions))
    ck('summary_case_coverage',summary['scenarios']==len(cases) and summary['intervals']==len(rows))
    for case in cases:
        path=folder/(case['id']+'_simulation.mat');ck('MAT_saved_'+case['id'],path.is_file() and path.stat().st_size>1024)
    fault=json.loads((folder/'fault_evidence_v30.json').read_text());runtime=json.loads((folder/'mat_audit_v30.json').read_text())
    expected_fault_ids=['negative_source','negative_demand','delivery_above_cutoff','condenser_below_tank_max',
        'cutoff_above_capacity','negative_rate','invalid_efficiency','zero_heat_capacity','above_capacity_state',
        'negative_boiler','invalid_hp_backend','invalid_heating_lift','delayed_negative_source',
        'delayed_delivery_fault','corrupt_temperature','corrupt_usable_inventory','corrupt_next_energy','corrupt_standing_loss']
    ck('independent_fault_case_coverage',[f['id'] for f in fault]==expected_fault_ids)
    for f in fault:
        metadata=next(m for m in runtime['faults'] if m['id']==f['id'])
        delayed=f['id'].startswith('delayed_');prefix=int(delayed)
        ck(f['id']+'_execution_rejection',metadata['stop_event']=='DiagnosticError' and metadata['error_phase']=='Execution' and near(metadata['error_time_h'],prefix) and f['expected_diagnostic'] in metadata['error_message'])
        ck(f['id']+'_valid_prefix',metadata['samples']==prefix==f['actual_prefix_samples'] and f['passed'])
        ck(f['id']+'_diagnostic_binding',metadata['error_message']==f['diagnostic'])
    ck('clean_restart',runtime['clean_restart_samples']==2 and runtime['clean_restart_error']=='')
    ck('MAT_trace_case_coverage',[c['id'] for c in runtime['valid_cases']]==[c['id'] for c in cases])
    for case in runtime['valid_cases']:
        group=[r for r in rows if r['scenario_id']==case['id']]
        ck(case['id']+'_MAT_rows',case['samples']==len(group) and case['error_message']=='')
        ys,us,energies,times=case['y'],case['u'],case['energy_start'],case['time_h']
        if case['samples']==1:ys,us,energies,times=[ys],[us],[energies],[times]
        ck(case['id']+'_MAT_complete_shapes',len(ys)==len(us)==len(energies)==len(times)==len(group) and all(len(y)==17 for y in ys) and all(len(u)==8 for u in us))
        for i,(y,u,a,t) in enumerate(zip(ys,us,energies,times)):
            for name,v in zip(PORTS+HP+['Storage_E_Start_MWh','Time_h'],y+u+[a,t]):
                # JSON encodes NaN as null; operating COP is the only allowed NaN.
                ck(f"{case['id']}:{i}:MAT_{name}",near(group[i][name],math.nan if v is None else v))
    comparison=readcsv(folder/'active_flow_comparison_v30.csv')
    ck('eight_executed_comparisons',len(comparison)==8)
    for row in comparison:
        case=next(c for c in cases if c['id']==row['scenario_id']);dt=case['p'][0];power=float(row['internal_power_MW']);rate=case['p'][6]
        legacy=next(c for c in runtime['legacy_cases'] if c['id']==row['scenario_id'])
        ck(row['scenario_id']+'_actual_v28_MAT_binding',legacy['samples']==len(case['inputs']) and legacy['error_message']=='' and near(row['v28_end_MWh'],legacy['energy_end_MWh']))
        exact=case['initial_energy_MWh']*math.exp(-2*rate)+power*(-math.expm1(-2*rate)/rate)
        r=math.exp(-rate*dt);split=case['initial_energy_MWh']
        for _ in case['inputs']:split=split*r+power*dt
        ck(row['scenario_id']+'_exact_partition',near(row['v30_end_MWh'],exact))
        ck(row['scenario_id']+'_legacy_split',near(row['v28_end_MWh'],split))
        ck(row['scenario_id']+'_bias',near(row['v28_minus_v30_MWh'],split-exact))
    # Separate synthetic reviewer checks, never added to actual evidence counts.
    synthetic=[]
    mutations={'truncated_trace':lambda v:v.pop(),'temperature_corruption':lambda v:v[0].__setitem__('Storage_T_Next_C','99'),
               'false_loss':lambda v:v[0].__setitem__('Storage_Standing_Loss_MWh','1'),
               'false_mode':lambda v:v[0].__setitem__('Mode','5'),
               'false_COP':lambda v:v[2].__setitem__('COP','2'),
               'wrong_sample_time':lambda v:v[0].__setitem__('Time_h','1')}
    for name,mutation in mutations.items():
        bad=copy.deepcopy(rows);mutation(bad)
        synthetic.append(dict(name=name,passed=any(not c['passed'] for c in trace_checks(bad,cases))))
    sections={'actual_numeric':actual,'static_saved_model':static,'artifact_and_runtime_bindings':integrity,'synthetic_reviewer_checks':synthetic}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    report=dict(timestamp_utc=stamp,scope='Implementation evidence QA, not equipment validation or article replication',
                result_directory=str(folder.relative_to(ROOT)),model_sha256=digest(snap/'DCHR_Dispatch_Stateflow_v30.slx'),
                verifier_sha256=digest(Path(__file__)),sections={name:dict(passed=sum(c['passed'] for c in checks),
                failed=sum(not c['passed'] for c in checks),evidence_class=name,checks=checks) for name,checks in sections.items()})
    report['failed']=sum(s['failed'] for s in report['sections'].values())
    path=ROOT/'audit'/f'Stateflow_independent_QA_v30_{stamp}.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report=str(path.relative_to(ROOT)),failed=report['failed'],
                         sections={n:{k:v for k,v in s.items() if k!='checks'} for n,s in report['sections'].items()}),indent=2))
    return int(report['failed']>0)
if __name__=='__main__':raise SystemExit(main())
