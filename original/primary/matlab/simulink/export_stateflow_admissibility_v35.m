function export_stateflow_admissibility_v35(folder)
% Read-only MAT export in a separate MATLAB batch for independent artifact QA.
paths=dir(fullfile(folder,'*_simulation.mat'));items=struct('file',{},'error_message',{},'phase',{},'time_h',{}, ...
    'dispatch',{},'segments',{},'clock_start',{},'clock_end',{},'energy_start',{},'sample_time_h',{});
for k=1:numel(paths)
    saved=load(fullfile(folder,paths(k).name),'result');r=saved.result;
    phase='';time=[];d=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;
    if ~isempty(d),phase=d.SimulationPhase;time=d.SimulationTime;end
    item=struct('file',paths(k).name,'error_message',r.ErrorMessage,'phase',phase,'time_h',time, ...
        'dispatch',[],'segments',[],'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[]);
    if isempty(r.ErrorMessage)
        item.dispatch=samples(r.dispatch_trace_v34,25);item.segments=samples(r.segment_trace_v34,1792);
        item.clock_start=samples(r.clock_start_trace_v34,2);item.clock_end=samples(r.clock_end_trace_v34,2);
        item.energy_start=samples(r.energy_start_trace_v34,1);item.sample_time_h=r.dispatch_trace_v34.Time;
    end
    items(end+1)=item; %#ok<AGROW>
end
path=fullfile(folder,'mat_audit_v35.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true)); %#ok<NASGU>
fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected saved trace dimensions.');end
end
