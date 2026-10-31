function export_reporting_v45(folder)
% Reopen saved report and original SimulationOutputs; do not simulate.
s=load(fullfile(folder,'reporting_v45.mat'),'report','spec');items=[];
for j=1:numel(s.report.cases)
    id=s.report.cases(j).id;t=load(fullfile(folder,[id '_simulation.mat']),'result');r=t.result;
    z=struct('id',id,'dispatch',reshape(r.dispatch_trace_v42.Data,25,[])', ...
        'segments',reshape(r.segment_trace_v42.Data,28,64)','error_message',r.ErrorMessage);
    if isempty(items),items=z;else,items(end+1)=z;end %#ok<AGROW>
end
path=fullfile(folder,'mat_reexport_v45.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(struct('report',s.report,'spec',s.spec,'simulation_outputs',items),PrettyPrint=true));
fprintf('MAT_REEXPORT_V45 saved_cases=%d\n',numel(items));
end
