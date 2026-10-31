"""Create additive executable v24 acceptance, preserving v22 evidence/code."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'
source=(HERE/'run_stateflow_acceptance_v22.m').read_text(encoding='utf-8').replace('v22','v24')
source=source.replace("'stateflow_qa_vectors_v24.csv'", "'stateflow_qa_vectors_v22.csv'")
source=source.replace("structure.chart_output_line.Outport(1),'DstBlockHandle'", 
    "get_param([mdl '/Runtime_Contract_Gate'],'LineHandles').Outport(1),'DstBlockHandle'")
source=source.replace("'chart_port_drives_TES_feedback'", "'contract_gate_drives_TES_feedback'")
source=source.replace("'Actual chart port destinations include next-energy selector and trace sink.'", 
    "'Accepted contract-gate destinations include next-energy selector and trace sink.'")
source=source.replace("'Chart output is wired to energy selector/feedback and numeric trace.'", 
    "'Chart output is wired into executable contract gate before feedback/trace.'")
source=source.replace('invalids();',"""monitor=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);
record('saved_model_embeds_contract_gate',strcmp(monitor.Script, ...
    fileread(fullfile(here,'stateflow_contract_gate_v24.m'))), ...
    'Actual saved .slx embeds reviewed first-law/runtime monitor source.');
rejectSummary=run_stateflow_rejections_v24(mdl,outputDir);
record('all_invalid_cases_simulated_and_rejected',rejectSummary.rejected==rejectSummary.cases && ...
    rejectSummary.expected_cause_observed==rejectSummary.cases && rejectSummary.accepted_invalid_traces==0, ...
    'Actual simulations rejected independent invalid-domain/clock cases with expected DCHR cause.');""")
start=source.index('    function invalids()')
end=source.index('\nend\n\nfunction c=configuration',start)
source=source[:start]+source[end:]
source=source.replace("'version','0.22'", "'version','0.24'")
source=source.replace("'simulink_executed',true", "'runtime_invalid_cases',rejectSummary.cases, ...\n    'runtime_invalid_cases_rejected',rejectSummary.rejected, ...\n    'simulink_executed',true")
with (HERE/'run_stateflow_acceptance_v24.m').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(source)
print('Created v24 actual-model acceptance and rejection handoff.')
