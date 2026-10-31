function export_stateflow_admissibility_v36(folder)
% Read-only MAT export in a separate MATLAB batch for independent artifact QA.
paths=dir(fullfile(folder,'*_simulation.mat'));items=struct('file',{},'error_message',{},'phase',{},'time_h',{}, ...
    'dispatch',{},'plan',{},'segments',{},'clock_start',{},'clock_end',{},'energy_start',{},'sample_time_h',{});
for k=1:numel(paths)
    saved=load(fullfile(folder,paths(k).name));
    if isfield(saved,'result'),r=saved.result;else,r=saved.baseline;end
    phase='';time=[];d=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;
    if ~isempty(d),phase=d.SimulationPhase;time=d.SimulationTime;end
    item=struct('file',paths(k).name,'error_message',r.ErrorMessage,'phase',phase,'time_h',time, ...
        'dispatch',[],'plan',[],'segments',[],'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[]);
    if isempty(r.ErrorMessage)
        item.plan=samples(r.plan_trace_v36,1152);item.dispatch=samples(r.dispatch_trace_v36,25);item.segments=samples(r.segment_trace_v36,1792);
        item.clock_start=samples(r.clock_start_trace_v36,2);item.clock_end=samples(r.clock_end_trace_v36,2);
        item.energy_start=samples(r.energy_start_trace_v36,1);item.sample_time_h=r.dispatch_trace_v36.Time;
    end
    items(end+1)=item; %#ok<AGROW>
end
path=fullfile(folder,'mat_audit_v36.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true)); %#ok<NASGU>
fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
legacy=struct('file',{},'dispatch',{},'sample_time_h',{},'error_message',{});
paths=dir(fullfile(folder,'*_v32_comparison.mat'));
for k=1:numel(paths)
    saved=load(fullfile(folder,paths(k).name),'oldresult');r=saved.oldresult;
    legacy(end+1)=struct('file',paths(k).name,'dispatch',samples(r.dispatch_trace_v32,25), ...
        'sample_time_h',r.dispatch_trace_v32.Time,'error_message',r.ErrorMessage); %#ok<AGROW>
end
fid2=fopen(fullfile(folder,'legacy_mat_audit_v36.json'),'w');assert(fid2>0);
cleanup2=onCleanup(@()fclose(fid2));fprintf(fid2,'%s\n',jsonencode(legacy,PrettyPrint=true)); %#ok<NASGU>
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected saved trace dimensions.');end
end
