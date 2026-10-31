function outputDir=run_stateflow_temporal_acceptance_v27()
% Capture actual failure times and accepted prefixes from the saved v24 model.
% Additive acceptance harness; no model/controller/physical-policy changes.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_temporal_v27_' stamp]);
assert(~isfolder(outputDir),'DCHR:v27:EvidenceExists','Refuse evidence overwrite.');
mkdir(outputDir);
fprintf('MATLAB_VERSION=%s\nSTATEFLOW_LICENSE=%d\n',version,license('test','Stateflow'));
assert(license('test','Stateflow'),'DCHR:v27:Unavailable','Stateflow unavailable.');
specPath=fullfile(root,'audit','stateflow_temporal_cases_v27.json');
spec=jsondecode(fileread(specPath));
mdl='DCHR_Dispatch_Stateflow_v24'; modelPath=fullfile(here,[mdl '.slx']);
modelBefore=sha256(modelPath);
assert(~bdIsLoaded(mdl),'DCHR:v27:LoadedModel','Use a fresh MATLAB batch session.');
load_system(modelPath); closeModel=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
old=Simulink.fileGenControl('getConfig');
restore=onCleanup(@()Simulink.fileGenControl('setConfig','config',old)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
checks=struct('name',{},'passed',{},'detail',{}); records=cell(numel(spec.cases),1);
for k=1:numel(spec.cases)
    if iscell(spec.cases), c=spec.cases{k}; else, c=spec.cases(k); end
    b=spec.baseline; dt=c.dt_h; b.p(1)=dt;
    times=(0:round(c.stop_time_h/dt))'*dt;
    assert(near(times(end),c.stop_time_h),'DCHR:v27:StopGrid','Stop must be on sample grid.');
    cleanRows=[0 b.x(:)';c.invalid_input_time_h b.x(:)'];
    badRows=cleanRows; badRows(2,c.target_index+1)=c.invalid_value;
    inputPath=fullfile(outputDir,[c.id '_configured_input.csv']);
    writetable(array2table(badRows,'VariableNames', ...
        {'Time_h','Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'}),inputPath);
    s=Simulink.SimulationInput(mdl);
    s=s.setModelParameter('CaptureErrors','on');
    s=s.setVariable('dchr_dt_v24',dt,'Workspace',mdl);
    s=s.setVariable('dchr_stop_v24',c.stop_time_h,'Workspace',mdl);
    s=s.setVariable('dchr_p_v24',b.p(:)','Workspace',mdl);
    s=s.setVariable('dchr_h_v24',b.h(:)','Workspace',mdl);
    s=s.setVariable('dchr_E0_v24',b.E,'Workspace',mdl);
    s=s.setVariable('dchr_input_v24',cleanRows,'Workspace',mdl);
    clean=sim(s); save(fullfile(outputDir,[c.id '_clean_simulation.mat']),'clean');
    [cleanTrace,cleanRaw]=trace(clean,b.x);
    cleanPath=fullfile(outputDir,[c.id '_clean_trace.csv']); writetable(cleanTrace,cleanPath);
    cleanMetadata=metadata(clean);
    record([c.id '_clean_completed'],strcmp(cleanMetadata.stop_event,'ReachedStopTime') && ...
        isempty(cleanMetadata.error_message) && isequal(cleanTrace.Time_h,times), ...
        'Clean actual model completes the requested grid with CaptureErrors enabled.');
    cfg=configuration(b,dt); input=array2table(repmat(b.x(:)',numel(times),1), ...
        'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'});
    reference=dchr.simulate_dispatch_v16(cfg,input);
    referencePath=fullfile(outputDir,[c.id '_reference_trace.csv']); writetable(reference,referencePath);
    numericNames=reference.Properties.VariableNames(6:end);
    match=true;
    for j=1:numel(numericNames)
        name=numericNames{j}; match=match && near(cleanTrace.(name),reference.(name));
    end
    record([c.id '_v16_reference'],match,'All numerical ports compared with verified v16 dispatch.');
    s=s.setVariable('dchr_input_v24',badRows,'Workspace',mdl);
    actual=sim(s); save(fullfile(outputDir,[c.id '_partial_simulation.mat']),'actual','s');
    m=metadata(actual); [partial,raw]=trace(actual,b.x);
    partialPath=fullfile(outputDir,[c.id '_partial_trace.csv']); writetable(partial,partialPath);
    diagnosticPath=fullfile(outputDir,[c.id '_diagnostic.json']); writejson(diagnosticPath,m);
    rawPath=fullfile(outputDir,[c.id '_raw_trace_times.json']); writejson(rawPath,raw);
    prefix=isequal(partial.Time_h,c.expected_valid_times_h(:));
    if prefix
        [found,idx]=ismember(partial.Time_h,cleanTrace.Time_h);
        prefix=all(found) && near(table2array(partial),table2array(cleanTrace(idx,:)));
    end
    record([c.id '_valid_prefix'],prefix,'Accepted dispatch prefix contains exactly the independently specified valid times and ports.');
    thrown=struct('simulation_attempted',false,'rejected',false,'cause_identifiers',{{}}, ...
        'message','','report_file','','report_sha256','');
    host=struct('component_call_attempted',false,'rejected',false,'cause_identifiers',{{}}, ...
        'message','','report_file','','report_sha256','');
    if strcmp(c.expected_outcome,'runtime_rejection')
        % Captured MSLDiagnostic can omit nested MException causes. Preserve a
        % companion thrown-mode diagnostic under the identical input schedule.
        thrown.simulation_attempted=true;
        try
            unexpected=sim(s.setModelParameter('CaptureErrors','off'));
            save(fullfile(outputDir,[c.id '_UNEXPECTED_THROW_MODE_ACCEPTANCE.mat']),'unexpected');
        catch failure
            thrown.rejected=true; thrown.cause_identifiers=identifiers(failure);
            thrown.message=failure.message;
            thrown.report_file=fullfile(outputDir,[c.id '_exception_report.txt']);
            fid=fopen(thrown.report_file,'w'); assert(fid>0);
            fprintf(fid,'%s\n',getReport(failure,'extended','hyperlinks','off')); fclose(fid);
            thrown.report_sha256=sha256(thrown.report_file);
        end
        % Simulink flattens nested causes in both error modes. Check original
        % component causes separately; this is NOT model timing evidence.
        host.component_call_attempted=true;
        invalidX=b.x; invalidX(c.target_index)=c.invalid_value;
        failIndex=find(times==c.expected_failure_time_h,1);
        try
            dchr_stateflow_hp_v24(invalidX(:)',cleanTrace.Storage_E_Start_MWh(failIndex), ...
                b.p(:)',b.h(:)',dt);
        catch failure
            host.rejected=true; host.cause_identifiers=identifiers(failure); host.message=failure.message;
            host.report_file=fullfile(outputDir,[c.id '_host_adapter_report.txt']);
            fid=fopen(host.report_file,'w'); assert(fid>0);
            fprintf(fid,'%s\n',getReport(failure,'extended','hyperlinks','off')); fclose(fid);
            host.report_sha256=sha256(host.report_file);
        end
        timed=strcmp(m.stop_event,'DiagnosticError') && strcmp(m.error_phase,'Execution') && ...
            near(m.error_time_h,c.expected_failure_time_h) && near(m.stop_event_time_h,c.expected_failure_time_h);
        causal=any(strcmp(m.cause_identifiers,c.expected_identifier)) && ~isempty(m.error_message) && ...
            thrown.rejected && any(strcmp(thrown.cause_identifiers,c.expected_identifier)) && ...
            contains(m.error_message,c.runtime_message_fragment) && ...
            contains(thrown.message,c.runtime_message_fragment);
        record([c.id '_rejection_time'],timed,'Runtime metadata proves the error occurred at the first sampled invalid input.');
        record([c.id '_rejection_cause'],causal, ...
            'Both actual-model error modes reject with the expected wrapper and domain-specific message.');
        record([c.id '_host_original_cause'],host.rejected && ...
            any(strcmp(host.cause_identifiers,c.expected_identifier)) && ...
            any(strcmp(host.cause_identifiers,c.expected_inner_identifier)), ...
            'Separate host adapter call verifies original nested causes; this is component evidence only.');
        record([c.id '_no_invalid_dispatch'],all(partial.Time_h<c.expected_failure_time_h), ...
            'No failed-tick or later accepted dispatch output.');
    else
        timed=strcmp(m.stop_event,'ReachedStopTime') && near(m.stop_event_time_h,c.stop_time_h);
        causal=isempty(m.error_message) && isempty(m.error_phase) && isempty(m.cause_identifiers);
        record([c.id '_future_input_not_executed'],timed && causal, ...
            'Finite invalid future input does not fail a simulation stopped before its sampled time.');
    end
    records{k}=struct('id',c.id,'simulation_attempted',true,'capture_errors','on', ...
        'expected_outcome',c.expected_outcome,'dt_h',dt,'invalid_input_time_h',c.invalid_input_time_h, ...
        'stop_time_h',c.stop_time_h,'diagnostic',m,'uncaptured_exception',thrown, ...
        'host_adapter_validation',host, ...
        'configured_input_file',inputPath,'configured_input_sha256',sha256(inputPath), ...
        'partial_intervals',height(partial), ...
        'clean_intervals',height(cleanTrace),'raw_trace_times',raw,'clean_raw_trace_times',cleanRaw, ...
        'valid_prefix_matches',prefix,'timing_matches',timed,'cause_matches',causal, ...
        'clean_trace_file',cleanPath,'clean_trace_sha256',sha256(cleanPath), ...
        'partial_trace_file',partialPath,'partial_trace_sha256',sha256(partialPath), ...
        'reference_trace_file',referencePath,'reference_trace_sha256',sha256(referencePath), ...
        'diagnostic_file',diagnosticPath,'diagnostic_sha256',sha256(diagnosticPath), ...
        'raw_trace_times_file',rawPath,'raw_trace_times_sha256',sha256(rawPath));
    fprintf('ACTUAL_TEMPORAL %s stop=%s phase=%s time=%s prefix=%d timing=%d cause=%d\n', ...
        c.id,m.stop_event,m.error_phase,mat2str(m.error_time_h),prefix,timed,causal);
end
% Verify clean execution and initialized TES after all rejected simulations.
final=sim(s.setVariable('dchr_input_v24',cleanRows,'Workspace',mdl));
save(fullfile(outputDir,'final_clean_simulation.mat'),'final');
[finalTrace,~]=trace(final,b.x); finalPath=fullfile(outputDir,'final_clean_trace.csv');
writetable(finalTrace,finalPath); finalMetadata=metadata(final);
record('post_rejection_clean_restart',isempty(finalMetadata.error_message) && ...
    isequaln(table2array(finalTrace),table2array(cleanTrace)), ...
    'Fresh simulation restarts at configured initial TES state after fault cases.');
record('saved_model_preserved',strcmp(modelBefore,sha256(modelPath)), 'Saved versioned model is unchanged.');
writetable(struct2table(checks),fullfile(outputDir,'temporal_assertions_v27.csv'));
summary=struct('version','0.27','timestamp_utc',stamp,'matlab_version',version, ...
    'stateflow_license',license('test','Stateflow'),'simulation_mode','normal', ...
    'model_path',modelPath,'model_version','0.24','model_sha256_before',modelBefore, ...
    'model_sha256_after',sha256(modelPath),'saved_model_modified',false, ...
    'spec_file',specPath,'spec_sha256',sha256(specPath), ...
    'runner_sha256',sha256([mfilename('fullpath') '.m']), ...
    'cases',numel(records),'checks',numel(checks),'passed',sum([checks.passed]), ...
    'failed',sum(~[checks.passed]),'records',{records},'final_clean_trace_file',finalPath, ...
    'final_clean_trace_sha256',sha256(finalPath),'simulink_executed',true, ...
    'stateflow_executed',true,'standalone_codegen',false,'primary_paper_replication',false, ...
    'equipment_validation',false,'output_directory',outputDir);
writejson(fullfile(outputDir,'temporal_summary_v27.json'),summary);
disp(rmfield(summary,'records')); fprintf('TEMPORAL_OUTPUT=%s\n',outputDir);
assert(all([checks.passed]),'DCHR:v27:Acceptance','See timestamped temporal assertion evidence.');

    function record(name,passed,detail)
        checks(end+1)=struct('name',name,'passed',logical(passed),'detail',detail);
        if ~passed, fprintf(2,'FAIL %s\n',name); end
    end
end

function m=metadata(result)
e=result.SimulationMetadata.ExecutionInfo;
m=struct('stop_event',e.StopEvent,'stop_event_time_h',e.StopEventTime, ...
    'stop_event_description',e.StopEventDescription,'error_message',result.ErrorMessage, ...
    'error_phase','','error_time_h',[],'cause_identifiers',{{}},'diagnostic_tree',[]);
if ~isempty(e.ErrorDiagnostic)
    d=e.ErrorDiagnostic;
    m.error_phase=d.SimulationPhase; m.error_time_h=d.SimulationTime;
    m.cause_identifiers=identifiers(d.Diagnostic); m.diagnostic_tree=diagnostic(d.Diagnostic);
end
end

function ids=identifiers(d)
ids={d.identifier};
for j=1:numel(d.cause), ids=[ids identifiers(d.cause{j})]; end %#ok<AGROW>
end

function out=diagnostic(d)
children=cell(size(d.cause));
for j=1:numel(d.cause), children{j}=diagnostic(d.cause{j}); end
out=struct('identifier',d.identifier,'message',d.message,'cause',{children});
end

function [t,raw]=trace(result,x)
names={'Time_h','Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW', ...
    'HP_Request_MW','HP_Heat_MW','HP_Direct_MW','HP_Electric_MW','HP_Source_Used_MW','COP', ...
    'HP_Available','Source_Unused_MW','Storage_Charge_MW','Storage_Discharge_MW', ...
    'Storage_E_Start_MWh','Storage_E_After_Loss_MWh','Storage_E_Next_MWh', ...
    'Storage_Standing_Loss_MWh','Storage_Charge_Loss_MWh','Storage_Discharge_Loss_MWh', ...
    'Gas_Heat_MW','Unmet_Heat_MW','Supplied_Heat_MW','System_Balance_Residual_MWh','Mode'};
t=array2table(zeros(0,numel(names)),'VariableNames',names);
raw=struct('dispatch_times_h',[],'hp_times_h',[],'energy_start_times_h',[],'joined',false);
available=who(result);
if ~all(ismember({'dispatch_trace_v24','hp_trace_v24','energy_start_trace_v24'},available)), return; end
d=result.dispatch_trace_v24; h=result.hp_trace_v24; e=result.energy_start_trace_v24;
raw.dispatch_times_h=d.Time(:)'; raw.hp_times_h=h.Time(:)'; raw.energy_start_times_h=e.Time(:)';
if isempty(d.Time), raw.joined=true; return; end
[hpFound,hi]=ismember(d.Time,h.Time); [energyFound,ei]=ismember(d.Time,e.Time);
if ~all(hpFound) || ~all(energyFound), return; end
y=samples(d,13); ports=samples(h,8); u=ports(hi,:); energy=reshape(e.Data,[],1); energy=energy(ei);
n=numel(d.Time); input=repmat(x(:)',n,1);
values=[d.Time,input,u(:,5),u(:,2),y(:,2),u(:,3),u(:,4),u(:,6),u(:,7),u(:,8), ...
    y(:,3),y(:,4),energy,y(:,7),y(:,8),y(:,9),y(:,10),y(:,11),y(:,5),y(:,6),y(:,12),y(:,13),y(:,1)];
t=array2table(values,'VariableNames',names); raw.joined=true;
end

function c=configuration(b,dt)
c=default_config_v2(); p=b.p; h=b.h; c.sim.dt_h=dt;
c.storage.capacity_MWh=p(2); c.storage.charge_limit_MW=p(3); c.storage.discharge_limit_MW=p(4);
c.storage.eta_charge=p(5); c.storage.eta_discharge=p(6); c.storage.loss_fraction_per_h=p(7);
c.storage.initial_soc=b.E/p(2); c.backup.max_heat_MW=p(8);
c.hp.max_heat_output_MW=h(1); c.hp.carnot_efficiency=h(2); c.hp.cop_min=h(3);
c.hp.cop_max=h(4); c.hp.part_load_penalty=h(5);
if h(6)==0, c.model.hp_backend='carnot'; else, c.model.hp_backend='lift_polynomial'; end
c.hp.poly_c0=h(7); c.hp.poly_c1=h(8); c.hp.poly_c2=h(9);
end

function ok=near(a,b)
if ~isequal(size(a),size(b)), ok=false; return; end
both=isnan(a)&isnan(b); finite=isfinite(a)&isfinite(b);
ok=all(both|finite,'all') && all(abs(a(finite)-b(finite))<=1e-9+1e-11*abs(b(finite)),'all');
end

function values=samples(ts,width)
raw=ts.Data; n=numel(ts.Time);
if ismatrix(raw) && isequal(size(raw),[n width]), values=raw;
elseif size(raw,1)==width && numel(raw)==n*width, values=reshape(raw,width,n)';
else, error('DCHR:v27:TraceDimensions','Unexpected timeseries dimensions.'); end
end

function writejson(path,value)
fid=fopen(path,'w'); assert(fid>0,'DCHR:v27:Write','Cannot open evidence file.');
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end

function value=sha256(path)
fid=fopen(path,'rb'); assert(fid>0); bytes=fread(fid,Inf,'*uint8'); fclose(fid);
digest=java.security.MessageDigest.getInstance('SHA-256'); digest.update(bytes);
value=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
