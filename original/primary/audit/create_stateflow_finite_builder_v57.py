"""Create an additive builder from the inspected, preserved v52 structure."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / 'matlab/simulink/build_dispatch_stateflow_v52.m').read_text()
dst = ROOT / 'matlab/simulink/build_dispatch_stateflow_v57.m'
assert not dst.exists(), 'Preserve existing versions.'
src = src.replace('build_dispatch_stateflow_v52()', 'build_dispatch_stateflow_v57()')
src = src.replace('DCHR_Dispatch_Stateflow_v52', 'DCHR_Dispatch_Stateflow_v57')
src = re.sub(r'dchr_(dt|stop|input|p|h|E0|c|m0)_v52', r'dchr_\1_v57', src)
src = re.sub(r'(clock_start_trace|clock_end_trace|segment_trace|dispatch_trace|plan_trace|energy_start_trace)_v52', r'\1_v57', src)
src = src.replace("assignin(mw,'dchr_input_v57',[0 6 35 75 0 45;1 0 35 75 5 45]);", "assignin(mw,'dchr_input_v57',[0 35 5 5 5 70 45 2 3 2 40 .8 .6 8 .5 .1 0 1]);")
src = src.replace("assignin(mw,'dchr_p_v57',[1 10 3 4 .9 .8 .1 5 .2 20 2]);", "assignin(mw,'dchr_p_v57',[1 10 3 4 .9 .8 .1 5.6 .2 20 2]);")
src = src.replace("add_block('simulink/Sources/Constant',[mdl '/HP_Parameters'],'Value','dchr_h_v57','Position',[20 170 150 200]);", '')
src = src.replace('Release 0.52:', 'Release 0.57: compiled finite-water interface;')
anchor = "connections={'Scenario_Input/1','Segment_HP_Plan/1';"
addition = """% Fixed-saturation finite-water boundary is computed inside the simulation.
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Finite_Temperature_Boundary'],'Position',[160 550 360 660]);
f=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Finite_Temperature_Boundary']);
f.Script=fileread(fullfile(here,'stateflow_finite_boundary_v57.m'));
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Finite_Port_Accounting'],'Position',[750 600 930 760]);
f=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Finite_Port_Accounting']);
f.Script=fileread(fullfile(here,'stateflow_finite_ports_v57.m'));
add_block('simulink/Sinks/To Workspace',[mdl '/Finite_Boundary_Trace'],'VariableName','finite_boundary_trace_v57', ...
    'SaveFormat','Timeseries','Position',[1030 610 1190 640]);
add_block('simulink/Sinks/To Workspace',[mdl '/Finite_Accounting_Trace'],'VariableName','finite_accounting_trace_v57', ...
    'SaveFormat','Timeseries','Position',[1030 700 1190 730]);
connections={'Finite_Temperature_Boundary/1','Segment_HP_Plan/1';"""
assert anchor in src
src = src.replace(anchor, addition)
src = src.replace("'HP_Parameters/1','Segment_HP_Plan/4'", "'Finite_Temperature_Boundary/2','Segment_HP_Plan/4'")
src = src.replace("'Scenario_Input/1','Runtime_Contract_Gate/3'", "'Finite_Temperature_Boundary/1','Runtime_Contract_Gate/3'")
src = src.replace("'HP_Parameters/1','Runtime_Contract_Gate/5'", "'Finite_Temperature_Boundary/2','Runtime_Contract_Gate/5'")
src = src.replace("'Runtime_Contract_Gate/3','Clock_End_Trace/1'};", """'Runtime_Contract_Gate/3','Clock_End_Trace/1'; ...
    'Scenario_Input/1','Finite_Temperature_Boundary/1';'TES_Parameters/1','Finite_Temperature_Boundary/2'; ...
    'Control_Parameters/1','Finite_Temperature_Boundary/3'; ...
    'Runtime_Contract_Gate/1','Finite_Port_Accounting/1';'Runtime_Contract_Gate/2','Finite_Port_Accounting/2'; ...
    'Finite_Temperature_Boundary/3','Finite_Port_Accounting/3';'Scenario_Input/1','Finite_Port_Accounting/4'; ...
    'TES_Parameters/1','Finite_Port_Accounting/5';'Integration_Step/1','Finite_Port_Accounting/6'; ...
    'Finite_Temperature_Boundary/3','Finite_Boundary_Trace/1';'Finite_Port_Accounting/1','Finite_Accounting_Trace/1'};""")
src = src.replace('% Additive model: 64 bounded segment slots and physical-hour HP supervisor.',
    '% Additive finite-water runtime model; held macro inputs, inherited v52 dispatch.\n% This is not continuous tank-linked condenser/variable-power propagation.')
dst.write_text(src, encoding='utf-8')
print(dst.relative_to(ROOT).as_posix())
