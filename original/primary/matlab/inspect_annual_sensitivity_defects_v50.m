function inspect_annual_sensitivity_defects_v50(folder)
% Reopen failed actual executions; retain prefix and isolated padding witnesses.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);s=load(fullfile(folder,'annual_sensitivity_v50.mat'));
target=fullfile(folder,'defect_evidence');assert(~isfolder(target));mkdir(target);
items=[];
for item=s.report.stateflow(:)'
    if item.execution_success,continue;end
    z=load(fullfile(folder,[item.id '_simulation.mat']),'result');r=z.result;
    a=load(fullfile(folder,[item.id '_adapter.mat']));a=a.a;
    dispatch=samples(r.dispatch_trace_v42,25);raw=samples(r.segment_trace_v42,1792);
    starts=samples(r.clock_start_trace_v42,4);ends=samples(r.clock_end_trace_v42,4);
    n=size(dispatch,1);nr=size(raw,1);
    writematrix(dispatch,fullfile(target,[item.id '_prefix_dispatch.csv']));
    writematrix(raw,fullfile(target,[item.id '_prefix_raw.csv']));
    writematrix(starts,fullfile(target,[item.id '_prefix_clock_start.csv']));
    writematrix(ends,fullfile(target,[item.id '_prefix_clock_end.csv']));
    % Examine last retained segment batch and first uncommitted input separately.
    bad=[];
    for i=max(1,nr-1):nr
        seg=reshape(raw(i,:),28,64)';
        for k=1:64
            v=seg(k,:);
            if v(2)==0&&(v(1)~=0||any(v(6:14)~=0)||any(v(17:21)~=0)||v(5)~=v(4))
                bad=[bad;[i k v]]; %#ok<AGROW>
            end
        end
    end
    writematrix(bad,fullfile(target,[item.id '_retained_padding_violations.csv']));
    candidate=[];probes=[];
    for interval=max(1,n):min(n+2,size(a.inputs,1))
        if interval==1,E=a.initial_energy_MWh;m=a.initial_clock;
        else,E=dispatch(min(interval-1,n),8);m=ends(min(interval-1,size(ends,1)),:)';end
        plan=dchr_segment_plan_v42(a.inputs(interval,:),E,a.p,a.h,a.p(1),m,a.c);
        rows=[];
        for k=1:64
            pp=plan(:,k);clock=[pp(15);pp(18);pp(20);pp(22)];
            mode=stateflow_choose_mode_v42(pp,a.p);v=stateflow_allocate_v42(mode,pp,a.p,clock);
            if pp(1)==0
                predicate=v(1)==0&&all(v(6:14)==0)&&all(v(17:21)==0)&&v(5)==v(4);
                rows=[rows;[interval k double(predicate) pp' v']]; %#ok<AGROW>
            end
        end
        writematrix(rows,fullfile(target,sprintf('%s_interval_%d_padding_probes.csv',item.id,interval)));
        probe=struct('interval',interval,'input',a.inputs(interval,:),'initial_energy_MWh',E, ...
            'initial_clock',m,'zero_slots',size(rows,1),'failed_padding_predicates',sum(rows(:,3)==0));
        if isempty(probes),probes=probe;else,probes(end+1)=probe;end %#ok<AGROW>
        if isempty(candidate)&&probe.failed_padding_predicates>0,candidate=probe;end
    end
    entry=struct('id',item.id,'original_error_message',r.ErrorMessage,'retained_dispatch_samples',n, ...
        'retained_segment_samples',nr,'retained_start_clock_samples',size(starts,1), ...
        'retained_end_clock_samples',size(ends,1),'dispatch_time_h',r.dispatch_trace_v42.Time', ...
        'segment_time_h',r.segment_trace_v42.Time','retained_padding_violations',size(bad,1), ...
        'probes',probes,'candidate',candidate);
    if isempty(items),items=entry;else,items(end+1)=entry;end %#ok<AGROW>
    fprintf('DEFECT_V50 id=%s retained=%d raw=%d padding_violations=%d probe_failures=%d\n', ...
        item.id,n,nr,size(bad,1),sum([probes.failed_padding_predicates]));
end
save(fullfile(target,'defects_v50.mat'),'items');
fid=fopen(fullfile(target,'defects_v50.json'),'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(items,PrettyPrint=true));fprintf('DEFECT_INSPECTION_V50 complete\n');
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if n==0,v=zeros(0,width);
elseif ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected failed trace dimensions.');end
end
