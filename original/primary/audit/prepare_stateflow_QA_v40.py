"""Adapt preserved v39 independent reviewer to a zero-failure repair gate."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
source = (ROOT/'audit/verify_stateflow_hp_domain_v39.py').read_text()
source = source.replace('v39', 'v40').replace('v38', 'v40').replace('0.39', '0.40').replace('0.38', '0.40')
source = source.replace('a, b = 4*(1-p), 4*p', "nominal = D(q.get('nominal_cop', 4.))\n        a, b = nominal*(1-p), nominal*p")
source = source.replace('Q*(1-1/(a+b*Q/cap))', 'Q*((a+b*Q/cap-1)/(a+b*Q/cap))')
source = source.replace("ck('execution',q['id']+'_not_rejected',not a['rejected']);hp=a['output'];expected=root(q)", """expected=root(q)
        should_reject=q.get('expected_reject',False)
        ck('execution',q['id']+'_expected_domain',a['rejected']==should_reject)
        if should_reject:
            ck('equation',q['id']+'_oracle_unrepresentable_electricity',expected is not None and expected['heat']>0 and expected['electric']==0)
            ck('execution',q['id']+'_specific_resolution_diagnostic',a['error_identifier']=='DCHR:v40:HPResolution')
            ledger.append(dict(id=q['id'],kind=q['kind'],expected=expected,actual_rejection=a))
            continue
        hp=a['output']
        ck('execution',q['id']+'_not_rejected',not a['rejected'])
        if a['rejected']:continue
        ck('numeric',q['id']+'_positive_representable_flows',not hp['available'] or
           hp['heat_output_MW']>0 and hp['electric_MW']>0 and hp['source_used_MW']>0)""")
start = source.index('    controls={r[\'id\']:r for r in plant_ledger}')
end = source.index('    for p in (folder/\'source_snapshot\').glob', start)
source = source[:start]+"""    controls={r['id']:r for r in plant_ledger}
    for bits in (90,120):
        wide,tight=controls[f'wide_request_{bits}'],controls[f'tight_request_{bits}']
        ck('repair',f'{bits}_wide_positive_maximum',near(wide['actual_HP_heat_MW'],wide['expected_HP_heat_MW']) and wide['actual_HP_heat_MW']>0)
        ck('repair',f'{bits}_no_lost_service',wide['actual_unmet_MW']==tight['actual_unmet_MW']==0)
    pairs={}
    for q,a in zip(spec['hp_probes'],probes):
        if q.get('pair'):pairs.setdefault(q['pair'],[]).append(a)
    for name,pair in pairs.items():
        ck('repair',name+'_source_limited_request_invariance',len(pair)==2 and all(not a['rejected'] for a in pair) and
           near(pair[0]['output']['heat_output_MW'],pair[1]['output']['heat_output_MW']) and
           pair[0]['output']['heat_output_MW']>0)
    faults=read(folder/'runtime_faults_v40.json')
    ck('execution','30_actual_runtime_fault_rejections',len(faults)==30 and all(a['rejected'] for a in faults))
    for a in faults:
        b=saved[a['id']+'_fault']
        ck('artifact',a['id']+'_fault_MAT_binding',a['error_message']==b['error_message'] and a['phase']==b['phase'] and a['time_h']==b['time_h'])
        ck('execution',a['id']+'_execution_rejection',b['rejected'] and b['phase']=='Execution')
    for key in ('dispatch','segments','clock_start','clock_end'):
        ck('repair','fault_restoration_'+key,saved['pre_fault_clean'][key]==saved['post_fault_clean'][key])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx'
    old=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v38.slx'
    ck('preservation','v38_checkpoint_hash',sha(old)==read(ROOT/'STATUS_stateflow_v38.json')['model_sha256'])
    ck('artifact','new_v40_model',sha(model)!=sha(old))
"""+source[end:]
source = source.replace("ck('defect_reproduction','fixed_80_search_in_bound_source','for iteration=1:80' in component and 'q=lower;' in component)", "ck('repair','source_relative_adjacent_search_in_bound_source','sourceFraction=' in component and 'middle==lower || middle==upper' in component and 'for iteration=1:80' not in component)")
source = source.replace("implementation_status='FAIL_OPEN_HP_DYNAMIC_RANGE',new_model=False", "implementation_status='PASS_SCOPED_HP_REPAIR',new_model=True")
source = source.replace("assert comparison['failed']>0,'Expected defect was not reproduced; reassess conclusion'", "assert comparison['failed']==0,'HP repair analytic implementation comparisons failed'")
source = source.replace('Implementation comparison FAIL counts stay separate from successful defect\nreproduction QA.', 'Every analytic implementation comparison must pass for repair acceptance.')
path = ROOT/'audit/verify_stateflow_hp_domain_v40.py'
assert not path.exists(); path.write_text(source,encoding='utf-8')
print('Prepared independent exact-input analytic repair reviewer v40')
