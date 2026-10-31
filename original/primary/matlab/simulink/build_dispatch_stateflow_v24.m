function modelPath = build_dispatch_stateflow_v24()
% Build additive v24 runtime-contract model; preserve v14 and v22.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
mdl='DCHR_Dispatch_Stateflow_v24'; modelPath=fullfile(here,[mdl '.slx']);
assert(~isfile(modelPath),'DCHR:v24:ModelExists','Versioned model already exists.');
assert(license('test','Stateflow'),'DCHR:v24:StateflowUnavailable','Stateflow license unavailable.');
load_system('sflib'); new_system(mdl);
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
set_param(mdl,'Solver','FixedStepDiscrete','SolverType','Fixed-step', ...
    'FixedStep','dchr_dt_v24','StopTime','dchr_stop_v24','SimulationMode','normal', ...
    'ReturnWorkspaceOutputs','on','SaveTime','on','TimeSaveName','tout');
mw=get_param(mdl,'ModelWorkspace');
assignin(mw,'dchr_dt_v24',1); assignin(mw,'dchr_stop_v24',2);
assignin(mw,'dchr_input_v24',[0 6 35 70 5;1 0 35 70 6;2 0 35 70 10]);
assignin(mw,'dchr_p_v24',[1 10 3 4 .9 .8 .01 2]);
assignin(mw,'dchr_h_v24',[8 .45 1.2 8 .08 0 4 0 0]);
assignin(mw,'dchr_E0_v24',0);
add_block('simulink/Sources/From Workspace',[mdl '/Scenario_Input'], ...
    'VariableName','dchr_input_v24','Interpolate','off','OutputAfterFinalValue','Holding final value', ...
    'SampleTime','dchr_dt_v24', ...
    'Position',[25 55 160 90]);
add_block('simulink/Sources/Constant',[mdl '/TES_and_Boiler_Parameters'], ...
    'Value','dchr_p_v24','Position',[25 170 160 205]);
add_block('simulink/Sources/Constant',[mdl '/HP_Parameters'], ...
    'Value','dchr_h_v24','Position',[25 240 160 275]);
add_block('simulink/Discrete/Unit Delay',[mdl '/TES_Energy_Memory'], ...
    'InitialCondition','dchr_E0_v24','SampleTime','dchr_dt_v24','Position',[550 340 595 380]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Verified_HP_Component'], ...
    'Position',[235 60 395 165]);
rt=sfroot; hp=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Verified_HP_Component']);
hp.Script=sprintf(['function u=hp_adapter(x,E,p,h,model_dt)\n%%#codegen\n' ...
    'coder.extrinsic(''dchr_stateflow_hp_v24'');\nu=zeros(8,1);\n' ...
    'u=dchr_stateflow_hp_v24(x,E,p,h,model_dt);\nend\n']);
add_block('simulink/Sources/Constant',[mdl '/Integration_Step'], ...
    'Value','dchr_dt_v24','Position',[25 300 160 335]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Runtime_Contract_Gate'], ...
    'Position',[700 65 900 205]);
monitor=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);
monitor.Script=fileread(fullfile(here,'stateflow_contract_gate_v24.m'));
add_block('sflib/Chart',[mdl '/Thermal_Dispatch'],'Position',[460 65 660 205]);
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
ch.ActionLanguage='MATLAB'; ch.ChartUpdate='DISCRETE'; ch.SampleTime='dchr_dt_v24';
ch.ExecuteAtInitialization=false;
ch.Description='v24 six-state finite TES/HP/boiler dispatch. Normal-mode host HP component; state actions drive all delivery ports.';
data(ch,'u','Input',1,'[8 1]'); data(ch,'E','Input',2,'1');
data(ch,'p','Input',3,'[1 8]'); data(ch,'y','Output',1,'[13 1]');
f=Stateflow.EMFunction(ch); f.Name='stateflow_choose_mode_v24';
f.Position=[40 420 220 65]; f.Script=fileread(fullfile(here,'stateflow_choose_mode_v24.m'));
f=Stateflow.EMFunction(ch); f.Name='stateflow_allocate_v24';
f.Position=[320 420 220 65]; f.Script=fileread(fullfile(here,'stateflow_allocate_v24.m'));
names={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'};
states=cell(6,1);
for k=1:6
    s=Stateflow.State(ch); s.Name=names{k};
    s.Position=[80+mod(k-1,3)*250 80+floor((k-1)/3)*170 205 95];
    s.LabelString=sprintf('%s\nen,du:\ny=stateflow_allocate_v24(%d,u,E,p);',names{k},k-1);
    states{k}=s;
end
j=Stateflow.Junction(ch); j.Position.Center=[35 35]; j.Position.Radius=8;
t=Stateflow.Transition(ch); t.Destination=j; t.DestinationOClock=12;
t.SourceEndPoint=[35 5]; t.MidPoint=[35 15];
for k=1:6
    t=Stateflow.Transition(ch); t.Source=j; t.Destination=states{k};
    t.SourceOClock=3; t.DestinationOClock=12;
    t.LabelString=sprintf('[stateflow_choose_mode_v24(u,E,p)==%d]',k-1);
end
for k=1:6
    for n=1:6
        if k==n, continue; end
        t=Stateflow.Transition(ch); t.Source=states{k}; t.Destination=states{n};
        t.SourceOClock=3; t.DestinationOClock=9;
        t.LabelString=sprintf('[stateflow_choose_mode_v24(u,E,p)==%d]',n-1);
    end
end
add_block('simulink/Signal Routing/Selector',[mdl '/Next_TES_Energy'], ...
    'NumberOfDimensions','1','IndexOptionArray',{'Index vector (dialog)'}, ...
    'Indices','8','InputPortWidth','13','Position',[930 260 980 300]);
add_block('simulink/Sinks/To Workspace',[mdl '/Dispatch_Trace'], ...
    'VariableName','dispatch_trace_v24','SaveFormat','Timeseries','Position',[1020 70 1170 100]);
add_block('simulink/Sinks/To Workspace',[mdl '/HP_Trace'], ...
    'VariableName','hp_trace_v24','SaveFormat','Timeseries','Position',[750 145 900 175]);
add_block('simulink/Sinks/To Workspace',[mdl '/Energy_Start_Trace'], ...
    'VariableName','energy_start_trace_v24','SaveFormat','Timeseries','Position',[750 340 900 370]);
add_line(mdl,'Scenario_Input/1','Verified_HP_Component/1','autorouting','on');
add_line(mdl,'TES_Energy_Memory/1','Verified_HP_Component/2','autorouting','on');
add_line(mdl,'TES_and_Boiler_Parameters/1','Verified_HP_Component/3','autorouting','on');
add_line(mdl,'HP_Parameters/1','Verified_HP_Component/4','autorouting','on');
add_line(mdl,'Verified_HP_Component/1','Thermal_Dispatch/1','autorouting','on');
add_line(mdl,'TES_Energy_Memory/1','Thermal_Dispatch/2','autorouting','on');
add_line(mdl,'TES_and_Boiler_Parameters/1','Thermal_Dispatch/3','autorouting','on');
add_line(mdl,'Integration_Step/1','Verified_HP_Component/5','autorouting','on');
add_line(mdl,'Thermal_Dispatch/1','Runtime_Contract_Gate/1','autorouting','on');
add_line(mdl,'Verified_HP_Component/1','Runtime_Contract_Gate/2','autorouting','on');
add_line(mdl,'TES_Energy_Memory/1','Runtime_Contract_Gate/3','autorouting','on');
add_line(mdl,'TES_and_Boiler_Parameters/1','Runtime_Contract_Gate/4','autorouting','on');
add_line(mdl,'Integration_Step/1','Runtime_Contract_Gate/5','autorouting','on');
add_line(mdl,'Runtime_Contract_Gate/1','Next_TES_Energy/1','autorouting','on');
add_line(mdl,'Next_TES_Energy/1','TES_Energy_Memory/1','autorouting','on');
add_line(mdl,'Runtime_Contract_Gate/1','Dispatch_Trace/1','autorouting','on');
add_line(mdl,'Verified_HP_Component/1','HP_Trace/1','autorouting','on');
add_line(mdl,'TES_Energy_Memory/1','Energy_Start_Trace/1','autorouting','on');
set_param(mdl,'SimulationCommand','update');
save_system(mdl,modelPath);
fprintf('BUILT_AND_COMPILED %s\n',modelPath);
end

function data(ch,name,scope,port,sizeText)
d=Stateflow.Data(ch); d.Name=name; d.Scope=scope; d.Port=port;
d.DataType='double'; d.Props.Array.Size=sizeText;
end
