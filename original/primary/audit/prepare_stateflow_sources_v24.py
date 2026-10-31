"""Create additive v24 MATLAB sources from the preserved v22 controller."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'matlab/simulink'
for name in ['stateflow_choose_mode', 'stateflow_allocate']:
    source=(HERE/(name+'_v22.m')).read_text(encoding='utf-8').replace('v22','v24')
    for old,new in [('u','hpPorts'),('E','energyStart'),('p','cfgPorts')]:
        source=re.sub(r'\b'+old+r'\b',new,source)
    with (HERE/(name+'_v24.m')).open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(source)

source=(HERE/'build_dispatch_stateflow_v22.m').read_text(encoding='utf-8').replace('v22','v24')
source=source.replace('% Build a new operational Stateflow model; never replace the v14 baseline.',
    '% Build additive v24 runtime-contract model; preserve v14 and v22.')
source=source.replace("    'coder.extrinsic(''dchr_stateflow_hp_v24'');\\nu=zeros(8,1);\\n'",
    "    'coder.extrinsic(''dchr_stateflow_hp_v24'');\\nu=zeros(8,1);\\n'")
source=source.replace('function u=hp_adapter(x,E,p,h)', 'function u=hp_adapter(x,E,p,h,model_dt)')
source=source.replace('u=dchr_stateflow_hp_v24(x,E,p,h);', 'u=dchr_stateflow_hp_v24(x,E,p,h,model_dt);')
marker="add_block('sflib/Chart',[mdl '/Thermal_Dispatch']"
addition="""add_block('simulink/Sources/Constant',[mdl '/Integration_Step'], ...
    'Value','dchr_dt_v24','Position',[25 300 160 335]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Runtime_Contract_Gate'], ...
    'Position',[700 65 900 205]);
monitor=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);
monitor.Script=fileread(fullfile(here,'stateflow_contract_gate_v24.m'));
"""
assert marker in source
source=source.replace(marker,addition+marker)
source=source.replace("ch.Description='v22 six-state", "ch.Description='v24 six-state")
source=source.replace("[mdl '/Dispatch_Trace'], ...", "[mdl '/Dispatch_Trace'], ...")
source=source.replace("'Position',[750 70 900 100]", "'Position',[1020 70 1170 100]")
source=source.replace("'Position',[705 260 755 300]", "'Position',[930 260 980 300]")
source=source.replace("add_line(mdl,'Thermal_Dispatch/1','Next_TES_Energy/1','autorouting','on');",
    """add_line(mdl,'Integration_Step/1','Verified_HP_Component/5','autorouting','on');
add_line(mdl,'Thermal_Dispatch/1','Runtime_Contract_Gate/1','autorouting','on');
add_line(mdl,'Verified_HP_Component/1','Runtime_Contract_Gate/2','autorouting','on');
add_line(mdl,'TES_Energy_Memory/1','Runtime_Contract_Gate/3','autorouting','on');
add_line(mdl,'TES_and_Boiler_Parameters/1','Runtime_Contract_Gate/4','autorouting','on');
add_line(mdl,'Integration_Step/1','Runtime_Contract_Gate/5','autorouting','on');
add_line(mdl,'Runtime_Contract_Gate/1','Next_TES_Energy/1','autorouting','on');""")
source=source.replace("add_line(mdl,'Thermal_Dispatch/1','Dispatch_Trace/1','autorouting','on');",
    "add_line(mdl,'Runtime_Contract_Gate/1','Dispatch_Trace/1','autorouting','on');")
with (HERE/'build_dispatch_stateflow_v24.m').open('x',encoding='utf-8',newline='\n') as stream:
    stream.write(source)
print('Created additive v24 builder and both reviewed allocation helpers.')
