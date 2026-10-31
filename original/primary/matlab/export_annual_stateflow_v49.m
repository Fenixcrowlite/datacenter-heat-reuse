function export_annual_stateflow_v49(folder)
% Independently reopen stored SimulationOutputs and original MAT objects.
s=load(fullfile(folder,'annual_stateflow_v49.mat'));target=fullfile(folder,'mat_reopen');
assert(~isfolder(target));mkdir(target);
a=load(fullfile(folder,'adapter_v49.mat'));
writematrix(a.a.inputs,fullfile(target,'annual_inputs.csv'));
writetable(a.a.preflight,fullfile(target,'fixed_preflight.csv'));
writetable(a.unsupported.preflight,fullfile(target,'scheduled_preflight.csv'));
for item=s.report.stateflow(:)'
    z=load(fullfile(folder,[item.id '_simulation.mat']),'result');r=z.result;
    dispatch=samples(r.dispatch_trace_v42,25);raw=samples(r.segment_trace_v42,1792);chunks=cell(size(raw,1),1);
    for i=1:size(raw,1)
        seg=reshape(raw(i,:),28,64)';pos=find(seg(:,2)>0);chunks{i}=[repmat(i,numel(pos),1) pos seg(pos,:)];
    end
    writematrix(dispatch,fullfile(target,[item.id '_dispatch.csv']));
    writematrix(vertcat(chunks{:}),fullfile(target,[item.id '_segments.csv']));
    writematrix(samples(r.clock_start_trace_v42,4),fullfile(target,[item.id '_clock_start.csv']));
    writematrix(samples(r.clock_end_trace_v42,4),fullfile(target,[item.id '_clock_end.csv']));
    ports=array2table(dispatch(:,[18 2 3 4 5 6 19 20]),'VariableNames',s.spec.port_columns);
    ports=dchr.adapt_dispatch_energy_v46(ports,'explicit_actual_v45');
    writetable(ports,fullfile(target,[item.id '_ports.csv']));
end
p=load(fullfile(folder,'paired_loss_first_v48.mat'));
writetable(p.paired,fullfile(target,'paired_loss_first_v48.csv'));writetable(p.pairedPorts,fullfile(target,'paired_loss_first_ports.csv'));
fid=fopen(fullfile(target,'report.json'),'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(s.report,PrettyPrint=true));fprintf('MAT_REOPEN_V49 complete\n');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected saved trace dimensions.');end
end
