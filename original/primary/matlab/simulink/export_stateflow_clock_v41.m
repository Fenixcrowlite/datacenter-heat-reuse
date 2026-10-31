function export_stateflow_clock_v41(folder)
% Separate read-only MATLAB process: bind JSON evidence to saved MAT outputs.
paths=dir(fullfile(folder,'*_simulation.mat'));items=[];
for k=1:numel(paths)
    saved=load(fullfile(folder,paths(k).name),'result');r=saved.result;
    item=struct('id',erase(paths(k).name,'_simulation.mat'),'rejected',~isempty(r.ErrorMessage), ...
        'error_message',r.ErrorMessage,'dispatch',[],'clock_start',[],'clock_end',[], ...
        'energy_start',[],'sample_time_h',[],'segments',[]);
    if ~item.rejected
        item.dispatch=unpack(r.dispatch_trace_v40,25);item.clock_start=unpack(r.clock_start_trace_v40,4);
        item.clock_end=unpack(r.clock_end_trace_v40,4);item.energy_start=unpack(r.energy_start_trace_v40,1);
        item.sample_time_h=r.dispatch_trace_v40.Time;
        raw=unpack(r.segment_trace_v40,1792);plan=unpack(r.plan_trace_v40,1408);
        for i=1:size(raw,1)
            segments=reshape(raw(i,:),28,64)';schedule=reshape(plan(i,:),22,64)';
            positive=find(segments(:,2)>0);
            for j=positive'
                item.segments(end+1,:)=[i-1 j segments(j,:) schedule(j,:)]; %#ok<AGROW>
            end
        end
    end
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
end
path=fullfile(folder,'mat_audit_v41.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid));fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true)); %#ok<NASGU>
fprintf('MAT_AUDIT_OUTPUT=%s\n',path);
end
function v=unpack(ts,width)
v=reshape(ts.Data,width,numel(ts.Time))';
if ismatrix(ts.Data) && isequal(size(ts.Data),[numel(ts.Time),width]),v=ts.Data;end
end
