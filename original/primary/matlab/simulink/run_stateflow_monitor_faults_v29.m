function outputDir=run_stateflow_monitor_faults_v29()
% Executed monitor-corruption acceptance on preserved saved model release v28.
% Checkpoint v29 mutates only a loaded allocation helper; never saves the model.
% Faults are implementation corruption, not equipment faults or physics evidence.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_monitor_v29_' stamp]);
assert(~isfolder(outputDir),'DCHR:v29:EvidenceExists','Refuse evidence overwrite.');
mkdir(outputDir);
fprintf('MATLAB_VERSION=%s\nSTATEFLOW_LICENSE=%d\n',version,license('test','Stateflow'));
assert(license('test','Stateflow'),'DCHR:v29:Unavailable','Stateflow license unavailable.');
specPath=fullfile(root,'audit','stateflow_monitor_fault_cases_v29.json');
spec=jsondecode(fileread(specPath));
mdl='DCHR_Dispatch_Stateflow_v28'; modelPath=fullfile(here,[mdl '.slx']);
sourcePath=fullfile(here,'stateflow_allocate_v28.m');
runnerPath=[mfilename('fullpath') '.m'];
assert(strcmp(spec.model_file,'matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx') && ...
    strcmp(spec.helper,'stateflow_allocate_v28'),'DCHR:v29:Scope','Fault specification targets another model.');
before=sha256(modelPath); sourceBefore=sha256(sourcePath);
assert(strcmp(before,spec.model_sha256),'DCHR:v29:ModelHash','Saved model differs from independently specified v28 baseline.');
assert(~bdIsLoaded(mdl),'DCHR:v29:LoadedModel','Use a fresh MATLAB batch session.');
paths={ 'matlab/simulink/run_stateflow_monitor_faults_v29.m', ...
    'audit/stateflow_monitor_fault_cases_v29.json', ...
    'matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx', ...
    'matlab/simulink/build_dispatch_stateflow_v28.m', ...
    'matlab/simulink/stateflow_allocate_v28.m', ...
    'matlab/simulink/stateflow_choose_mode_v28.m', ...
    'matlab/simulink/stateflow_contract_gate_v28.m', ...
    'matlab/simulink/dchr_stateflow_hp_v28.m', ...
    'matlab/+dchr/simulate_dispatch_v28.m', ...
    'matlab/+dchr/+components/storage_step_v28.m', ...
    'matlab/+dchr/+components/heat_pump_step_v14.m', ...
    'matlab/default_config_v2.m', 'matlab/default_config.m'};
snapshotDir=fullfile(outputDir,'source_snapshot'); mkdir(snapshotDir);
sourceHashesBefore=hash_sources(root,paths);
manifestFiles=struct('project_relative_path',{},'snapshot_relative_path',{}, ...
    'sha256_before',{},'sha256_after',{},'snapshot_sha256',{},'unchanged',{});
for k=1:numel(paths)
    destination=fullfile(snapshotDir,paths{k});
    if ~isfolder(fileparts(destination)), mkdir(fileparts(destination)); end
    copyfile(fullfile(root,paths{k}),destination);
    snapHash=sha256(destination);
    assert(strcmp(snapHash,sourceHashesBefore(k).sha256),'DCHR:v29:Snapshot','Source changed during evidence snapshot.');
    manifestFiles(end+1)=struct('project_relative_path',paths{k}, ...
        'snapshot_relative_path',['source_snapshot/' paths{k}], ...
        'sha256_before',sourceHashesBefore(k).sha256,'sha256_after','', ...
        'snapshot_sha256',snapHash,'unchanged',false); %#ok<AGROW>
end
manifestBeforePath=fullfile(outputDir,'source_snapshot_manifest_before_v29.json');
writejson(manifestBeforePath,struct('version','0.29','timestamp_utc',stamp, ...
    'created_before_simulations',true,'files',manifestFiles));
load_system(modelPath);
modelCleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
previous=Simulink.fileGenControl('getConfig');
filegenCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',previous)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
rt=sfroot; chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
assert(numel(chart)==1,'DCHR:v29:Chart','Expected exactly one dispatch chart.');
helper=chart.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v28');
choose=chart.find('-isa','Stateflow.EMFunction','Name','stateflow_choose_mode_v28');
gate=rt.find('-isa','Stateflow.EMChart','Path',[mdl '/Runtime_Contract_Gate']);
assert(numel(helper)==1 && numel(choose)==1 && numel(gate)==1, ...
    'DCHR:v29:Helper','Expected exact allocation, choice and contract-gate objects.');
original=helper.Script;
embeddedMatches=strcmp(original,fileread(sourcePath)) && ...
    strcmp(choose.Script,fileread(fullfile(here,'stateflow_choose_mode_v28.m'))) && ...
    strcmp(gate.Script,fileread(fullfile(here,'stateflow_contract_gate_v28.m')));
assert(embeddedMatches,'DCHR:v29:SourceMismatch','Saved model embeds stale allocation, choice or gate source.');
helperCleanup=onCleanup(@()restore_helper(helper,original,mdl)); %#ok<NASGU>
lineHandles=get_param([mdl '/Runtime_Contract_Gate'],'LineHandles');
destinations=get_param(lineHandles.Outport(1),'DstBlockHandle');
gateFeeds=all(ismember([get_param([mdl '/Next_TES_Energy'],'Handle') ...
    get_param([mdl '/Dispatch_Trace'],'Handle')],destinations));
assert(gateFeeds,'DCHR:v29:GateWiring','Runtime gate must drive trace and TES feedback.');
bindingPath=fullfile(outputDir,'saved_model_binding_v29.json');
writejson(bindingPath,struct('model_release','0.28','model_sha256',before, ...
    'chart_path',chart.Path,'sample_time',chart.SampleTime, ...
    'saved_embedded_sources_match',embeddedMatches,'contract_gate_drives_feedback_and_trace',gateFeeds, ...
    'embedded_allocate_script',original,'embedded_choose_script',choose.Script, ...
    'embedded_contract_gate_script',gate.Script));
b=spec.baseline;
assert(b.model_dt_h>0 && b.p(1)==b.model_dt_h && b.stop_time_h==b.model_dt_h && ...
    numel(b.input_x)==4 && numel(b.p)==8 && numel(b.h)==9, ...
    'DCHR:v29:Clock','Independent two-sample baseline clock/port mismatch.');
s=Simulink.SimulationInput(mdl);
s=s.setVariable('dchr_dt_v28',b.model_dt_h,'Workspace',mdl);
s=s.setVariable('dchr_stop_v28',b.stop_time_h,'Workspace',mdl);
s=s.setVariable('dchr_input_v28',[(0:1)'*b.model_dt_h repmat(b.input_x(:)',2,1)],'Workspace',mdl);
s=s.setVariable('dchr_p_v28',b.p(:)','Workspace',mdl);
s=s.setVariable('dchr_h_v28',b.h(:)','Workspace',mdl);
s=s.setVariable('dchr_E0_v28',b.initial_energy_MWh,'Workspace',mdl);
assert(strcmp(get_param(mdl,'SimulationMode'),'normal'),'DCHR:v29:SimulationMode','Expected normal-mode host MATLAB adapter.');
baseline=sim(s);
save(fullfile(outputDir,'unmutated_baseline_simulation.mat'),'baseline');
baselineTrace=trace(baseline);
baselineTracePath=fullfile(outputDir,'baseline_trace_v29.csv');
writetable(baselineTrace,baselineTracePath);
assert(height(baselineTrace)==2 && isequal(baselineTrace.Time_h,[0;b.model_dt_h]), ...
    'DCHR:v29:TimeGrid','Expected two actual model samples.');
reference=baseline_reference(b);
writetable(reference,fullfile(outputDir,'baseline_matlab_reference_v29.csv'));
referenceMatches=matches_reference(baselineTrace,reference);
assert(referenceMatches,'DCHR:v29:BaselineReference','Unmutated executable baseline differs from separate v28 numerical dispatch.');
fprintf('UNMUTATED_BASELINE_EXECUTED intervals=%d reference_matches=%d\n',height(baselineTrace),referenceMatches);
cases=spec.cases;
assert(numel(unique({cases.id}))==numel(cases),'DCHR:v29:DuplicateCase','Independent case IDs must be unique.');
records=struct('id',{},'mutation',{},'expected_message',{},'simulation_attempted',{}, ...
    'rejected',{},'actual_identifier',{},'cause_identifiers',{},'message',{}, ...
    'expected_gate_observed',{},'compilation_failure_detected',{},'accepted_invalid_trace',{}, ...
    'failure_report',{},'failure_report_sha256',{},'restored_source',{}, ...
    'mutation_source_file',{},'mutation_source_sha256',{},'capture_errors',{}, ...
    'diagnostic',{},'diagnostic_file',{},'diagnostic_sha256',{}, ...
    'captured_simulation_file',{},'captured_simulation_sha256',{}, ...
    'raw_trace_times',{},'raw_trace_times_file',{},'raw_trace_times_sha256',{}, ...
    'captured_runtime_rejection',{});
for k=1:numel(cases)
    c=cases(k);
    assert(~isempty(regexp(c.id,'^[a-z][a-z0-9_]*$','once')), ...
        'DCHR:v29:CaseName','Case ID must be a local evidence basename.');
    mutated=regexprep(original,'\nend\s*$',sprintf('\n%% Independent QA in-memory corruption\n%s\nend\n',c.mutation));
    assert(~strcmp(mutated,original),'DCHR:v29:Mutation','Mutation failed to change helper.');
    mutationPath=fullfile(outputDir,[c.id '_in_memory_allocation.m']);
    writetext(mutationPath,mutated);
    helper.Script=mutated;
    assert(strcmp(helper.Script,mutated),'DCHR:v29:MutationBinding','Loaded helper did not accept the specified corruption.');
    captured=sim(s.setModelParameter('CaptureErrors','on'));
    capturedPath=fullfile(outputDir,[c.id '_captured_simulation.mat']);
    save(capturedPath,'captured');
    m=metadata(captured); raw=raw_trace_times(captured);
    diagnosticPath=fullfile(outputDir,[c.id '_diagnostic.json']);
    rawPath=fullfile(outputDir,[c.id '_raw_trace_times.json']);
    writejson(diagnosticPath,m); writejson(rawPath,raw);
    capturedRuntime=strcmp(m.stop_event,'DiagnosticError') && strcmp(m.error_phase,'Execution') && ...
        isequal(m.error_time_h,0) && isequal(m.stop_event_time_h,0) && ...
        contains(m.error_message,'Runtime_Contract_Gate') && contains(m.error_message,c.expected_message) && ...
        isempty(raw.dispatch_times_h);
    rejected=false; actual=''; ids={}; message=''; report=''; accepted=false;
    try
        invalidResult=sim(s.setModelParameter('CaptureErrors','off')); accepted=true;
        save(fullfile(outputDir,[c.id '_UNEXPECTED_ACCEPTANCE.mat']),'invalidResult');
    catch failure
        rejected=true; actual=failure.identifier; ids=identifiers(failure);
        message=failure.message; report=getReport(failure,'extended','hyperlinks','off');
    end
    helper.Script=original;
    restored=strcmp(helper.Script,original);
    compilationFailure=any(contains(lower(report), ...
        {'errors occurred during parsing','error evaluating parameter','compilation of model', ...
         'error compiling','parse error','syntax error'}));
    observed=capturedRuntime && rejected && contains(report,'Runtime_Contract_Gate') && ...
        contains(report,c.expected_message) && ~compilationFailure;
    reportPath=fullfile(outputDir,[c.id '_rejection.txt']);
    writetext(reportPath,[report newline]);
    records(end+1)=struct('id',c.id,'mutation',c.mutation,'expected_message',c.expected_message, ...
        'simulation_attempted',true,'rejected',rejected,'actual_identifier',actual, ...
        'cause_identifiers',{ids},'message',message,'expected_gate_observed',observed, ...
        'compilation_failure_detected',compilationFailure,'accepted_invalid_trace',accepted, ...
        'failure_report',reportPath,'failure_report_sha256',sha256(reportPath), ...
        'restored_source',restored,'mutation_source_file',mutationPath, ...
        'mutation_source_sha256',sha256(mutationPath),'capture_errors','on', ...
        'diagnostic',m,'diagnostic_file',diagnosticPath,'diagnostic_sha256',sha256(diagnosticPath), ...
        'captured_simulation_file',capturedPath,'captured_simulation_sha256',sha256(capturedPath), ...
        'raw_trace_times',raw,'raw_trace_times_file',rawPath,'raw_trace_times_sha256',sha256(rawPath), ...
        'captured_runtime_rejection',capturedRuntime); %#ok<AGROW>
    fprintf('ACTUAL_MONITOR_FAULT %s rejected=%d expected_gate=%d captured_runtime=%d compile_failure=%d restored=%d\n', ...
        c.id,rejected,observed,capturedRuntime,compilationFailure,restored);
end
assert(strcmp(helper.Script,original),'DCHR:v29:Restore','Embedded source not restored.');
restoredResult=sim(s);
save(fullfile(outputDir,'restored_baseline_simulation.mat'),'restoredResult');
restoredTrace=trace(restoredResult);
restoredTracePath=fullfile(outputDir,'restored_trace_v29.csv');
writetable(restoredTrace,restoredTracePath);
same=isequaln(table2array(baselineTrace),table2array(restoredTrace));
fprintf('RESTORED_BASELINE_EXECUTED intervals=%d exact_match=%d\n',height(restoredTrace),same);
sourceHashesAfter=hash_sources(root,paths);
snapshotHashes=hash_sources(outputDir,strcat('source_snapshot/',paths));
unchanged=true;
for k=1:numel(paths)
    manifestFiles(k).sha256_after=sourceHashesAfter(k).sha256;
    manifestFiles(k).unchanged=strcmp(manifestFiles(k).sha256_before,sourceHashesAfter(k).sha256) && ...
        strcmp(manifestFiles(k).snapshot_sha256,snapshotHashes(k).sha256);
    unchanged=unchanged && manifestFiles(k).unchanged;
end
for k=1:numel(snapshotHashes)
    snapshotHashes(k).path=strrep(fullfile(outputDir,snapshotHashes(k).path),[root filesep],'');
end
manifestPath=fullfile(outputDir,'source_snapshot_manifest_v29.json');
writejson(manifestPath,struct('version','0.29','timestamp_utc',stamp, ...
    'created_before_simulations',true,'all_sources_and_snapshots_unchanged',unchanged,'files',manifestFiles));
summary=struct('version','0.29','checkpoint_version','0.29','model_release','0.28', ...
    'timestamp_utc',stamp,'matlab_version',version, ...
    'stateflow_license',license('test','Stateflow'),'simulation_mode','normal', ...
    'model_path',modelPath,'model_sha256_before',before,'model_sha256_after',sha256(modelPath), ...
    'source_file',sourcePath,'allocation_source_sha256_before',sourceBefore,'allocation_source_sha256_after',sha256(sourcePath), ...
    'source_sha256_before',sourceHashesBefore,'source_sha256_after',sourceHashesAfter, ...
    'source_snapshot_hashes',snapshotHashes,'source_snapshot_directory',snapshotDir, ...
    'source_snapshot_complete',true,'source_snapshots_unchanged',unchanged, ...
    'snapshot_manifest_file',manifestPath,'snapshot_manifest_sha256',sha256(manifestPath), ...
    'source_snapshot_manifest_before_file',manifestBeforePath, ...
    'source_snapshot_manifest_before_sha256',sha256(manifestBeforePath), ...
    'saved_model_binding_file',bindingPath,'saved_model_binding_sha256',sha256(bindingPath), ...
    'saved_embedded_sources_match',embeddedMatches,'contract_gate_drives_feedback_and_trace',gateFeeds, ...
    'spec_file',specPath,'spec_sha256',sha256(specPath), ...
    'runner_file',runnerPath,'runner_sha256',sha256(runnerPath), ...
    'cases',numel(cases),'rejected',sum([records.rejected]), ...
    'expected_gate_observed',sum([records.expected_gate_observed]), ...
    'captured_runtime_rejections',sum([records.captured_runtime_rejection]), ...
    'compilation_failures',sum([records.compilation_failure_detected]), ...
    'accepted_invalid_traces',sum([records.accepted_invalid_trace]),'records',records, ...
    'unmutated_baseline_executed',true,'baseline_intervals',height(baselineTrace), ...
    'baseline_matlab_reference_matches',referenceMatches, ...
    'baseline_trace_file',baselineTracePath,'baseline_trace_sha256',sha256(baselineTracePath), ...
    'restored_baseline_executed',true,'restored_intervals',height(restoredTrace),'restored_baseline_matches',same, ...
    'restored_trace_file',restoredTracePath,'restored_trace_sha256',sha256(restoredTracePath), ...
    'embedded_source_restored',strcmp(helper.Script,original), ...
    'saved_model_modified',~strcmp(before,sha256(modelPath)), ...
    'simulink_executed',true,'stateflow_executed',true,'standalone_codegen',false, ...
    'primary_paper_replication',false,'equipment_validation',false);
writejson(fullfile(outputDir,'gate_fault_rejections_v29.json'),summary);
assert(summary.rejected==summary.cases && summary.expected_gate_observed==summary.cases && ...
    summary.captured_runtime_rejections==summary.cases && ...
    summary.compilation_failures==0 && summary.accepted_invalid_traces==0 && ...
    summary.embedded_source_restored && same && height(restoredTrace)==2 && unchanged && ...
    strcmp(summary.model_sha256_before,summary.model_sha256_after) && ...
    strcmp(summary.allocation_source_sha256_before,summary.allocation_source_sha256_after), ...
    'DCHR:v29:FaultAcceptance','See completed actual-model monitor evidence; compile errors cannot count as monitor acceptance.');
disp(rmfield(summary,{'records','source_sha256_before','source_sha256_after','source_snapshot_hashes'}));
fprintf('MONITOR_OUTPUT=%s\n',outputDir);
end

function r=baseline_reference(b)
p=b.p; h=b.h; cfg=default_config_v2(); cfg.sim.dt_h=p(1);
cfg.storage.capacity_MWh=p(2); cfg.storage.charge_limit_MW=p(3); cfg.storage.discharge_limit_MW=p(4);
cfg.storage.eta_charge=p(5); cfg.storage.eta_discharge=p(6); cfg.storage.continuous_loss_rate_per_h=p(7);
cfg.storage.initial_soc=0;
if p(2)>0, cfg.storage.initial_soc=b.initial_energy_MWh/p(2); end
cfg.backup.max_heat_MW=p(8); cfg.hp.max_heat_output_MW=h(1); cfg.hp.carnot_efficiency=h(2);
cfg.hp.cop_min=h(3); cfg.hp.cop_max=h(4); cfg.hp.part_load_penalty=h(5);
if h(6)==0, cfg.model.hp_backend='carnot'; else, cfg.model.hp_backend='lift_polynomial'; end
cfg.hp.poly_c0=h(7); cfg.hp.poly_c1=h(8); cfg.hp.poly_c2=h(9);
x=array2table(repmat(b.input_x(:)',2,1),'VariableNames', ...
    {'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'});
r=dchr.simulate_dispatch_v28(cfg,x);
end

function ok=matches_reference(t,r)
names=intersect(t.Properties.VariableNames,r.Properties.VariableNames);
ok=height(t)==height(r);
for k=1:numel(names)
    a=t.(names{k}); b=r.(names{k}); finite=isfinite(a)&isfinite(b);
    ok=ok && all(finite|(isnan(a)&isnan(b))) && all(abs(a(finite)-b(finite))<=1e-9+1e-11*abs(b(finite)));
end
end

function restore_helper(helper,original,mdl)
% MATLAB does not guarantee ordering among separate onCleanup objects.
% Once the model is closed, its in-memory chart/helper no longer exists.
if bdIsLoaded(mdl)
    helper.Script=original;
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

function out=diagnostic(d)
children=cell(size(d.cause));
for j=1:numel(d.cause), children{j}=diagnostic(d.cause{j}); end
out=struct('identifier',d.identifier,'message',d.message,'cause',{children});
end

function raw=raw_trace_times(result)
raw=struct('dispatch_available',false,'hp_available',false,'energy_start_available',false, ...
    'dispatch_times_h',[],'hp_times_h',[],'energy_start_times_h',[]);
available=who(result);
raw.logged_output_names=available;
names={'dispatch_trace_v28','hp_trace_v28','energy_start_trace_v28'};
flags={'dispatch_available','hp_available','energy_start_available'};
times={'dispatch_times_h','hp_times_h','energy_start_times_h'};
for k=1:numel(names)
    if ismember(names{k},available)
        ts=result.(names{k}); raw.(flags{k})=true; raw.(times{k})=ts.Time(:)';
    end
end
end

function ids=identifiers(failure)
ids={failure.identifier};
for k=1:numel(failure.cause), ids=[ids identifiers(failure.cause{k})]; end %#ok<AGROW>
end

function t=trace(result)
y=samples(result.dispatch_trace_v28,13); u=samples(result.hp_trace_v28,8);
e=reshape(result.energy_start_trace_v28.Data,[],1);
t=table(result.dispatch_trace_v28.Time,y(:,1),u(:,5),u(:,2),u(:,3),u(:,4),u(:,6), ...
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
else, error('DCHR:v29:TraceDimensions','Unexpected timeseries dimensions.');
end
end

function rows=hash_sources(root,paths)
rows=struct('path',{},'sha256',{});
for k=1:numel(paths)
    rows(end+1)=struct('path',paths{k},'sha256',sha256(fullfile(root,paths{k}))); %#ok<AGROW>
end
end

function writejson(path,value)
writetext(path,[jsonencode(value,PrettyPrint=true) newline]);
end

function writetext(path,value)
fid=fopen(path,'w','n','UTF-8'); assert(fid>0,'DCHR:v29:Write','Cannot write evidence.');
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s',value);
end

function value=sha256(path)
fid=fopen(path,'rb'); assert(fid>0,'DCHR:v29:Hash','Cannot read provenance file.');
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
bytes=fread(fid,Inf,'*uint8');
digest=java.security.MessageDigest.getInstance('SHA-256'); digest.update(bytes);
value=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
