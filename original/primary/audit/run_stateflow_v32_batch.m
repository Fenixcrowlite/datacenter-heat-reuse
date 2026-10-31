function run_stateflow_v32_batch(mode,spec)
root=fileparts(fileparts(mfilename('fullpath')));cd(root);
addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
diary(fullfile(root,'automation','logs',['stateflow_' mode '_v32_' stamp '.log']));
cleanup=onCleanup(@()diary('off')); %#ok<NASGU>
old=Simulink.fileGenControl('getConfig');
genCleanup=onCleanup(@()Simulink.fileGenControl('setConfig','config',old)); %#ok<NASGU>
work=fullfile(root,'results',['stateflow_' mode '_work_v32_' stamp]);mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
if strcmp(mode,'build')
    build_dispatch_stateflow_v32();
    r=sim('DCHR_Dispatch_Stateflow_v32');save(fullfile(work,'initial_simulation.mat'),'r');
    disp(r.dispatch_trace_v32.Data);assert(isempty(r.ErrorMessage));
elseif strcmp(mode,'accept')
    out=run_stateflow_acceptance_v32(spec);export_stateflow_mat_audit_v32(out);
else,error('Unknown operation');end
fprintf('BATCH_%s_PASS\n',upper(mode));
end
