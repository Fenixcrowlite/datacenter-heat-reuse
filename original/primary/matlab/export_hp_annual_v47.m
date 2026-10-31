function export_hp_annual_v47(folder)
% Reopen original MAT files without recomputing dispatch.
s=load(fullfile(folder,'hp_annual_v47.mat'));a=load(fullfile(folder,'annual_v47.mat'));
target=fullfile(folder,'mat_reopen');assert(~isfolder(target));mkdir(target);
writetable(a.out,fullfile(target,'annual_legacy.csv'));writetable(a.audit,fullfile(target,'annual_capability.csv'));
writetable(s.probeTable,fullfile(target,'hp_probes.csv'));
for item=s.report.stateflow(:)'
    t=load(fullfile(folder,[item.id '_simulation.mat']),'result');r=t.result;
    dispatch=samples(r.dispatch_trace_v42,25);raw=samples(r.segment_trace_v42,1792);segments=[];
    for i=1:size(raw,1)
        z=reshape(raw(i,:),28,64)';positive=find(z(:,2)>0);
        segments=[segments;[repmat(i,numel(positive),1) positive z(positive,:)]]; %#ok<AGROW>
    end
    writematrix(dispatch,fullfile(target,[item.id '_dispatch.csv']));writematrix(segments,fullfile(target,[item.id '_segments.csv']));
end
fid=fopen(fullfile(target,'report.json'),'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(s.report,PrettyPrint=true));fprintf('MAT_REOPEN_V47 complete\n');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected saved trace dimensions.');end
end
