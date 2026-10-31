function export_annual_dispatch_v48(folder)
% Reopen original MAT evidence without recomputing simulation.
s=load(fullfile(folder,'annual_dispatch_v48.mat'));target=fullfile(folder,'mat_reopen');
assert(~isfolder(target));mkdir(target);
items=[{s.report.annual.id} {s.report.fixtures.id}];
for j=1:numel(items)
    a=load(fullfile(folder,[items{j} '.mat']));
    writetable(a.out,fullfile(target,[items{j} '.csv']));writetable(a.legacy,fullfile(target,[items{j} '_legacy.csv']));
    if isfield(a,'ports'),writetable(a.ports,fullfile(target,[items{j} '_ports.csv']));end
end
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
fprintf(fid,'%s\n',jsonencode(s.report,PrettyPrint=true));fprintf('MAT_REOPEN_V48 complete\n');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected saved trace dimensions.');end
end
