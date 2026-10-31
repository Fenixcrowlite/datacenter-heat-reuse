function export_stateflow_mat_audit_v32(folder)
% Read-only MAT re-export, independent of harness comparison tables.
source=fullfile(folder,'mat_audit_source');assert(~isfolder(source));mkdir(source);
copyfile([mfilename('fullpath') '.m'],source);
spec=jsondecode(fileread(fullfile(folder,'source_snapshot','spec','cases.json')));
valid=struct('id',{},'y',{},'segments',{},'time_h',{},'energy_start',{},'error_message',{});
legacy=struct('id',{},'y',{},'u',{},'time_h',{},'energy_start',{},'error_message',{});
for k=1:numel(spec.cases)
    if iscell(spec.cases),c=spec.cases{k};else,c=spec.cases(k);end
    saved=load(fullfile(folder,[c.id '_simulation.mat']),'result');r=saved.result;
    valid(end+1)=struct('id',c.id,'y',samples(r.dispatch_trace_v32,25), ...
        'segments',samples(r.segment_trace_v32,50),'time_h',r.dispatch_trace_v32.Time, ...
        'energy_start',reshape(r.energy_start_trace_v32.Data,[],1),'error_message',r.ErrorMessage); %#ok<AGROW>
    if any(strcmp(c.id,spec.comparison_ids))
        saved=load(fullfile(folder,[c.id '_v30_simulation.mat']),'oldresult');r=saved.oldresult;
        legacy(end+1)=struct('id',c.id,'y',samples(r.dispatch_trace_v30,17),'u',samples(r.hp_trace_v30,8), ...
            'time_h',r.dispatch_trace_v30.Time,'energy_start',reshape(r.energy_start_trace_v30.Data,[],1), ...
            'error_message',r.ErrorMessage); %#ok<AGROW>
    end
end
faults=jsondecode(fileread(fullfile(folder,'fault_evidence_v32.json')));
diagnostics=struct('id',{},'phase',{},'time_h',{},'stop_event',{},'error_message',{},'samples',{});
for k=1:numel(faults)
    saved=load(fullfile(folder,[faults(k).id '_fault_simulation.mat']),'result');r=saved.result;
    info=r.SimulationMetadata.ExecutionInfo;d=info.ErrorDiagnostic;
    n=0;if any(strcmp(r.who,'dispatch_trace_v32')) && isa(r.dispatch_trace_v32,'timeseries'),n=numel(r.dispatch_trace_v32.Time);end
    diagnostics(end+1)=struct('id',faults(k).id,'phase',d.SimulationPhase,'time_h',d.SimulationTime, ...
        'stop_event',info.StopEvent,'error_message',r.ErrorMessage,'samples',n); %#ok<AGROW>
end
a=load(fullfile(folder,'pre_fault_clean_simulation.mat'),'baseline');
b=load(fullfile(folder,'post_fault_clean_simulation.mat'),'result');
report=struct('valid_cases',valid,'legacy_cases',legacy,'faults',diagnostics, ...
    'restored_segments_equal',isequaln(a.baseline.segment_trace_v32.Data,b.result.segment_trace_v32.Data), ...
    'restored_error',b.result.ErrorMessage,'evidence_class','read_only_saved_SimulationOutput_export');
path=fullfile(folder,'mat_audit_v32.json');assert(~isfile(path));
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected saved trace dimensions');end
end
