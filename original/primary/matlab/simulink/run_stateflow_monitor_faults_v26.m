function outputDir=run_stateflow_monitor_faults_v26()
% Actual v24 saved-model monitor acceptance and fault rejection evidence.
% v26 adds a completed two-interval harness; production model is preserved.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_monitor_v26_' stamp]);
assert(~isfolder(outputDir),'DCHR:v26:EvidenceExists','Refuse evidence overwrite.');
mkdir(outputDir);
fprintf('MATLAB_VERSION=%s\nSTATEFLOW_LICENSE=%d\n',version,license('test','Stateflow'));
assert(license('test','Stateflow'),'DCHR:v26:Unavailable','Stateflow license unavailable.');
specPath=fullfile(root,'audit','stateflow_monitor_fault_cases_v26.json');
spec=jsondecode(fileread(specPath));
mdl='DCHR_Dispatch_Stateflow_v24'; modelPath=fullfile(here,[mdl '.slx']);
sourcePath=fullfile(here,'stateflow_allocate_v24.m');
before=sha256(modelPath); sourceBefore=sha256(sourcePath);
assert(~bdIsLoaded(mdl),'DCHR:v26:LoadedModel','Use a fresh MATLAB batch session.');
load_system(modelPath);
modelCleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
previous=Simulink.fileGenControl('getConfig');
filegenCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',previous)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
rt=sfroot; chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
helper=chart.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v24');
assert(numel(helper)==1,'DCHR:v26:Helper','Expected exactly one allocation helper.');
original=helper.Script;
assert(strcmp(original,fileread(sourcePath)),'DCHR:v26:SourceMismatch','Saved model is stale.');
b=spec.baseline;
assert(b.model_dt_h>0 && b.p(1)==b.model_dt_h && b.stop_time_h==b.model_dt_h, ...
    'DCHR:v26:Clock','Independent baseline clock mismatch.');
s=Simulink.SimulationInput(mdl);
s=s.setVariable('dchr_dt_v24',b.model_dt_h,'Workspace',mdl);
s=s.setVariable('dchr_stop_v24',b.stop_time_h,'Workspace',mdl);
s=s.setVariable('dchr_input_v24',[(0:1)'*b.model_dt_h repmat(b.input_x(:)',2,1)],'Workspace',mdl);
s=s.setVariable('dchr_p_v24',b.p(:)','Workspace',mdl);
s=s.setVariable('dchr_h_v24',b.h(:)','Workspace',mdl);
s=s.setVariable('dchr_E0_v24',b.initial_energy_MWh,'Workspace',mdl);
baseline=sim(s);
save(fullfile(outputDir,'unmutated_baseline_simulation.mat'),'baseline');
baselineTrace=trace(baseline);
writetable(baselineTrace,fullfile(outputDir,'baseline_trace_v26.csv'));
assert(height(baselineTrace)==2 && isequal(baselineTrace.Time_h,[0;b.model_dt_h]), ...
    'DCHR:v26:TimeGrid','Expected two actual model samples.');
fprintf('UNMUTATED_BASELINE_EXECUTED intervals=%d\n',height(baselineTrace));
cases=spec.cases;
records=struct('id',{},'mutation',{},'expected_message',{},'simulation_attempted',{}, ...
    'rejected',{},'actual_identifier',{},'cause_identifiers',{},'message',{}, ...
    'expected_gate_observed',{},'accepted_invalid_trace',{},'failure_report',{}, ...
    'failure_report_sha256',{},'restored_source',{});
for k=1:numel(cases)
    c=cases(k);
    mutated=regexprep(original,'\nend\s*$',sprintf('\n%% Independent QA in-memory corruption\n%s\nend\n',c.mutation));
    assert(~strcmp(mutated,original),'DCHR:v26:Mutation','Mutation failed to change helper.');
    helper.Script=mutated;
    rejected=false; actual=''; ids={}; message=''; report=''; accepted=false;
    try
        invalidResult=sim(s); accepted=true;
        save(fullfile(outputDir,[c.id '_UNEXPECTED_ACCEPTANCE.mat']),'invalidResult');
    catch failure
        rejected=true; actual=failure.identifier; ids=identifiers(failure);
        message=failure.message; report=getReport(failure,'extended','hyperlinks','off');
    end
    helper.Script=original;
    restored=strcmp(helper.Script,original);
    observed=contains(report,'Runtime_Contract_Gate') && contains(report,c.expected_message);
    reportPath=fullfile(outputDir,[c.id '_rejection.txt']);
    fid=fopen(reportPath,'w'); assert(fid>0,'DCHR:v26:Write','Cannot write diagnostic.');
    fprintf(fid,'%s\n',report); fclose(fid);
    records(end+1)=struct('id',c.id,'mutation',c.mutation,'expected_message',c.expected_message, ...
        'simulation_attempted',true,'rejected',rejected,'actual_identifier',actual, ...
        'cause_identifiers',{ids},'message',message,'expected_gate_observed',observed, ...
        'accepted_invalid_trace',accepted,'failure_report',reportPath, ...
        'failure_report_sha256',sha256(reportPath),'restored_source',restored); %#ok<AGROW>
    fprintf('ACTUAL_MONITOR_FAULT %s rejected=%d expected_gate=%d restored=%d\n', ...
        c.id,rejected,observed,restored);
end
assert(strcmp(helper.Script,original),'DCHR:v26:Restore','Embedded source not restored.');
restoredResult=sim(s);
save(fullfile(outputDir,'restored_baseline_simulation.mat'),'restoredResult');
restoredTrace=trace(restoredResult);
writetable(restoredTrace,fullfile(outputDir,'restored_trace_v26.csv'));
same=isequaln(table2array(baselineTrace),table2array(restoredTrace));
fprintf('RESTORED_BASELINE_EXECUTED intervals=%d exact_match=%d\n',height(restoredTrace),same);
summary=struct('version','0.26','timestamp_utc',stamp,'matlab_version',version, ...
    'stateflow_license',license('test','Stateflow'),'simulation_mode','normal', ...
    'model_path',modelPath,'model_sha256_before',before,'model_sha256_after',sha256(modelPath), ...
    'source_sha256_before',sourceBefore,'source_sha256_after',sha256(sourcePath), ...
    'spec_file',specPath,'spec_sha256',sha256(specPath), ...
    'runner_sha256',sha256([mfilename('fullpath') '.m']), ...
    'cases',numel(cases),'rejected',sum([records.rejected]), ...
    'expected_gate_observed',sum([records.expected_gate_observed]), ...
    'accepted_invalid_traces',sum([records.accepted_invalid_trace]),'records',records, ...
    'unmutated_baseline_executed',true,'baseline_intervals',height(baselineTrace), ...
    'restored_baseline_executed',true,'restored_baseline_matches',same, ...
    'embedded_source_restored',strcmp(helper.Script,original),'saved_model_modified',false, ...
    'simulink_executed',true,'stateflow_executed',true,'standalone_codegen',false, ...
    'primary_paper_replication',false,'equipment_validation',false);
fid=fopen(fullfile(outputDir,'gate_fault_rejections_v26.json'),'w'); assert(fid>0);
fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true)); fclose(fid);
assert(summary.rejected==summary.cases && summary.expected_gate_observed==summary.cases && ...
    summary.accepted_invalid_traces==0 && summary.embedded_source_restored && same && ...
    strcmp(summary.model_sha256_before,summary.model_sha256_after) && ...
    strcmp(summary.source_sha256_before,summary.source_sha256_after), ...
    'DCHR:v26:FaultAcceptance','See completed actual-model monitor evidence.');
disp(rmfield(summary,'records')); fprintf('MONITOR_OUTPUT=%s\n',outputDir);
end

function ids=identifiers(failure)
ids={failure.identifier};
for k=1:numel(failure.cause), ids=[ids identifiers(failure.cause{k})]; end %#ok<AGROW>
end

function t=trace(result)
y=samples(result.dispatch_trace_v24,13); u=samples(result.hp_trace_v24,8);
e=reshape(result.energy_start_trace_v24.Data,[],1);
t=table(result.dispatch_trace_v24.Time,y(:,1),u(:,5),u(:,2),u(:,3),u(:,4),u(:,6), ...
    e,y(:,7),y(:,8),y(:,2),y(:,3),y(:,4),y(:,5),y(:,6),y(:,9),y(:,10),y(:,11),y(:,12),y(:,13), ...
    'VariableNames',{'Time_h','Mode','HP_Request_MW','HP_Heat_MW','HP_Electric_MW', ...
    'HP_Source_Used_MW','COP','Storage_E_Start_MWh','Storage_E_After_Loss_MWh','Storage_E_Next_MWh', ...
    'HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW', ...
    'Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh','Storage_Discharge_Loss_MWh', ...
    'Supplied_Heat_MW','System_Balance_Residual_MWh'});
end

function values=samples(ts,width)
raw=ts.Data; n=numel(ts.Time);
if ismatrix(raw) && isequal(size(raw),[n width]), values=raw;
elseif size(raw,1)==width && numel(raw)==n*width, values=reshape(raw,width,n)';
else, error('DCHR:v26:TraceDimensions','Unexpected timeseries dimensions.');
end
end

function value=sha256(path)
fid=fopen(path,'rb'); assert(fid>0); bytes=fread(fid,Inf,'*uint8'); fclose(fid);
digest=java.security.MessageDigest.getInstance('SHA-256'); digest.update(bytes);
value=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
