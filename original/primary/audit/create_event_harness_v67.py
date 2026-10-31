from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'matlab/run_interval_dispatch_v66.m').read_text()
start=s.index("oldmdl='DCHR_Interval_Dispatch_Stateflow_v65'")
end=s.index('% A single saved chart',start)
s=s[:start]+s[end:]
s=s.replace('run_interval_dispatch_v66','run_event_brackets_v67').replace("mdl='DCHR_Interval_Dispatch_Stateflow_v66'","mdl='DCHR_Event_Brackets_Stateflow_v67'")
s=s.replace('build_interval_dispatch_v66(', 'build_event_brackets_v67(')
s=s.replace('reshape(out.interval_trace_v66.Data,205,[])','reshape(out.interval_trace_v66.Data,250,[])')
s=s.replace("'version','0.66'", "'version','0.67'").replace("'baseline_witness',baseline_witness,",'')
s=s.replace('interval_dispatch_v66.mat','event_brackets_v67.mat').replace('INTERVAL_DISPATCH_V66','EVENT_BRACKETS_V67')
s=s.replace("'scope','CONSERVATIVE_SAMPLED_INTERVAL_SERVICE_WITH_RETAINED_RESTART_PREFIX'", "'scope','EXECUTED_ROOT_OBSERVER_SAMPLED_DISPATCH_UNCHANGED_EARLIEST_SWITCHING_OPEN'")
anchor="[prefix,~]=execute(input(1:2,:),rows(1:2,:));"
extra="""% Actual strict event-ordering rejections in the saved six-mode chart.
for id={'boundary_collision','boundary_delayed'}
    cc=spec.cases(strcmp({spec.cases.id},id{1}));ii=cc.input;ii(end,4)=1;rr=repmat(cc.cfg(:)',size(ii,1),1);
    identifier='';message='';try,execute(ii,rr);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record([id{1} '_strict_rejection'],~isempty(identifier)&&contains(message,'v67 unresolved event ordering'));
    faults{end+1}=struct('id',[id{1} '_strict_rejection'],'identifier',identifier,'message',message, ...
        'expected_guard','v67 unresolved event ordering','input',ii,'cfg_rows',rr);
    if size(ii,1)>1
        [vp,~]=execute(ii(1:2,:),rr(1:2,:));
        ix=find(cellfun(@(r)strcmp(r.id,id{1}),runs));
        record('strict_collision_valid_prefix',isequal(vp,runs{ix}.trace(1:2,:)));
    end
end
% Direct function probes exercise broader boxes and exact algebraic identities.
probes={};
args={
    'wide_charge',[8.5 8.7],[1 1],0,[9.6 9.6],1,2,0,[0 0];
    'wide_cutoff',[6.1 6.3],[-2 -2],0,[5.6 5.6],-1,1,0,[0 0];
    'passive_restart',[8.1 8.3],[0 0],.1,[8 8],-1,1,.25,[.01 .03];
    'dwell_after_horizon',[7.5 7.7],[0 0],.1,[8 8],-1,1,2,[.1 .2];
    'dwell_boundary',[7.5 7.7],[0 0],.1,[8 8],-1,1,1,[0 0];
    'dwell_ready',[7.5 7.7],[0 0],.1,[8 8],-1,1,.25,[.1 .2];
    'threshold_overlap',[7.9 8.1],[0 0],.1,[8 8],-1,1,.25,[0 0];
    'slow_no_crossing',[8.5 8.7],[1 1],.01,[9.6 9.6],1,.1,0,[0 0];
    'lossy_charge',[8.5 8.7],[1 1],.01,[9.6 9.6],1,2,0,[0 0];
    'lossy_cutoff',[6.1 6.3],[-2 -2],.01,[5.6 5.6],-1,1,0,[0 0]};
for j=1:size(args,1)
    v=certify_event_root_v67(args{j,2:end});
    probes{end+1}=struct('id',args{j,1},'E',args{j,2},'B',args{j,3},'lambda',args{j,4},'target',args{j,5}, ...
        'direction',args{j,6},'horizon',args{j,7},'dwell',args{j,8},'age',args{j,9},'output',v');
    record([args{j,1} '_finite_certificate'],all(isfinite(v)));
end
"""
assert anchor in s;s=s.replace(anchor,extra+'\n'+anchor)
s=s.replace("'faults',{faults},'valid_prefix'", "'faults',{faults},'root_probes',{probes},'valid_prefix'")
with (ROOT/'matlab/run_event_brackets_v67.m').open('x',encoding='utf-8') as f:f.write(s)
s=(ROOT/'audit/run_interval_dispatch_v66.ps1').read_text().replace('run_interval_dispatch_v66','run_event_brackets_v67')
with (ROOT/'audit/run_event_brackets_v67.ps1').open('x',encoding='utf-8') as f:f.write(s)
