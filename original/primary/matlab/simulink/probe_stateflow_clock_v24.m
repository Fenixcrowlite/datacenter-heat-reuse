function outputDir=probe_stateflow_clock_v24()
% Reproduce the unguarded v22 clock defect without editing that model.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_clock_defect_v24_' stamp]); mkdir(outputDir);
mdl='DCHR_Dispatch_Stateflow_v22'; load_system(fullfile(here,[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
old=Simulink.fileGenControl('getConfig');
restore=onCleanup(@()Simulink.fileGenControl('setConfig','config',old)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
s=Simulink.SimulationInput(mdl);
s=s.setVariable('dchr_dt_v22',1,'Workspace',mdl);
s=s.setVariable('dchr_stop_v22',1,'Workspace',mdl);
s=s.setVariable('dchr_input_v22',[0 0 35 70 1;1 0 35 70 1],'Workspace',mdl);
s=s.setVariable('dchr_p_v22',[.5 10 3 4 .9 .8 0 0],'Workspace',mdl);
s=s.setVariable('dchr_h_v22',[8 .45 1.2 8 .08 0 4 0 0],'Workspace',mdl);
s=s.setVariable('dchr_E0_v22',5,'Workspace',mdl);
result=sim(s); save(fullfile(outputDir,'clock_mismatch_simulation.mat'),'result');
y=reshape(result.dispatch_trace_v22.Data,13,[])';
e=reshape(result.energy_start_trace_v22.Data,[],1);
trace=table(result.dispatch_trace_v22.Time,e,y(:,4),y(:,8),y(:,11),y(:,13), ...
    'VariableNames',{'Time_h','Energy_Start_MWh','Discharge_MW','Energy_Next_MWh','Discharge_Loss_MWh','Reported_Residual_MWh'});
% No HP/boiler: first law evaluated over the ACTUAL 1 h tick.
trace.Clock_Correct_Residual_MWh=e-y(:,4)*1-y(:,8)-y(:,11)/.5*1;
writetable(trace,fullfile(outputDir,'clock_mismatch_trace_v24.csv'));
summary=struct('model_sample_h',1,'physical_parameter_h',.5,'simulation_executed',true, ...
    'defect_reproduced',all(abs(trace.Clock_Correct_Residual_MWh)>.1), ...
    'max_reported_residual_MWh',max(abs(y(:,13))), ...
    'max_clock_correct_residual_MWh',max(abs(trace.Clock_Correct_Residual_MWh)), ...
    'model_modified',false,'equipment_validation',false);
fid=fopen(fullfile(outputDir,'clock_defect_v24.json'),'w'); fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true)); fclose(fid);
assert(summary.defect_reproduced,'DCHR:v24:Probe','Expected actual-model clock inconsistency.');
disp(summary); fprintf('CLOCK_DEFECT_OUTPUT=%s\n',outputDir);
end
