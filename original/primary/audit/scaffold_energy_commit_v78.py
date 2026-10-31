"""Create additive v78 tooling; immutable v75/v77 thermal implementation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def write(name,text):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)

builder=(ROOT/'matlab/simulink/build_temporal_commit_v77.m').read_text()
builder=builder.replace('build_temporal_commit_v77','build_energy_commit_v78').replace('DCHR_Earliest_Dispatch_Stateflow_v77','DCHR_Earliest_Dispatch_Stateflow_v78')
anchor="f=Stateflow.EMFunction(ch);f.Name='earliest_mode_v73';"
builder=builder.replace(anchor,"f=Stateflow.EMFunction(ch);f.Name='monitor_energy_commit_v78';f.Position=[1250 800 380 90];f.Script=fileread(fullfile(here,'monitor_energy_commit_v78.m'));\n"+anchor)
builder=builder.replace('monitor_temporal_commit_v77(horizon_input,policy_input,retained_memory,core);','monitor_energy_commit_v78(horizon_input,policy_input,retained_memory,core);')
builder=builder.replace('v77 pre-commit temporal-monitored','v78 pre-commit energy/temporal-monitored').replace('BUILT_TEMPORAL_COMMIT_STATEFLOW_V77','BUILT_ENERGY_COMMIT_STATEFLOW_V78')
write('matlab/simulink/build_energy_commit_v78.m',builder)
batch=(ROOT/'audit/run_temporal_commit_v77.ps1').read_text().replace('run_temporal_commit_v77','run_energy_commit_v78')
write('audit/run_energy_commit_v78.ps1',batch)
h=(ROOT/'matlab/run_temporal_commit_v77.m').read_text()
h=h.replace('run_temporal_commit_v77','run_energy_commit_v78').replace('build_temporal_commit_v77','build_energy_commit_v78')
h=h.replace('DCHR_Earliest_Dispatch_Stateflow_v77','DCHR_Earliest_Dispatch_Stateflow_v78').replace('DCHR_Earliest_Dispatch_Stateflow_v75','DCHR_Earliest_Dispatch_Stateflow_v77')
h=h.replace('v77','v78').replace('V77','V78').replace('0.77','0.78').replace('bitwise_saved_v75','bitwise_saved_v77')
h=h.replace('monitor_temporal_commit_v78','monitor_energy_commit_v78')
h=h.replace("original=kernel.Script;", "original=kernel.Script;\npriorCh=rt.find('-isa','Stateflow.Chart','Path',[prior '/Six_Mode_Interval_Dispatch']);\npriorKernel=priorCh.find('-isa','Stateflow.EMFunction','Name','earliest_dispatch_kernel_v75');\nassert(strcmp(priorKernel.Script,original));")
h=h.replace("if strcmp(f.operation,'toggle'),rhs=", "if strcmp(f.operation,'negative'),rhs='-1';\n    elseif strcmp(f.operation,'toggle'),rhs=")
h=h.replace("expected=['v78 ' f.expected];", "priorKernel.Script=strrep(original,anchor,[char(anchor) injection]);\n    [~,legacy]=execute(prior,a);priorKernel.Script=original;\n    expected=['v78 ' f.expected];")
h=h.replace("if strcmp(f.operation,'toggle'),expectedTrace", "if strcmp(f.operation,'negative'),expectedTrace(end,col)=-1;\n    elseif strcmp(f.operation,'toggle'),expectedTrace")
h=h.replace("record([f.id '_bypass_is_exact_single_fault'],isequal(bypass,expectedTrace));", "record([f.id '_bypass_is_exact_single_fault'],isequal(bypass,expectedTrace));\n    record([f.id '_saved_v77_monitor_accepts_same_fault'],isequal(legacy,expectedTrace));")
h=h.replace("'trace',bypass,'expected_text'", "'trace',bypass,'legacy_trace',legacy,'expected_text'")
h=h.replace("'prior_trace'}", "'prior_trace','legacy_trace'}")
h=h.replace("record('restored_kernel',strcmp(kernel.Script,original));", "record('restored_kernel',strcmp(kernel.Script,original));\nrecord('restored_prior_kernel',strcmp(priorKernel.Script,original));")
write('matlab/run_energy_commit_v78.m',h)

q=(ROOT/'audit/temporal_commit_v77.py').read_text()
q=q.replace('temporal_commit_v77','energy_commit_v78').replace('Temporal_commit','Energy_commit').replace('v77','v78').replace('V77','V78').replace('0.77','0.78')
q=q.replace('monitor_temporal_commit_v78','monitor_energy_commit_v78')
q=q.replace("from temporal_reporting_v76 import", "from energy_checks_v78 import energy_checks\nfrom temporal_reporting_v76 import")
start=q.index('    spec=json.loads(',q.index('def prepare():'))
end=q.index("    folder=ROOT/'results'",start)
q=q[:start]+'''    spec=json.loads((ROOT/'results/temporal_commit_v77_20261012T123639_894788Z/spec.json').read_text())
    controls=[('negative_power',[124],'negative','port domain'),
        ('HP_capacity',[124],'shift','port capacity'),
        ('HP_allocation',[124],'smallshift','HP allocation'),
        ('demand_allocation',[129],'shift','demand allocation'),
        ('forcing',[130,131],'shift','forcing binding'),
        ('negative_energy',[132,133],'negative','energy domain'),
        ('heat_energy',[132,133],'shift','port energy binding'),
        ('charge_loss',[140,141],'shift','efficiency loss binding'),
        ('source_energy',[134,135],'shift','HP first law'),
        ('auxiliary_energy',[150,151],'shift','auxiliary binding'),
        ('standing_energy',[138,139],'shift','segment first law'),
        ('segment_offset',[152,153],'shift','segment offsets'),
        ('interval_energy',[15,16],'shift','interval totals'),
        ('cumulative_energy',[31,32],'shift','cumulative totals'),
        ('origin',[51,52],'shift','origin binding'),
        ('stored_residual',[53,54],'shift','cumulative first law')]
    faults=[dict(id=id,columns=cols,local_columns=[],operation=op,expected=expected,event=0) for id,cols,op,expected in controls]
    spec.update(version='0.78',scope='SAVED_STATEFLOW_PRECOMMIT_ENERGY_AND_TEMPORAL_MONITOR',faults=faults)
'''+q[end:]
# Add monitor dependency and QA helpers to the immutable source snapshot.
q=q.replace("'audit/scaffold_energy_commit_v78.py','audit/energy_commit_v78.py']", "'audit/scaffold_energy_commit_v78.py','audit/energy_commit_v78.py','audit/energy_checks_v78.py',\n     'audit/Energy_commit_derivation_v78.md']")
q=q.replace("NEW+PRIOR_FILES+['audit/temporal_reporting_v76.py']", "NEW+PRIOR_FILES+['audit/temporal_reporting_v76.py','matlab/simulink/monitor_temporal_commit_v77.m']")
q=q.replace("for c in temporal_checks(r):", "for c in energy_checks(r)+temporal_checks(r):")
q=q.replace("cs=temporal_checks(bad);changed=[]", "cs=energy_checks(bad);changed=[]")
q=q.replace("check('isolated_bypass',f['id'],", "check('legacy_acceptance',f['id'],rows(f['legacy_trace'])==mutated)\n            check('isolated_bypass',f['id'],")
q=q.replace("'matlab/simulink/monitor_energy_commit_v78.m','matlab/simulink/earliest_dispatch_kernel_v75.m'", "'matlab/simulink/monitor_energy_commit_v78.m','matlab/simulink/monitor_temporal_commit_v77.m','matlab/simulink/earliest_dispatch_kernel_v75.m'")
q=q.replace("by_id={r['id']:r for r in report['runs']}", "by_id={r['id']:r for r in report['runs']}\n        for col in [123,129,131,137,149,151,14,30,50,52]:\n            bad=copy.deepcopy(by_id['temporal_chain']);bad['trace'][1][col]+=1\n            selfchecks.append(dict(name=f'synthetic_energy_{col+1}',passed=any(not c['passed'] for c in energy_checks(bad))))")
q=q.replace('Original-MAT QA independent of the production temporal monitor.', 'Original-MAT QA independent of the production energy and temporal monitors.')
write('audit/energy_commit_v78.py',q)
release=(ROOT/'audit/verify_temporal_commit_release_v77.py').read_text().replace('temporal_commit_v77','energy_commit_v78').replace('v77','v78')
write('audit/verify_energy_commit_release_v78.py',release)
print('Added immutable additive v78 builder, batch, harness and review tools.')
