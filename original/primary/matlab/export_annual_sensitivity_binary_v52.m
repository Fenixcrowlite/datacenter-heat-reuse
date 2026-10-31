function export_annual_sensitivity_binary_v52(folder)
% Exact binary physical spans/clocks from original MATs, without resimulation.
s=load(fullfile(folder,'annual_sensitivity_v52.mat'));target=fullfile(folder,'binary_reopen');
assert(~isfolder(target));mkdir(target);
for item=s.report.stateflow(:)'
    if ~item.execution_success,continue;end
    z=load(fullfile(folder,[item.id '_simulation.mat']),'result');r=z.result;
    raw=samples(r.segment_trace_v52,1792);starts=samples(r.clock_start_trace_v52,4);ends=samples(r.clock_end_trace_v52,4);
    fid=fopen(fullfile(target,[item.id '_spans_hex.csv']),'w');assert(fid>0);
    for i=1:size(raw,1)
        seg=reshape(raw(i,:),28,64)';
        for k=find(seg(:,2)>0)'
            fprintf(fid,'%d,%d,%s\n',i,k,num2hex(seg(k,2)));
        end
    end
    fclose(fid);
    fid=fopen(fullfile(target,[item.id '_clocks_hex.csv']),'w');assert(fid>0);
    for i=1:size(starts,1)
        fprintf(fid,'%d',i);v=[starts(i,:) ends(i,:)];
        for k=1:8,fprintf(fid,',%s',num2hex(v(k)));end
        fprintf(fid,'\n');
    end
    fclose(fid);
    fprintf('BINARY_REOPEN_V52 id=%s intervals=%d\n',item.id,size(raw,1));
end
fprintf('BINARY_REOPEN_V52 complete\n');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected original trace dimensions.');end
end
