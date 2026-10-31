function export_TES_event_mat_audit_v31(folder)
% Independent read-only saved SimulationOutput binding, no rerun or model edits.
snap=fullfile(folder,'mat_audit_source');assert(~isfolder(snap));mkdir(snap);
copyfile([mfilename('fullpath') '.m'],snap);
spec=jsondecode(fileread(fullfile(folder,'source_snapshot','spec','cases.json')));
cases=struct('id',{},'stop_event',{},'error_message',{},'time_h',{},'y',{},'u',{},'energy_start',{},'model_info',{});
for j=1:numel(spec.comparison_cases)
    c=spec.comparison_cases(j);saved=load(fullfile(folder,[c.id '_simulation.mat']),'result');r=saved.result;
    metadata=r.SimulationMetadata;
    cases(end+1)=struct('id',c.id,'stop_event',metadata.ExecutionInfo.StopEvent, ...
        'error_message',r.ErrorMessage,'time_h',r.dispatch_trace_v30.Time, ...
        'y',samples(r.dispatch_trace_v30,17),'u',samples(r.hp_trace_v30,8), ...
        'energy_start',reshape(r.energy_start_trace_v30.Data,[],1),'model_info',metadata.ModelInfo); %#ok<AGROW>
end
path=fullfile(folder,'mat_audit_v31.json');assert(~isfile(path));
report=struct('timestamp_utc',char(datetime('now','TimeZone','UTC')), ...
    'evidence_class','read_only_saved_SimulationOutput_export','cases',cases);
fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw) && isequal(size(raw),[n width]),v=raw;
elseif size(raw,1)==width && numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('DCHR:v31:TraceDimensions','Unexpected saved trace shape.');end
end
