function outputDir=run_stateflow_gate_faults_v24()
% Actual saved-model gate failure paths; mutate only loaded helper, never save.
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(here));
addpath(fullfile(root,'matlab'),here);
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
outputDir=fullfile(root,'results',['stateflow_gate_faults_v24_' stamp]);
assert(~isfolder(outputDir)); mkdir(outputDir);
mdl='DCHR_Dispatch_Stateflow_v24'; modelPath=fullfile(here,[mdl '.slx']);
before=sha256(modelPath); load_system(modelPath);
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
old=Simulink.fileGenControl('getConfig');
restoreFilegen=onCleanup(@()Simulink.fileGenControl('setConfig','config',old)); %#ok<NASGU>
Simulink.fileGenControl('set','CacheFolder',fullfile(outputDir,'cache'), ...
    'CodeGenFolder',fullfile(outputDir,'codegen'),'createDir',true);
rt=sfroot; chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Thermal_Dispatch']);
helper=chart.find('-isa','Stateflow.EMFunction','Name','stateflow_allocate_v24');
original=helper.Script; restoreSource=onCleanup(@()set(helper,'Script',original)); %#ok<NASGU>
assert(strcmp(original,fileread(fullfile(here,'stateflow_allocate_v24.m'))));
s=Simulink.SimulationInput(mdl);
s=s.setVariable('dchr_dt_v24',1,'Workspace',mdl);
s=s.setVariable('dchr_stop_v24',0,'Workspace',mdl);
s=s.setVariable('dchr_input_v24',[0 6 35 70 5;1 6 35 70 5],'Workspace',mdl);
s=s.setVariable('dchr_p_v24',[1 10 3 4 .9 .8 .01 2],'Workspace',mdl);
s=s.setVariable('dchr_h_v24',[8 .45 1.2 8 .08 0 4 0 0],'Workspace',mdl);
s=s.setVariable('dchr_E0_v24',1,'Workspace',mdl);
baseline=sim(s); save(fullfile(outputDir,'unmutated_baseline_simulation.mat'),'baseline');
faults={ ...
    'false_system_residual','y(13)=y(13)+.1;','System first-law failure or false residual.'; ...
    'false_next_energy','y(8)=y(8)+.1;','TES first-law failure.'; ...
    'negative_backup_flow','y(5)=-1;','Negative dispatch/HP port.'; ...
    'wrong_active_mode','y(1)=5;','Active state does not match delivered flows.'; ...
    'false_standing_loss','y(9)=y(9)+.1;','TES loss reporting mismatch.'; ...
    'unallocated_hp_heat','y(2)=y(2)-.1;','Unallocated HP condenser heat.'; ...
    'simultaneous_tes_ports','y(4)=.1;','Simultaneous TES charge and discharge.'; ...
    'false_useful_heat','y(12)=y(12)+.1;','Useful heat mismatch.'};
records=struct('id',{},'mutation',{},'expected_message',{},'simulation_attempted',{}, ...
    'rejected',{},'actual_identifier',{},'cause_identifiers',{},'message',{}, ...
    'expected_gate_observed',{},'accepted_invalid_trace',{},'failure_report',{},'restored_source',{});
for k=1:size(faults,1)
    helper.Script=regexprep(original,'\nend\s*$',sprintf('\n%% QA in-memory corruption\n%s\nend\n',faults{k,2}));
    assert(~strcmp(helper.Script,original));
    rejected=false; ids={}; actual=''; message=''; report=''; accepted=false;
    try
        invalidResult=sim(s); accepted=true;
        save(fullfile(outputDir,[faults{k,1} '_UNEXPECTED_ACCEPTANCE.mat']),'invalidResult');
    catch failure
        rejected=true; actual=failure.identifier; ids=identifiers(failure);
        message=failure.message; report=getReport(failure,'extended','hyperlinks','off');
    end
    helper.Script=original;
    observed=contains(report,'Runtime_Contract_Gate') && contains(report,faults{k,3});
    path=fullfile(outputDir,[faults{k,1} '_rejection.txt']);
    fid=fopen(path,'w'); assert(fid>0); fprintf(fid,'%s\n',report); fclose(fid);
    records(end+1)=struct('id',faults{k,1},'mutation',faults{k,2},'expected_message',faults{k,3}, ...
        'simulation_attempted',true,'rejected',rejected,'actual_identifier',actual, ...
        'cause_identifiers',{ids},'message',message,'expected_gate_observed',observed, ...
        'accepted_invalid_trace',accepted,'failure_report',path, ...
        'restored_source',strcmp(helper.Script,original)); %#ok<AGROW>
    fprintf('ACTUAL_GATE_FAULT %s rejected=%d expected_gate=%d\n',faults{k,1},rejected,observed);
end
summary=struct('cases',size(faults,1),'rejected',sum([records.rejected]), ...
    'expected_gate_observed',sum([records.expected_gate_observed]), ...
    'accepted_invalid_traces',sum([records.accepted_invalid_trace]),'records',records, ...
    'unmutated_baseline_executed',true,'saved_model_modified',false, ...
    'embedded_source_restored',strcmp(helper.Script,original), ...
    'restored_source',strcmp(helper.Script,original), ...
    'model_sha256_before',before,'model_sha256_after',sha256(modelPath));
fid=fopen(fullfile(outputDir,'gate_fault_rejections_v24.json'),'w'); assert(fid>0);
fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true)); fclose(fid);
assert(summary.rejected==summary.cases && summary.expected_gate_observed==summary.cases && ...
    summary.accepted_invalid_traces==0 && summary.embedded_source_restored && ...
    strcmp(summary.model_sha256_before,summary.model_sha256_after), ...
    'DCHR:v24:GateFaultAcceptance','See actual-gate fault evidence.');
disp(rmfield(summary,'records')); fprintf('GATE_FAULT_OUTPUT=%s\n',outputDir);
end

function ids=identifiers(failure)
ids={failure.identifier};
for k=1:numel(failure.cause), ids=[ids identifiers(failure.cause{k})]; end %#ok<AGROW>
end

function value=sha256(path)
fid=fopen(path,'rb'); assert(fid>0); bytes=fread(fid,Inf,'*uint8'); fclose(fid);
digest=java.security.MessageDigest.getInstance('SHA-256'); digest.update(bytes);
value=lower(reshape(dec2hex(typecast(digest.digest(),'uint8'),2).',1,[]));
end
