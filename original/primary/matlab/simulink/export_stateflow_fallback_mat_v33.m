function export_stateflow_fallback_mat_v33(folder)
% Read-only second extraction from saved SimulationOutput, separate from tables.
spec=jsondecode(fileread(fullfile(folder,'source_snapshot','spec','cases.json')));
valid=struct('id',{},'y',{},'segments',{},'time_h',{},'energy_start',{},'error_message',{});
for k=1:numel(spec.cases)
    if iscell(spec.cases),c=spec.cases{k};else,c=spec.cases(k);end
    saved=load(fullfile(folder,[c.id '_simulation.mat']),'result');r=saved.result;
    valid(end+1)=struct('id',c.id,'y',samples(r.dispatch_trace_v32,25), ...
        'segments',samples(r.segment_trace_v32,50),'time_h',r.dispatch_trace_v32.Time, ...
        'energy_start',reshape(r.energy_start_trace_v32.Data,[],1),'error_message',r.ErrorMessage); %#ok<AGROW>
end
path=fullfile(folder,'mat_audit_v33.json');assert(~isfile(path));
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(struct('valid_cases',valid,'evidence_class','saved_SimulationOutput_read_only_export'),PrettyPrint=true));
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected saved trace dimensions');end
end
