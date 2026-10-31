function path=build_charge_event_record_v60()
% Executable scoped correlated-record handoff model; not a six-mode plant.
here=fileparts(mfilename('fullpath'));mdl='DCHR_Charge_Event_Record_v60';path=fullfile(here,[mdl '.slx']);
assert(~isfile(path),'DCHR:v60:ModelExists','Preserve saved model.');assert(license('test','Stateflow'));
load_system('sflib');load_system('simulink');new_system(mdl);cl=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
set_param(mdl,'Solver','FixedStepDiscrete','SolverType','Fixed-step','FixedStep','1','StopTime','2', ...
    'SimulationMode','normal','ReturnWorkspaceOutputs','on');
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'event_packets_v60',zeros(3,33));
add_block('simulink/Sources/From Workspace',[mdl '/Correlated_Record'],'VariableName','event_packets_v60', ...
    'Interpolate','off','OutputAfterFinalValue','Holding final value','SampleTime','1','Position',[40 80 210 120]);
add_block('sflib/Chart',[mdl '/Event_Handoff'],'Position',[300 50 600 210]);rt=sfroot;
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Event_Handoff']);ch.ActionLanguage='MATLAB';ch.ChartUpdate='INHERITED';ch.ExecuteAtInitialization=false;
ch.Description='v60 scoped correlated upward charge record. Samples are protocol phases, not physical solver events. Host exact-rational proof; compiled interval/correlation gate. No scalar TES memory.';
for item={'packet','Input';'trace','Output'}'
    d=Stateflow.Data(ch);d.Name=item{1};d.Scope=item{2};d.Port=1;d.DataType='double';d.Props.Array.Size='[32 1]';
end
d=Stateflow.Data(ch);d.Name='previous';d.Scope='Local';d.DataType='double';d.Props.Array.Size='[32 1]';d.Props.InitialValue='zeros(32,1)';
f=Stateflow.EMFunction(ch);f.Name='stateflow_event_record_gate_v60';f.Position=[40 500 300 90];f.Script=fileread(fullfile(here,'stateflow_event_record_gate_v60.m'));
names={'FLOOR_CHARGE','EVENT_CONTACT','TANK_CHARGE'};states=cell(3,1);
for j=1:3
    a=Stateflow.State(ch);a.Name=names{j};a.Position=[60+300*(j-1) 90 260 180];
    a.LabelString=sprintf('%s\nen:\ntrace=stateflow_event_record_gate_v60(packet,previous,%d);\nprevious=trace;\ndu:\nassert(false,''Event phase must advance exactly once.'');',names{j},j-1);states{j}=a;
end
t=Stateflow.Transition(ch);t.Destination=states{1};t.DestinationOClock=12;t.SourceEndPoint=[100 20];t.MidPoint=[100 50];t.LabelString='[packet(1)==0]';
for j=1:2,t=Stateflow.Transition(ch);t.Source=states{j};t.Destination=states{j+1};t.SourceOClock=3;t.DestinationOClock=9;t.LabelString=sprintf('[packet(1)==%d]',j);end
add_block('simulink/Sinks/To Workspace',[mdl '/Record_Trace'],'VariableName','event_trace_v60','SaveFormat','Timeseries','Position',[710 90 890 130]);
add_line(mdl,'Correlated_Record/1','Event_Handoff/1');add_line(mdl,'Event_Handoff/1','Record_Trace/1');
set_param(mdl,'SimulationCommand','update');save_system(mdl,path);fprintf('BUILT_COMPILED_EVENT_RECORD_V60=%s\n',path);
end
