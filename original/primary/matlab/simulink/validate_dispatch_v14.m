function validate_dispatch_v14()
here=fileparts(mfilename('fullpath')); mdl='DCHR_Dispatch_Stateflow_v14';
load_system(fullfile(here,[mdl '.slx']));
% Add a genuine Stateflow chart with explicit operational modes.
chartPath=[mdl '/Operating_Modes'];
if isempty(find_system(mdl,'SearchDepth',1,'Name','Operating_Modes'))
 add_block('sflib/Chart',chartPath,'Position',[460 80 650 210]);
 rt=sfroot; ch=rt.find('-isa','Stateflow.Chart','Path',chartPath);
 s1=Stateflow.State(ch);s1.Name='RECOVERY';s1.Position=[35 40 115 55];s1.LabelString='RECOVERY';
 s2=Stateflow.State(ch);s2.Name='BACKUP';s2.Position=[210 40 115 55];s2.LabelString='BACKUP';
 t0=Stateflow.Transition(ch);t0.Destination=s1;t0.DestinationOClock=9;t0.SourceEndPoint=[20 65];t0.MidPoint=[25 65];
 t1=Stateflow.Transition(ch);t1.Source=s1;t1.Destination=s2;t1.LabelString='[true]';t1.SourceOClock=3;t1.DestinationOClock=9;
 t2=Stateflow.Transition(ch);t2.Source=s2;t2.Destination=s1;t2.LabelString='[false]';t2.SourceOClock=3;t2.DestinationOClock=9;
end
save_system(mdl);
try
 set_param(mdl,'SimulationCommand','update');
 result=sim(mdl,'StopTime','2');
 fprintf('PASS update and sim: %s\n',mdl);
catch ME
 fprintf(2,'FAIL: %s\n',getReport(ME,'extended'));rethrow(ME);
end
close_system(mdl,0);
end
