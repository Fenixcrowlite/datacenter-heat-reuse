function path=build_interval_dispatch_v66(input,cfg)
here=fileparts(mfilename('fullpath'));mdl='DCHR_Interval_Dispatch_Stateflow_v66';path=fullfile(here,[mdl '.slx']);
assert(~isfile(path),'DCHR:v66:PreserveModel','Saved model already exists');assert(license('test','Stateflow'));
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
ch.Description='v66 conservative sampled service allocation; retained v64 restart provenance; six executed modes. Protocol ticks differ from physical hours. Enclosures are retained, never midpoint reset.';
names={'horizon_input','policy_input','trace','retained_memory'};scopes={'Input','Input','Output','Local'};sizes={'[12 1]','[60 1]','[205 1]','[205 1]'};
for j=1:4
    d=Stateflow.Data(ch);d.Name=names{j};d.Scope=scopes{j};d.DataType='double';d.Props.Array.Size=sizes{j};
    if j<3,d.Port=j;elseif j==3,d.Port=1;else,d.Props.InitialValue='zeros(205,1)';end
end
f=Stateflow.EMFunction(ch);f.Name='interval_dispatch_kernel_v66';f.Position=[60 550 380 90];f.Script=fileread(fullfile(here,'interval_dispatch_kernel_v66.m'));
f=Stateflow.EMFunction(ch);f.Name='interval_mode_v66';f.Position=[480 550 300 90];
f.Script=sprintf('function mode=interval_mode_v66(u,cfg,memory)\ny=interval_dispatch_kernel_v66(u,cfg,memory);mode=y(115);\nend');
sn={'IDLE','HEAT_RECOVERY','STORAGE_CHARGE','STORAGE_DISCHARGE','BACKUP','UNMET_DEMAND'};states=cell(6,1);
for j=1:6
    s=Stateflow.State(ch);s.Name=sn{j};s.Position=[60+300*(j-1) 80 270 320];
    action=sprintf('trace=interval_dispatch_kernel_v66(horizon_input,policy_input,retained_memory);\nassert(trace(115)==%d);\nretained_memory=trace;',j-1);
    s.LabelString=sprintf('%s\nen:\n%s\ndu:\n%s',sn{j},action,action);states{j}=s;
end
junction=Stateflow.Junction(ch);junction.Position.Center=[30 30];junction.Position.Radius=8;
t=Stateflow.Transition(ch);t.Destination=junction;t.DestinationOClock=12;t.SourceEndPoint=[30 0];t.MidPoint=[30 15];
for j=1:6
    t=Stateflow.Transition(ch);t.Source=junction;t.Destination=states{j};t.SourceOClock=3;t.DestinationOClock=12;
    t.LabelString=sprintf('[interval_mode_v66(horizon_input,policy_input,retained_memory)==%d]',j-1);
    for k=1:6
        if k==j,continue;end
        t=Stateflow.Transition(ch);t.Source=states{k};t.Destination=states{j};t.SourceOClock=3;t.DestinationOClock=9;
        t.LabelString=sprintf('[interval_mode_v66(horizon_input,policy_input,retained_memory)==%d]',j-1);
    end
end
add_block('simulink/Sinks/To Workspace',[mdl '/Numeric_Trace'],'VariableName','interval_trace_v66','SaveFormat','Timeseries','Position',[750 70 930 120]);
add_line(mdl,'Physical_Input/1','Six_Mode_Interval_Dispatch/1');add_line(mdl,'Policy_Provenance/1','Six_Mode_Interval_Dispatch/2');
add_line(mdl,'Six_Mode_Interval_Dispatch/1','Numeric_Trace/1');
set_param(mdl,'SimulationCommand','update');save_system(mdl,path);fprintf('BUILT_INTERVAL_DISPATCH_V66=%s\n',path);
end
