function path=build_electrical_ceiling_v83r2(input,cfg)
here=fileparts(mfilename('fullpath'));mdl='DCHR_Electrical_Dispatch_Stateflow_v83r2';path=fullfile(here,[mdl '.slx']);
assert(~isfile(path),'DCHR:v70:PreserveModel','Saved model already exists');assert(license('test','Stateflow'));
load_system('sflib');load_system('simulink');new_system(mdl);cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
set_param(mdl,'Solver','FixedStepDiscrete','SolverType','Fixed-step','FixedStep','1','StopTime',num2str(size(input,1)-1), ...
    'SimulationMode','normal','ReturnWorkspaceOutputs','on');
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',input);assignin(mw,'dispatch_cfg_v66',cfg);
add_block('simulink/Sources/From Workspace',[mdl '/Physical_Input'],'VariableName','dispatch_input_v66','SampleTime','1', ...
    'Interpolate','off','OutputAfterFinalValue','Holding final value','Position',[30 30 220 80]);
add_block('simulink/Sources/From Workspace',[mdl '/Policy_Provenance'],'VariableName','dispatch_cfg_v66','SampleTime','1', ...
    'Interpolate','off','OutputAfterFinalValue','Holding final value','Position',[30 140 220 190]);
add_block('sflib/Chart',[mdl '/Six_Mode_Interval_Dispatch'],'Position',[300 30 650 240]);rt=sfroot;
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);ch.ActionLanguage='MATLAB';
ch.ChartUpdate='INHERITED';ch.ExecuteAtInitialization=false;
ch.Description='v83 conservative compressor-ceiling; v80 pre-commit standing-loss/HP/energy/temporal-monitored SAME six-mode chart executes analytic earliest-event segments. Root hulls, symbolic thresholds, port offsets and physical clock survive each segment. No root midpoint. Macro solver ticks are protocol calls, not physical event times.';
names={'horizon_input','policy_input','trace','retained_memory','core'};scopes={'Input','Input','Output','Local','Local'};sizes={'[12 1]','[26 1]','[1380 1]','[1380 1]','[1380 1]'};
for j=1:5
    d=Stateflow.Data(ch);d.Name=names{j};d.Scope=scopes{j};d.DataType='double';d.Props.Array.Size=sizes{j};
    if j<3,d.Port=j;elseif j==3,d.Port=1;else,d.Props.InitialValue='zeros(1380,1)';end
end
f=Stateflow.EMFunction(ch);f.Name='earliest_dispatch_kernel_v75';f.Position=[60 550 380 90];f.Script=fileread(fullfile(here,'earliest_dispatch_kernel_v75.m'));
f=Stateflow.EMFunction(ch);f.Name='certify_event_root_v73';f.Position=[850 550 380 90];f.Script=fileread(fullfile(here,'certify_event_root_v73.m'));
f=Stateflow.EMFunction(ch);f.Name='inventory_flow_v73';f.Position=[850 680 380 90];f.Script=fileread(fullfile(here,'inventory_flow_v73.m'));
f=Stateflow.EMFunction(ch);f.Name='passive_contact_root_v73r2';f.Position=[1250 680 380 90];f.Script=fileread(fullfile(here,'passive_contact_root_v73r2.m'));
f=Stateflow.EMFunction(ch);f.Name='monitor_temporal_commit_v77';f.Position=[1250 550 380 90];f.Script=fileread(fullfile(here,'monitor_temporal_commit_v77.m'));
f=Stateflow.EMFunction(ch);f.Name='monitor_energy_commit_v78';f.Position=[1250 800 380 90];f.Script=fileread(fullfile(here,'monitor_energy_commit_v78.m'));
f=Stateflow.EMFunction(ch);f.Name='monitor_hp_partition_v79';f.Position=[1650 800 380 90];f.Script=fileread(fullfile(here,'monitor_hp_partition_v79.m'));
f=Stateflow.EMFunction(ch);f.Name='monitor_standing_loss_v80';f.Position=[2050 800 380 90];f.Script=fileread(fullfile(here,'monitor_standing_loss_v80.m'));
d=Stateflow.Data(ch);d.Name='electrical_certificate';d.Scope='Output';d.DataType='double';d.Props.Array.Size='[27 1]';d.Port=2;
d=Stateflow.Data(ch);d.Name='raw_policy_memory';d.Scope='Local';d.DataType='double';d.Props.Array.Size='[26 1]';d.Props.InitialValue='zeros(26,1)';
f=Stateflow.EMFunction(ch);f.Name='electrical_policy_v83r2';f.Position=[2450 800 380 90];f.Script=fileread(fullfile(here,'electrical_policy_v83r2.m'));
f=Stateflow.EMFunction(ch);f.Name='electrical_dispatch_v83r2';f.Position=[2450 550 380 90];
f.Script=sprintf('function [y,certificate]=electrical_dispatch_v83r2(u,raw,memory,rawMemory)\nif memory(2)~=0,assert(all(raw==rawMemory),''v83 immutable electrical policy'');end\np=electrical_policy_v83r2(raw);\ny=earliest_dispatch_kernel_v75(u,p,memory);\nmonitor_standing_loss_v80(u,p,memory,y);\ncertificate=[raw;p(11)];\nend');
f=Stateflow.EMFunction(ch);f.Name='earliest_mode_v73';f.Position=[480 550 300 90];
f.Script=sprintf('function mode=earliest_mode_v73(u,cfg,memory)\np=electrical_policy_v83r2(cfg);y=earliest_dispatch_kernel_v75(u,p,memory);mode=y(1);\nend');
sn={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'};states=cell(6,1);
for j=1:6
    s=Stateflow.State(ch);s.Name=sn{j};s.Position=[60+300*(j-1) 80 270 320];
    action=sprintf('[core,electrical_certificate]=electrical_dispatch_v83r2(horizon_input,policy_input,retained_memory,raw_policy_memory);\nassert(core(1)==%d);\nraw_policy_memory=policy_input;\ntrace=core;\nretained_memory=core;',j-1);
    s.LabelString=sprintf('%s\nen:\n%s\ndu:\n%s',sn{j},action,action);states{j}=s;
end
junction=Stateflow.Junction(ch);junction.Position.Center=[30 30];junction.Position.Radius=8;
t=Stateflow.Transition(ch);t.Destination=junction;t.DestinationOClock=12;t.SourceEndPoint=[30 0];t.MidPoint=[30 15];
for j=1:6
    t=Stateflow.Transition(ch);t.Source=junction;t.Destination=states{j};t.SourceOClock=3;t.DestinationOClock=12;
    t.LabelString=sprintf('[earliest_mode_v73(horizon_input,policy_input,retained_memory)==%d]',j-1);
    for k=1:6
        if k==j,continue;end
        t=Stateflow.Transition(ch);t.Source=states{k};t.Destination=states{j};t.SourceOClock=3;t.DestinationOClock=9;
        t.LabelString=sprintf('[earliest_mode_v73(horizon_input,policy_input,retained_memory)==%d]',j-1);
    end
end
add_block('simulink/Sinks/To Workspace',[mdl '/Numeric_Trace'],'VariableName','interval_trace_v66','SaveFormat','Timeseries','Position',[750 70 930 120]);
add_line(mdl,'Physical_Input/1','Six_Mode_Interval_Dispatch/1');add_line(mdl,'Policy_Provenance/1','Six_Mode_Interval_Dispatch/2');
add_line(mdl,'Six_Mode_Interval_Dispatch/1','Numeric_Trace/1');
add_block('simulink/Sinks/To Workspace',[mdl '/Electrical_Certificate'],'VariableName','electrical_certificate_v83','SaveFormat','Timeseries','Position',[750 170 930 220]);
add_line(mdl,'Six_Mode_Interval_Dispatch/2','Electrical_Certificate/1');
set_param(mdl,'SimulationCommand','update');save_system(mdl,path);fprintf('BUILT_ELECTRICAL_CEILING_STATEFLOW_V83=%s\n',path);
end
