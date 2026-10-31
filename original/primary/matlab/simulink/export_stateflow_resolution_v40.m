function export_stateflow_resolution_v40(folder)
% Separate read-only batch: export preserved SimulationOutput clocks/dispatch.
paths=dir(fullfile(folder,'*_simulation.mat'));
items=struct('id',{},'rejected',{},'error_message',{},'phase',{},'time_h',{},'dispatch',{},'clock_start',{},'clock_end',{},'energy_start',{},'sample_time_h',{},'segments',{});
for k=1:numel(paths)
    saved=load(fullfile(folder,paths(k).name));if isfield(saved,'result'),r=saved.result;else,r=saved.baseline;end
    id=erase(paths(k).name,'_simulation.mat');d=r.SimulationMetadata.ExecutionInfo.ErrorDiagnostic;phase='';time=[];
    if ~isempty(d),phase=d.SimulationPhase;time=d.SimulationTime;end
    item=struct('id',id,'rejected',~isempty(r.ErrorMessage),'error_message',r.ErrorMessage,'phase',phase,'time_h',time, ...
        'dispatch',[],'clock_start',[],'clock_end',[],'energy_start',[],'sample_time_h',[],'segments',[]);
    if isempty(r.ErrorMessage)
        item.dispatch=samples(r.dispatch_trace_v40,25);item.clock_start=samples(r.clock_start_trace_v40,4);
        item.clock_end=samples(r.clock_end_trace_v40,4);item.energy_start=samples(r.energy_start_trace_v40,1);
        item.sample_time_h=r.dispatch_trace_v40.Time;
        raw=samples(r.segment_trace_v40,1792);plan=samples(r.plan_trace_v40,1408);
        for i=1:size(raw,1)
            z=reshape(raw(i,:),28,64)';s=reshape(plan(i,:),22,64)';
            for j=1:64
                if z(j,2)>0,item.segments(end+1,:)=[i-1 j z(j,:) s(j,:)];end %#ok<AGROW>
            end
        end
    end
    items(end+1)=item; %#ok<AGROW>
end
saved=load(fullfile(folder,'hp_components.mat'),'probes');
v=struct('simulations',items,'component_probes',saved.probes);
path=fullfile(folder,'mat_audit_v40.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true)); %#ok<NASGU>
fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected saved trace dimensions.');end
end
