function export_endpoint_protocol_exact_v52(folder)
% Reopen accepted SimulationOutputs; export exact positive-span state protocol.
report=load(fullfile(folder,'annual_sensitivity_v52.mat'));
target=fullfile(folder,'endpoint_binary');assert(~isfolder(target));mkdir(target);
for item=report.report.stateflow(:)'
    assert(item.execution_success);
    saved=load(fullfile(folder,[item.id '_simulation.mat']),'result');r=saved.result;
    raw=samples(r.segment_trace_v52,1792);plan=samples(r.plan_trace_v52,1472);
    fid=fopen(fullfile(target,[item.id '.csv']),'w');assert(fid>0);
    cleanup=onCleanup(@()fclose(fid));
    fprintf(fid,'Interval,Slot,Kind,StartHex,EndHex,TargetHex,ChargeHex,DischargeHex,SpanHex,StandingHex,ResidualHex\n');
    for i=1:size(raw,1)
        z=reshape(raw(i,:),28,64)';s=reshape(plan(i,:),23,64)';
        assert(all(s(:,23)==z(:,5)) && all(s(:,2)==z(:,4)));
        assert(all(z(2:end,4)==z(1:end-1,5)));
        for k=find(z(:,2)>0)'
            fprintf(fid,'%d,%d,%d',i,k,z(k,24));
            values=[z(k,4:5) s(k,23) z(k,7:8) z(k,2) z(k,17) z(k,21)];
            for v=values,fprintf(fid,',%s',num2hex(v));end
            fprintf(fid,'\n');
        end
    end
    clear cleanup;
    fprintf('ENDPOINT_BINARY_V52 id=%s intervals=%d\n',item.id,size(raw,1));
end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;
if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';
else,error('Unexpected original-MAT trace dimensions.');end
end
