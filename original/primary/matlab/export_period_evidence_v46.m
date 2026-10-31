function export_period_evidence_v46(folder)
% Reopen saved original MATs; no simulation or production-report recomputation.
s=load(fullfile(folder,'period_v46.mat'),'report','spec');items=[];
stamp=char(datetime('now','TimeZone','UTC','Format','yyyyMMdd''T''HHmmssSSS''Z'''));
target=fullfile(folder,['mat_reopen_v46_' stamp]);assert(~isfolder(target));mkdir(target);
copyfile([mfilename('fullpath') '.m'],target);
for j=1:numel(s.report.stateflow)
    id=s.report.stateflow(j).id;t=load(fullfile(folder,[id '_simulation.mat']),'result');r=t.result;
    dispatch=samples(r.dispatch_trace_v42,25);raw=samples(r.segment_trace_v42,1792);segments=[];
    for i=1:size(raw,1)
        z=reshape(raw(i,:),28,64)';positive=find(z(:,2)>0);
        segments=[segments;[repmat(i,numel(positive),1) positive z(positive,:)]]; %#ok<AGROW>
    end
    writematrix(dispatch,fullfile(target,[id '_mat_dispatch.csv']));writematrix(segments,fullfile(target,[id '_mat_segments.csv']));
    z=struct('id',id,'error_message',r.ErrorMessage,'sample_time_h',r.dispatch_trace_v42.Time);
    if isempty(items),items=z;else,items(end+1)=z;end %#ok<AGROW>
end
annual=[];
for j=1:numel(s.report.annual)
    id=s.report.annual(j).id;t=load(fullfile(folder,[id '_reference.mat']),'out','ports','cfg','m','old');
    writetable(t.ports,fullfile(target,[id '_mat_ports.csv']));writetable(t.out,fullfile(target,[id '_mat_legacy.csv']));
    z=struct('id',id,'report',t.m,'legacy_report',t.old,'dt_h',t.cfg.sim.dt_h);
    if isempty(annual),annual=z;else,annual(end+1)=z;end %#ok<AGROW>
end
path=fullfile(target,'mat_reexport_v46.json');assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(struct('report',s.report,'stateflow',items,'annual',annual),PrettyPrint=true));
fprintf('MAT_REEXPORT_V46 stateflow=%d annual=%d\n',numel(items),numel(annual));
fprintf('MAT_REOPEN_FOLDER=%s\n',target);
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected saved trace dimensions.');end
end
