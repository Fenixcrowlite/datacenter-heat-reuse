function modelPath=build_dispatch_stateflow_v38()
% Additive model: 64 bounded segment slots and physical-hour HP supervisor.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);mdl='DCHR_Dispatch_Stateflow_v38';
modelPath=fullfile(here,[mdl '.slx']);assert(~isfile(modelPath),'DCHR:v38:ModelExists','Preserve saved version.');
assert(license('test','Stateflow'),'Stateflow license unavailable');
load_system('sflib');load_system('simulink');new_system(mdl);
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
set_param(mdl,'Solver','FixedStepDiscrete','SolverType','Fixed-step','FixedStep','dchr_dt_v38', ...
    'StopTime','dchr_stop_v38','SimulationMode','normal','ReturnWorkspaceOutputs','on');
mw=get_param(mdl,'ModelWorkspace');
assignin(mw,'dchr_dt_v38',1);assignin(mw,'dchr_stop_v38',1);
assignin(mw,'dchr_input_v38',[0 6 35 75 0 45;1 0 35 75 5 45]);
assignin(mw,'dchr_p_v38',[1 10 3 4 .9 .8 .1 5 .2 20 2]);
assignin(mw,'dchr_h_v38',[8 .45 1.2 8 .08 0 4 0 0]);assignin(mw,'dchr_E0_v38',9);
add_block('simulink/Sources/From Workspace',[mdl '/Scenario_Input'],'VariableName','dchr_input_v38', ...
    'Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','dchr_dt_v38','Position',[20 30 150 60]);
add_block('simulink/Sources/Constant',[mdl '/TES_Parameters'],'Value','dchr_p_v38','Position',[20 110 150 140]);
add_block('simulink/Sources/Constant',[mdl '/HP_Parameters'],'Value','dchr_h_v38','Position',[20 170 150 200]);
add_block('simulink/Sources/Constant',[mdl '/Integration_Step'],'Value','dchr_dt_v38','Position',[20 230 150 260]);
add_block('simulink/Discrete/Unit Delay',[mdl '/TES_Energy_Memory'],'InitialCondition','dchr_E0_v38', ...
    'SampleTime','dchr_dt_v38','Position',[500 360 550 400]);
assignin(mw,'dchr_c_v38',[8 .25 .25 64]);assignin(mw,'dchr_m0_v38',[1;0;0;0]);
add_block('simulink/Sources/Constant',[mdl '/Control_Parameters'],'Value','dchr_c_v38','Position',[20 420 150 450]);
add_block('simulink/Discrete/Unit Delay',[mdl '/HP_Clock_Memory'],'InitialCondition','dchr_m0_v38', ...
    'SampleTime','dchr_dt_v38','Position',[500 470 550 510]);
add_block('simulink/Sinks/To Workspace',[mdl '/Clock_Start_Trace'],'VariableName','clock_start_trace_v38', ...
    'SaveFormat','Timeseries','Position',[1030 450 1190 480]);
add_block('simulink/Sinks/To Workspace',[mdl '/Clock_End_Trace'],'VariableName','clock_end_trace_v38', ...
    'SaveFormat','Timeseries','Position',[1030 520 1190 550]);
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Segment_HP_Plan'],'Position',[210 30 360 175]);
rt=sfroot;f=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Segment_HP_Plan']);
f.Script=sprintf(['function plan=make_plan(x,E,p,h,dt,m,c)\n%%#codegen\n' ...
    'coder.extrinsic(''dchr_segment_plan_v38'');\nplan=zeros(22,64);\n' ...
    'plan=dchr_segment_plan_v38(x,E,p,h,dt,m,c);\nend\n']);
sub=[mdl '/Execute_Segments'];
add_block('simulink/Ports & Subsystems/For Iterator Subsystem',sub,'Position',[410 30 620 175]);
% Only newly created default blocks/lines are replaced; no baseline is edited.
Simulink.SubSystem.deleteContents(sub);
add_block('simulink/Ports & Subsystems/In1',[sub '/Plan'],'Port','1','Position',[20 30 50 45]);
add_block('simulink/Ports & Subsystems/In1',[sub '/Parameters'],'Port','2','Position',[20 95 50 110]);
add_block('simulink/Ports & Subsystems/For Iterator Subsystem/For Iterator',[sub '/For Iterator'], ...
    'IterationSource','internal','IterationLimit','64','IndexMode','One-based', ...
    'ResetStates','held','Position',[20 160 70 190]);
add_block('simulink/User-Defined Functions/MATLAB Function',[sub '/Select_Segment'],'Position',[115 25 220 80]);
f=rt.find('-isa','Stateflow.EMChart','Path',[sub '/Select_Segment']);
f.Script=sprintf('function s=pick(plan,iteration)\n%%#codegen\ns=plan(:,iteration);\nend\n');
add_block('sflib/Chart',[sub '/Thermal_Dispatch'],'Position',[280 30 490 170]);
ch=rt.find('-isa','Stateflow.Chart','Path',[sub '/Thermal_Dispatch']);
ch.ActionLanguage='MATLAB';ch.ChartUpdate='INHERITED';ch.ExecuteAtInitialization=false;
ch.Description='Release 0.38: bounded physical-hour events, actual persistent HP ON/OFF supervisor and six guarded thermal modes. Normal-mode host HP planner.';
data(ch,'segmentInput','Input',1,'[22 1]');data(ch,'parameters','Input',2,'[1 11]');
data(ch,'iteration','Input',3,'1');data(ch,'hpClock','Input',4,'[4 1]');data(ch,'Trace','Output',1,'[1792 1]');
it=ch.find('-isa','Stateflow.Data','Name','iteration');it.DataType='int32';
d=Stateflow.Data(ch);d.Name='segmentOutput';d.Scope='Local';d.DataType='double';d.Props.Array.Size='[28 1]';
functions={'stateflow_choose_mode_v38','stateflow_allocate_v38','stateflow_collect_v38'};
for k=1:3
    f=Stateflow.EMFunction(ch);f.Name=functions{k};f.Position=[40+260*(k-1) 440 240 65];
    f.Script=fileread(fullfile(here,[functions{k} '.m']));
end
names={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'};
states=cell(6,1);
for k=1:6
    s=Stateflow.State(ch);s.Name=names{k};s.Position=[70+mod(k-1,3)*260 80+floor((k-1)/3)*170 230 130];
    s.LabelString=sprintf(['%s\nen,du:\nif iteration==1\nTrace=zeros(1792,1);\nend\n' ...
        'segmentOutput=stateflow_allocate_v38(%d,segmentInput,parameters,hpClock);\n' ...
        'Trace=stateflow_collect_v38(Trace,segmentOutput,iteration);'],names{k},k-1);
    states{k}=s;
end
j=Stateflow.Junction(ch);j.Position.Center=[35 35];j.Position.Radius=8;
t=Stateflow.Transition(ch);t.Destination=j;t.DestinationOClock=12;t.SourceEndPoint=[35 5];t.MidPoint=[35 15];
for k=1:6
    t=Stateflow.Transition(ch);t.Source=j;t.Destination=states{k};t.SourceOClock=3;t.DestinationOClock=12;
    t.LabelString=sprintf('[stateflow_choose_mode_v38(segmentInput,parameters)==%d]',k-1);
end
for k=1:6
    for n=1:6
        if k==n,continue;end
        t=Stateflow.Transition(ch);t.Source=states{k};t.Destination=states{n};t.SourceOClock=3;t.DestinationOClock=9;
        t.LabelString=sprintf('[stateflow_choose_mode_v38(segmentInput,parameters)==%d]',n-1);
    end
end
add_block('simulink/Ports & Subsystems/In1',[sub '/Control'],'Port','3','Position',[20 220 50 235]);
add_block('sflib/Chart',[sub '/HP_Supervisor'],'Position',[270 240 490 350]);
hc=rt.find('-isa','Stateflow.Chart','Path',[sub '/HP_Supervisor']);
hc.ActionLanguage='MATLAB';hc.ChartUpdate='INHERITED';hc.ExecuteAtInitialization=false;
hc.Description='Persistent HP latch and explicit physical-hour elapsed timer. Safety capacity/input infeasibility overrides ON dwell; OFF dwell remains binding.';
data(hc,'s','Input',1,'[22 1]');data(hc,'p','Input',2,'[1 11]');data(hc,'c','Input',3,'[1 4]');
data(hc,'clock','Output',1,'[4 1]');
d=Stateflow.Data(hc);d.Name='age';d.Scope='Local';d.DataType='double';d.Props.InitialValue='0';
f=Stateflow.EMFunction(hc);f.Name='stateflow_supervisor_guard_v38';f.Position=[40 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_supervisor_guard_v38.m'));
f=Stateflow.EMFunction(hc);f.Name='stateflow_time_tolerance_v36';f.Position=[340 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_time_tolerance_v36.m'));
f=Stateflow.EMFunction(hc);f.Name='stateflow_clock_add_v38';f.Position=[640 400 260 70];
f.Script=fileread(fullfile(here,'stateflow_clock_add_v38.m'));
for name={'low','bound'}
    d=Stateflow.Data(hc);d.Name=name{1};d.Scope='Local';d.DataType='double';d.Props.InitialValue='0';
end
hs=cell(2,1);
for k=1:2
    a=Stateflow.State(hc);a.Name='HP_OFF';if k==2,a.Name='HP_ON';end
    a.Position=[70+(k-1)*300 70 250 210];
    a.LabelString=sprintf(['%s\nen:\nage=s(16);low=s(19);bound=s(21);\n' ...
        'assert(s(15)==%d);\n[age,low,bound]=stateflow_clock_add_v38(age,low,bound,s(1));\nclock=[%d;age;low;bound];\n' ...
        'du:\nassert(s(15)==%d);\nassert(abs(age-s(16))<=stateflow_time_tolerance_v36([age;s(16)]));\n' ...
        '[age,low,bound]=stateflow_clock_add_v38(age,low,bound,s(1));\nclock=[%d;age;low;bound];'],a.Name,k-1,k-1,k-1,k-1);
    hs{k}=a;
end
jj=Stateflow.Junction(hc);jj.Position.Center=[35 35];jj.Position.Radius=8;
t=Stateflow.Transition(hc);t.Destination=jj;t.DestinationOClock=12;t.SourceEndPoint=[35 5];t.MidPoint=[35 15];
for k=1:2
    t=Stateflow.Transition(hc);t.Source=jj;t.Destination=hs{k};t.SourceOClock=3;t.DestinationOClock=12;
    t.LabelString=sprintf('[s(15)==%d]',k-1);
end
for k=1:2
    n=3-k;t=Stateflow.Transition(hc);t.Source=hs{k};t.Destination=hs{n};t.SourceOClock=3;t.DestinationOClock=9;
    t.LabelString=sprintf('[s(15)==%d && stateflow_supervisor_guard_v38(%d,s,p,c,age,low)]',n-1,n-1);
end
add_block('simulink/Ports & Subsystems/Out1',[sub '/Clock'],'Port','2','Position',[550 260 580 275]);
add_line(sub,'Select_Segment/1','HP_Supervisor/1');add_line(sub,'Parameters/1','HP_Supervisor/2');
add_line(sub,'Control/1','HP_Supervisor/3');add_line(sub,'HP_Supervisor/1','Thermal_Dispatch/4');
add_line(sub,'HP_Supervisor/1','Clock/1');
add_block('simulink/Ports & Subsystems/Out1',[sub '/Trace'],'Position',[550 40 580 55]);
add_line(sub,'Plan/1','Select_Segment/1');add_line(sub,'For Iterator/1','Select_Segment/2');
add_line(sub,'Select_Segment/1','Thermal_Dispatch/1');add_line(sub,'Parameters/1','Thermal_Dispatch/2');
add_line(sub,'For Iterator/1','Thermal_Dispatch/3');add_line(sub,'Thermal_Dispatch/1','Trace/1');
add_block('simulink/User-Defined Functions/MATLAB Function',[mdl '/Runtime_Contract_Gate'],'Position',[680 30 870 210]);
f=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);f.Script=fileread(fullfile(here,'stateflow_contract_gate_v38.m'));
add_block('simulink/Signal Routing/Selector',[mdl '/Next_TES_Energy'],'NumberOfDimensions','1', ...
    'IndexOptionArray',{'Index vector (dialog)'},'Indices','8','InputPortWidth','25','Position',[920 300 970 345]);
traceNames={'segment_trace_v38','dispatch_trace_v38','plan_trace_v38','energy_start_trace_v38'};
blockNames={'Segment_Trace','Dispatch_Trace','Plan_Trace','Energy_Start_Trace'};
for k=1:4
    add_block('simulink/Sinks/To Workspace',[mdl '/' blockNames{k}],'VariableName',traceNames{k}, ...
        'SaveFormat','Timeseries','Position',[1030 30+60*(k-1) 1190 60+60*(k-1)]);
end
connections={'Scenario_Input/1','Segment_HP_Plan/1';'TES_Energy_Memory/1','Segment_HP_Plan/2'; ...
    'TES_Parameters/1','Segment_HP_Plan/3';'HP_Parameters/1','Segment_HP_Plan/4'; ...
    'Integration_Step/1','Segment_HP_Plan/5';'Segment_HP_Plan/1','Execute_Segments/1'; ...
    'TES_Parameters/1','Execute_Segments/2';'Execute_Segments/1','Runtime_Contract_Gate/1'; ...
    'Segment_HP_Plan/1','Runtime_Contract_Gate/2';'Scenario_Input/1','Runtime_Contract_Gate/3'; ...
    'TES_Parameters/1','Runtime_Contract_Gate/4';'HP_Parameters/1','Runtime_Contract_Gate/5'; ...
    'Integration_Step/1','Runtime_Contract_Gate/6';'Runtime_Contract_Gate/1','Segment_Trace/1'; ...
    'Runtime_Contract_Gate/2','Dispatch_Trace/1';'Runtime_Contract_Gate/2','Next_TES_Energy/1'; ...
    'Next_TES_Energy/1','TES_Energy_Memory/1';'Segment_HP_Plan/1','Plan_Trace/1'; ...
    'TES_Energy_Memory/1','Energy_Start_Trace/1'; ...
    'HP_Clock_Memory/1','Segment_HP_Plan/6';'Control_Parameters/1','Segment_HP_Plan/7'; ...
    'Control_Parameters/1','Execute_Segments/3';'Execute_Segments/2','Runtime_Contract_Gate/7'; ...
    'HP_Clock_Memory/1','Runtime_Contract_Gate/8';'Control_Parameters/1','Runtime_Contract_Gate/9'; ...
    'Runtime_Contract_Gate/3','HP_Clock_Memory/1';'HP_Clock_Memory/1','Clock_Start_Trace/1'; ...
    'Runtime_Contract_Gate/3','Clock_End_Trace/1'};
for k=1:size(connections,1),add_line(mdl,connections{k,1},connections{k,2},'autorouting','on');end
set_param(mdl,'SimulationCommand','update');save_system(mdl,modelPath);
fprintf('BUILT_AND_COMPILED=%s\n',modelPath);
end

function data(ch,name,scope,port,sizeText)
d=Stateflow.Data(ch);d.Name=name;d.Scope=scope;d.Port=port;d.DataType='double';d.Props.Array.Size=sizeText;
end
