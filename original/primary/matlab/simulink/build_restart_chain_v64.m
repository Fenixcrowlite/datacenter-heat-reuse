function path=build_restart_chain_v64(cfg,steps)
% Executable branch-memory prerequisite, not the six-mode plant replacement.
here=fileparts(mfilename('fullpath'));mdl='DCHR_Restart_Chain_Stateflow_v64';path=fullfile(here,[mdl '.slx']);
assert(~isfile(path),'DCHR:v63:ModelExists','Preserve saved model');assert(license('test','Stateflow'));
load_system('sflib');load_system('simulink');new_system(mdl);cl=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
set_param(mdl,'Solver','FixedStepDiscrete','SolverType','Fixed-step','FixedStep','1','StopTime','9', ...
    'SimulationMode','normal','ReturnWorkspaceOutputs','on');
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'restart_cfg_v64',[(0:9)' repmat(cfg',10,1)]);assignin(mw,'restart_steps_v64',steps);
add_block('simulink/Sources/From Workspace',[mdl '/Physical_Horizons'],'VariableName','restart_steps_v64', ...
    'Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','1','Position',[30 50 210 90]);
add_block('simulink/Sources/From Workspace',[mdl '/Exact_Operand_Provenance'],'VariableName','restart_cfg_v64', ...
    'Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','1','Position',[30 160 210 200]);
add_block('sflib/Chart',[mdl '/Correlated_Capacity_Chain'],'Position',[300 40 620 250]);rt=sfroot;
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Correlated_Capacity_Chain']);ch.ActionLanguage='MATLAB';ch.ChartUpdate='INHERITED';ch.ExecuteAtInitialization=false;
ch.Description='v64 retained interval restart chain; compiled global flow and tank-linked source/water ports. Seven protocol phases, not solver-clock physical event firing. Exact operand expression retained, enclosures only, constant request upward branch.';
names={'horizon_input','provenance_input','trace','retained_memory'};scopes={'Input','Input','Output','Local'};sizes={'[3 1]','[35 1]','[114 1]','[114 1]'};
for j=1:4
    d=Stateflow.Data(ch);d.Name=names{j};d.Scope=scopes{j};d.DataType='double';d.Props.Array.Size=sizes{j};
    if j==1,d.Port=1;elseif j==2,d.Port=2;elseif j==3,d.Port=1;else,d.Props.InitialValue='zeros(114,1)';end
end
f=Stateflow.EMFunction(ch);f.Name='restart_chain_kernel_v64';f.Position=[60 460 320 90];f.Script=fileread(fullfile(here,'restart_chain_kernel_v64.m'));
sn={'FLOOR_CHARGE','CORRELATED_CONTACT','TANK_CHARGE','CAPACITY_CONTACT','PASSIVE_COOLING','RESTART_CHARGE','RECHARGE_CONTINUATION'};states=cell(7,1);
for j=1:7
    a=Stateflow.State(ch);a.Name=sn{j};a.Position=[60+320*(j-1) 80 280 230];
    action=sprintf('trace=restart_chain_kernel_v64(horizon_input,provenance_input,retained_memory,%d);\nretained_memory=trace;',j-1);
    a.LabelString=sprintf('%s\nen:\n%s\ndu:\n%s',sn{j},action,action);states{j}=a;
end
t=Stateflow.Transition(ch);t.Destination=states{1};t.DestinationOClock=12;t.SourceEndPoint=[100 20];t.MidPoint=[100 50];
for j=1:6
    t=Stateflow.Transition(ch);t.Source=states{j};t.Destination=states{j+1};t.SourceOClock=3;t.DestinationOClock=9;
    t.LabelString=sprintf('[horizon_input(1)==%d]',j);
end
add_block('simulink/Sinks/To Workspace',[mdl '/Compiled_Memory_Trace'],'VariableName','restart_trace_v64','SaveFormat','Timeseries','Position',[720 90 920 130]);
add_line(mdl,'Physical_Horizons/1','Correlated_Capacity_Chain/1');add_line(mdl,'Exact_Operand_Provenance/1','Correlated_Capacity_Chain/2');
add_line(mdl,'Correlated_Capacity_Chain/1','Compiled_Memory_Trace/1');
set_param(mdl,'SimulationCommand','update');save_system(mdl,path);fprintf('BUILT_CAPACITY_CHAIN_V63=%s\n',path);
end
