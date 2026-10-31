function export_padding_identity_v51(folder)
% Reopen actual MAT slots; strict identity, memory and clock checks without sim.
s=load(fullfile(folder,'annual_sensitivity_v51.mat'));
for item=s.report.stateflow(:)'
    assert(item.execution_success);r=load(fullfile(folder,[item.id '_simulation.mat']),'result');r=r.result;
    raw=samples(r.segment_trace_v51,1792);plan=samples(r.plan_trace_v51,1408);
    d=samples(r.dispatch_trace_v51,25);starts=samples(r.energy_start_trace_v51,1);
    rows=zeros(size(raw,1),7);hexes=cell(size(raw,1),7);
    for i=1:size(raw,1)
        z=reshape(raw(i,:),28,64)';p=reshape(plan(i,:),22,64)';pad=z(:,2)==0;
        identity=all(z(pad,1)==0)&&all(z(pad,4)==z(pad,5))&&all(z(pad,6:14)==0,'all')&&all(z(pad,17:21)==0,'all');
        energy=all(z(2:end,4)==z(1:end-1,5))&&all(p(:,2)==z(:,4));
        clocks=all(p(pad,15)==z(pad,26))&&all(p(pad,16)==p(pad,18))&&all(p(pad,19)==p(pad,20))&&all(p(pad,21)==p(pad,22))&&all(z(pad,27)==z(pad,28));
        memory=d(i,8)==z(end,5)&&starts(i)==z(1,4);
        if i<size(raw,1),memory=memory&&starts(i+1)==z(end,5);end
        bounds=all(z(:,4)>=0 & z(:,5)>=0 & z(:,4)<=item.p(2) & z(:,5)<=item.p(2));
        rows(i,:)=[i sum(pad) identity energy clocks memory bounds];
        firstPad=find(pad,1);lastPhysical=find(~pad,1,'last');
        assert(~isempty(firstPad));
        v=[z(firstPad,4) z(firstPad,5) max(abs(z(pad,21))) ...
            max(abs(z(pad,[6:14 17:20])),[],'all') max(abs(z(pad,28)-z(pad,27))) ...
            z(lastPhysical,5) d(i,8)];
        hexes(i,:)=cellstr(num2hex(v(:)))';
    end
    t=array2table(rows,'VariableNames',{'Interval','PaddingSlots','Identity','EnergyHandoff','ClockIdentity','MacroMemory','Bounds'});
    for k=1:7
        names={'PaddingStartHex','PaddingEndHex','ResidualMaxHex','ServiceMaxHex','ClockDeltaMaxHex','PhysicalEndHex','MacroEndHex'};
        t.(names{k})=hexes(:,k);
    end
    writetable(t,fullfile(folder,'binary_reopen',[item.id '_padding_identity.csv']));
    assert(all(rows(:,3:7)==1,'all'),'Original-MAT identity audit failed.');
    fprintf('PADDING_IDENTITY_V51 id=%s intervals=%d padding=%d\n',item.id,size(raw,1),sum(rows(:,2)));
end
end
function v=samples(ts,width)
n=numel(ts.Time);v=reshape(ts.Data,width,n)';
end
