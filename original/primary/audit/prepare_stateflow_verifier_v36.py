"""Additive independent verifier with corrected-release expectations."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'audit/verify_stateflow_admissibility_v35.py').read_text().replace('v35','v36').replace("version='0.35'", "version='0.36'")
s=s.replace('Reproducing a monitor failure does not confer model acceptance.',
            'Implementation acceptance only; no primary replication or physical validation.')
s=s.replace('summary_v36.json', 'summary_v36.json')
s=s.replace("model_version='0.34'", "model_version='0.36'")
s=s.replace('DCHR_Dispatch_Stateflow_v34.slx','DCHR_Dispatch_Stateflow_v36.slx')
# Require hours within the declared 64-ulp budget, independently evaluated.
s=s.replace('def laws(s,x,p):','''def time_near(a,b):
    a=float(a);b=float(b)
    budget=64*math.ulp(max(1,abs(a),abs(b)))
    return math.isfinite(a) and math.isfinite(b) and budget<=1e-8 and abs(a-b)<=budget

def laws(s,x,p):
    if not time_near(s['HP_Age_End_h'],float(s['HP_Age_Start_h'])+float(s['Duration_h'])):return False''')
start=s.index("    faults=json.loads((folder/'fault_evidence_v36.json')")
end=s.index('    for path in (folder/\'source_snapshot\').glob(\'*.m\'):',start)
s=s[:start]+'''    faults=json.loads((folder/'fault_evidence_v36.json').read_text())
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
''' + s[end:]
s=s.replace("'Stateflow_manifest_v34_*.json'", "'Stateflow_admissibility_manifest_v35_*.json','Stateflow_manifest_v34_*.json'")
s=s.replace("conclusion='OPEN dimensional clock tolerance defect independently reproduced'", "conclusion='Dimensional tolerance repair passes executed implementation QA'")
# All handoffs checked against actual exported plans and strict hour budgets.
point="            ck('numeric',f'{c[\"id\"]}_{i}_partition',near(sum(float(s['Duration_h']) for s in slots),p[0]))"
s=s.replace(point,'''            offset=0.;previousE=float(r['Storage_E_Start_MWh']);on,age=clock
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
            ck('time',f'{c["id"]}_{i}_final_clock',float(r['HP_Latch_End'])==on and time_near(r['HP_Age_End_h'],age))''')
path=ROOT/'audit/verify_stateflow_v36.py';assert not path.exists();path.write_text(s,encoding='utf-8')
print('Prepared independent v36 reviewer.')
