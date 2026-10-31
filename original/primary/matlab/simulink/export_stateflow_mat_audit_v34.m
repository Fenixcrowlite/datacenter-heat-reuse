function export_stateflow_mat_audit_v34(folder)
% Read-only independent re-export from saved SimulationOutputs.
source=fullfile(folder,'mat_audit_source');assert(~isfolder(source));mkdir(source);
copyfile([mfilename('fullpath') '.m'],source);
spec=jsondecode(fileread(fullfile(folder,'source_snapshot','spec','cases.json')));
valid=struct('id',{},'y',{},'segments',{},'plan',{},'time_h',{},'energy_start',{},'clock_start',{},'clock_end',{},'error_message',{});
legacy=struct('id',{},'y',{},'time_h',{},'error_message',{});
for k=1:numel(spec.cases)
    c=spec.cases(k);saved=load(fullfile(folder,[c.id '_simulation.mat']),'result');r=saved.result;
    valid(end+1)=struct('id',c.id,'y',samples(r.dispatch_trace_v34,25),'segments',samples(r.segment_trace_v34,1792), ...
        'plan',samples(r.plan_trace_v34,1152),'time_h',r.dispatch_trace_v34.Time,'energy_start',samples(r.energy_start_trace_v34,1), ...
        'clock_start',samples(r.clock_start_trace_v34,2),'clock_end',samples(r.clock_end_trace_v34,2),'error_message',r.ErrorMessage); %#ok<AGROW>
    path=fullfile(folder,[c.id '_v32_simulation.mat']);
    if isfile(path)
        saved=load(path,'oldresult');r=saved.oldresult;
        legacy(end+1)=struct('id',c.id,'y',samples(r.dispatch_trace_v32,25),'time_h',r.dispatch_trace_v32.Time,'error_message',r.ErrorMessage); %#ok<AGROW>
    end
end
faults=jsondecode(fileread(fullfile(folder,'fault_evidence_v34.json')));
diagnostics=struct('id',{},'phase',{},'time_h',{},'error_message',{});
for k=1:numel(faults)
    saved=load(fullfile(folder,[faults(k).id '_fault_simulation.mat']),'result');r=saved.result;
    d=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;
    diagnostics(end+1)=struct('id',faults(k).id,'phase',d.SimulationPhase,'time_h',d.SimulationTime,'error_message',r.ErrorMessage); %#ok<AGROW>
end
a=load(fullfile(folder,'pre_fault_clean_simulation.mat'),'baseline');b=load(fullfile(folder,'post_fault_clean_simulation.mat'),'result');
report=struct('valid_cases',valid,'legacy_cases',legacy,'faults',diagnostics, ...
    'restored_segments_equal',isequaln(a.baseline.segment_trace_v34.Data,b.result.segment_trace_v34.Data), ...
    'restored_clock_equal',isequaln(a.baseline.clock_end_trace_v34.Data,b.result.clock_end_trace_v34.Data), ...
    'restored_error',b.result.ErrorMessage,'evidence_class','read_only_saved_SimulationOutput_export');
path=fullfile(folder,'mat_audit_v34.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true)); %#ok<NASGU>
fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected saved trace dimensions');end
end
