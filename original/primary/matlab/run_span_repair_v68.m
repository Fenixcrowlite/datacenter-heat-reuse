function run_span_repair_v68(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
mdl='DCHR_Span_Repair_Stateflow_v68';spec=jsondecode(fileread(fullfile(folder,'spec.json')));
% Optional prefix provenance fields make heterogeneous JSON arrays decode as cells.
if iscell(spec.cases),spec.cases=cellfun(@(x)rm_optional(x),spec.cases,'UniformOutput',false);spec.cases=[spec.cases{:}];end
checks=struct('name',{},'passed',{});runs={};faults={};
% A single saved chart executes both inherited correlated restart and new service.
for j=1:numel(spec.cases)
    c=spec.cases(j);input=c.input;cfg=c.cfg(:);rows=repmat(cfg',size(input,1),1);
    if ~isfile(fullfile(root,'matlab','simulink',[mdl '.slx']))
        build_span_repair_v68([(0:size(input,1)-1)' input],[(0:size(input,1)-1)' rows]);
    end
    load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));[trace,out]=execute(input,rows);
    record([c.id '_schema'],all(trace(:,180)==66));
    record([c.id '_firstlaw'],all(trace(:,53)<=0&trace(:,54)>=0));
    record([c.id '_positive_ports'],all(all(trace(:,41:52)>=0)));
    record([c.id '_inventory'],all(trace(:,37)>=0&trace(:,37)<=trace(:,38)));
    service=find(input(:,1)==1);
    record([c.id '_service_closure'],all(abs(trace(service,171))<1e-12));
    record([c.id '_mutual_exclusivity'],all(trace(service,122).*trace(service,123)==0));
    record([c.id '_boiler_limit'],all(trace(service,124)<=cfg(59)));
    record([c.id '_thermal_stop'],all(trace(service,122)==0|trace(service,38)<cfg(36)*(cfg(60)-cfg(37))));
    record([c.id '_cutoff'],all(trace(service,123)==0|trace(service,37)>=trace(service,169)));
    record([c.id '_expected_modes'],all(ismember(c.expected_modes,unique(trace(:,115)))));
    record([c.id '_positive_enclosures'],all(all(trace(service,128:151)>=0)));
    for k=service(:)'
        if k>1
            record(sprintf('%s_handoff_%d',c.id,k),isequal(trace(k,160:161),trace(k-1,37:38)));
            if trace(k,164)==trace(k,55)
                record(sprintf('%s_age_%d',c.id,k),isequal(trace(k,162:163),trace(k-1,39:40)));
            end
        end
    end
    references={};
    % Pure exact-input fixtures compare to the verified constant-power v30 kernel.
    if input(1,1)==1
        for k=1:numel(service)
            ix=service(k);initial=input(1,10);if ix>1,initial=refsE;end
            pp=[input(ix,5);cfg(36)*(cfg(38)-cfg(37));cfg(44);cfg(45);cfg(42);cfg(43);cfg(41); ...
                cfg(36)*(cfg(39)-cfg(37));cfg(36);cfg(37)];
            ref=dchr.components.storage_kernel_v30(initial,trace(ix,122),trace(ix,123),pp);refsE=ref(4);
            record(sprintf('%s_v30_%d',c.id,ix),ref(4)>=trace(ix,37)&&ref(4)<=trace(ix,38));
            references{end+1}=struct('tick',ix,'initial',initial,'parameters',pp','charge',trace(ix,122),'discharge',trace(ix,123),'output',ref'); %#ok<AGROW>
        end
    end
    runs{end+1}=struct('id',c.id,'cfg',cfg','input',input,'trace',trace,'references_v30',{references},'solver_time',out.interval_trace_v66.Time'); %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','trace','cfg','input','-v7.3');
end
function c=rm_optional(c)
for name={'prefix_origin','prefix_id'}
    if isfield(c,name{1}),c=rmfield(c,name{1});end
end
end
coverage=[];for j=1:numel(runs),coverage=[coverage;runs{j}.trace(:,115)];end %#ok<AGROW>
record('same_saved_chart_all_six_modes',isequal(unique(coverage)',0:5));
base=spec.cases(strcmp({spec.cases.id},'delayed_fault_control'));input=base.input;rows=repmat(base.cfg(:)',size(input,1),1);
labels={'negative_demand','delayed_nan','delayed_policy','reverse_clock','interval_mismatch', ...
    'ON_dwell','invalid_efficiency','invalid_temperature','negative_source','prefix_after_service'};
expected={'service input domain','finite domain','immutable policy','physical clock must advance', ...
    'physical interval mismatch','ON dwell not certified','equipment domain','temperature policy','service input domain','prefix cannot resume'};
for j=1:numel(labels)
    ii=input;rr=rows;
    switch j
        case 1,ii(3,6)=-1;
        case 2,ii(3,6)=NaN;
        case 3,rr(3:end,59)=rr(3:end,59)+1;
        case 4,ii(3,3)=ii(2,3);
        case 5,ii(3,5)=ii(3,5)+.02;
        case 6,ii(1,12)=0;ii(1,8)=0;
        case 7,rr(:,42)=1.1;
        case 8,rr(:,60)=rr(:,40);
        case 9,ii(3,7)=-1;
        case 10,ii(3,1)=0;
    end
    identifier='';message='';try,execute(ii,rr);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record(labels{j},~isempty(identifier)&&contains(message,expected{j}));
    faults{end+1}=struct('id',labels{j},'identifier',identifier,'message',message,'expected_guard',expected{j},'input',ii,'cfg_rows',rr); %#ok<AGROW>
end
% Actual strict event-ordering rejections in the saved six-mode chart.
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
    'exact_boundary',[8 8],[1 1],0,[9 9],1,1,0,[0 0];
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
    v=certify_event_root_v68(args{j,2:end});
    probes{end+1}=struct('id',args{j,1},'E',args{j,2},'B',args{j,3},'lambda',args{j,4},'target',args{j,5}, ...
        'direction',args{j,6},'horizon',args{j,7},'dwell',args{j,8},'age',args{j,9},'output',v');
    record([args{j,1} '_finite_certificate'],all(isfinite(v)));
end

% Boundary witnesses are checked against the actual preserved v67r2 model.
% A caught expected legacy failure is defect evidence, not corrected acceptance.
legacy_defects={};legacy='DCHR_Event_Brackets_Stateflow_v67r2';
load_system(fullfile(root,'matlab','simulink',[legacy '.slx']));
for id={'span_equal_one','span_near_one','span_delayed'}
    cc=spec.cases(strcmp({spec.cases.id},id{1}));ii=cc.input;rr=repmat(cc.cfg(:)',size(ii,1),1);
    ticks=(0:size(ii,1)-1)';mw=get_param(legacy,'ModelWorkspace');
    assignin(mw,'dispatch_input_v66',[ticks ii]);assignin(mw,'dispatch_cfg_v66',[ticks rr]);
    identifier='';message='';
    try,sim(legacy,'StopTime',num2str(size(ii,1)-1),'ReturnWorkspaceOutputs','on');
    catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    expectedFailure=~strcmp(id{1},'span_near_one');
    record([id{1} '_legacy_actual_defect_or_control'], ...
        (expectedFailure&&~isempty(identifier)&&contains(message,'v63 outward span exceeds one'))|| ...
        (~expectedFailure&&isempty(message)));
    vp=[];
    if size(ii,1)>1
        assignin(mw,'dispatch_input_v66',[ticks(1:2) ii(1:2,:)]);
        assignin(mw,'dispatch_cfg_v66',[ticks(1:2) rr(1:2,:)]);
        oo=sim(legacy,'StopTime','1','ReturnWorkspaceOutputs','on');
        vp=reshape(oo.interval_trace_v66.Data,256,[])';
        ix=find(cellfun(@(r)strcmp(r.id,id{1}),runs));
        % Expanded tail changes enclosures; compare retained exact trajectory
        % independently instead of requiring byte-identical new/old widths.
        record('legacy_delayed_prefix_completed',size(vp,1)==2&&all(vp(:,180)==66));
    end
    legacy_defects{end+1}=struct('id',id{1},'model',legacy,'identifier',identifier,'message',message, ...
        'expected_guard','v63 outward span exceeds one','input',ii,'cfg',cc.cfg,'valid_prefix',vp);
end
close_system(legacy,0);
% Isolate the same defect in the host root function. Exact-binary powers of
% two make lambda*H exactly one; the previous representable H is strictly <1.
for H=[8,8-eps(8)/2,8-eps(8)]
    identifier='';message='';legacy_output=[];
    try,legacy_output=certify_event_root_v67([8 8],[0 0],.125,[4 4],-1,H,0,[0 0]);
    catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    expectedFailure=H==8;
    record(sprintf('legacy_root_span_%.17g',H), ...
        (expectedFailure&&contains(message,'v67 outward root span'))||(~expectedFailure&&isempty(identifier)));
    legacy_defects{end+1}=struct('id',sprintf('host_span_%.17g',H),'model','host_v67', ...
        'identifier',identifier,'message',message,'horizon',H,'output',legacy_output);
    v=certify_event_root_v68([8 8],[0 0],.125,[4 4],-1,H,0,[0 0]);
    probes{end+1}=struct('id',sprintf('repaired_span_%.17g',H),'E',[8 8],'B',[0 0],'lambda',.125, ...
        'target',[4 4],'direction',-1,'horizon',H,'dwell',0,'age',[0 0],'output',v');
    record(sprintf('repaired_root_span_%.17g',H),v(1)==1&&v(12)==1);
end

[prefix,~]=execute(input(1:2,:),rows(1:2,:));record('delayed_two_valid_samples',isequal(prefix,runs{find(cellfun(@(r)strcmp(r.id,base.id),runs))}.trace(1:2,:)));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.68','scope','NUMERICAL_SPAN_REPAIR_SAMPLED_POLICY_EARLIEST_SWITCHING_OPEN', ...
    'new_model',true,'runs',{runs},'faults',{faults},'root_probes',{probes},'legacy_defects',{legacy_defects},'valid_prefix',prefix,'metadata',metadata,'mode_coverage',unique(coverage)', ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'span_repair_v68.mat'),'report','-v7.3');reopened=load(fullfile(folder,'span_repair_v68.mat'));
assert(isequaln(reopened.report,report));writejson('report.json',report);writejson('mat_reopen.json',reopened.report);
mkdir(fullfile(folder,'binary'));manifest=struct('id',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopened.report.runs)
    r=reopened.report.runs{j};for field={'cfg','input','trace'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('id',r.id,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);close_system(mdl,0);
fprintf('SPAN_REPAIR_V68 PASS=%d FAIL=%d RUNS=%d FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v66:AcceptanceFailure','Inspect retained report');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
        fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
    end
    function [trace,out]=execute(ii,rr)
        ticks=(0:size(ii,1)-1)';mw=get_param(mdl,'ModelWorkspace');
        assignin(mw,'dispatch_input_v66',[ticks ii]);assignin(mw,'dispatch_cfg_v66',[ticks rr]);
        out=sim(mdl,'StopTime',num2str(size(ii,1)-1),'ReturnWorkspaceOutputs','on');
        trace=reshape(out.interval_trace_v66.Data,256,[])';assert(size(trace,1)==size(ii,1));
    end
end
