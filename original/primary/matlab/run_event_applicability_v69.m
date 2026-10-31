function run_event_applicability_v69(folder)
% Execute preserved v68, not a compile-only or repaired-controller claim.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));mdl='DCHR_Span_Repair_Stateflow_v68';
load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
checks=struct('name',{},'passed',{});runs={};faults={};probes={};coverage=[];
for j=1:numel(spec.cases)
    c=spec.cases(j);cfg=c.cfg(:);input=c.input;[trace,out]=execute(input,cfg);
    record([c.id '_schema'],all(trace(:,180)==66));
    record([c.id '_mode'],all(ismember(c.expected_modes,unique(trace(:,115)))));
    record([c.id '_balance'],all(trace(:,53)<=0&trace(:,54)>=0));
    record([c.id '_bounds'],all(trace(:,37)>=0&trace(:,37)<=trace(:,38)));
    record([c.id '_TES_exclusive'],all(trace(:,122).*trace(:,123)==0));
    record([c.id '_service'],all(abs(trace(:,171))<=1e-12));
    record([c.id '_boiler'],all(trace(:,124)<=cfg(59)));
    references={};refsE=input(1,10);
    for k=1:size(input,1)
        z=event_observer_v68(input(k,:)',cfg,trace(k,1:205)');
        record(sprintf('%s_compiled_host_%d',c.id,k),isequal(z',trace(k,206:256)));
        pp=[input(k,5);cfg(36)*(cfg(38)-cfg(37));cfg(44);cfg(45);cfg(42);cfg(43);cfg(41);cfg(36)*(cfg(39)-cfg(37));cfg(36);cfg(37)];
        ref=dchr.components.storage_kernel_v30(refsE,trace(k,122),trace(k,123),pp);
        record(sprintf('%s_v30_%d',c.id,k),ref(4)>=trace(k,37)&&ref(4)<=trace(k,38));
        references{end+1}=struct('initial',refsE,'parameters',pp','output',ref');refsE=ref(4); %#ok<AGROW>
    end
    if strcmp(c.audit_kind,'inactive_cutoff')&&contains(c.id,'contact')
        record([c.id '_inactive_collision'],trace(end,221)==2&&trace(end,247)==0&&all(trace(:,123)==0)&&all(trace(:,121)==1));
    elseif strcmp(c.audit_kind,'inactive_stop')
        record([c.id '_nonactionable_root'],trace(end,206)==1&&trace(end,217)==1&&trace(end,55)==0&&trace(end,122)==0&&trace(end,40)<cfg(58));
    elseif strcmp(c.audit_kind,'missing_forced_restart')
        record([c.id '_restart_missing'],trace(end,236)==0&&trace(end,55)==0&&trace(end,123)==.5&&trace(end,38)<trace(end,170));
        E=trace(1,160:161);b=-input(1,6)/cfg(43);B=[b-2*eps(b) b+2*eps(b)];
        target=cfg(36)*(cfg(40)-cfg(37));target=[target-2*eps(target) target+2*eps(target)];
        args={E,B,cfg(41),target,-1,input(1,5),cfg(58),trace(1,162:163)};
        z=certify_event_root_v68(args{:});record([c.id '_forced_root_certified'],z(1)==1&&z(12)==1);
        probes{end+1}=struct('id',c.id,'E',E,'B',B,'lambda',cfg(41),'target',target,'direction',-1,'horizon',input(1,5),'dwell',cfg(58),'age',trace(1,162:163),'output',z'); %#ok<AGROW>
    end
    runs{end+1}=struct('id',c.id,'audit_kind',c.audit_kind,'cfg',cfg','input',input,'trace',trace,'references_v30',{references},'solver_time',out.interval_trace_v66.Time'); %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','trace','cfg','input','-v7.3');coverage=[coverage;trace(:,115)]; %#ok<AGROW>
end
for j=1:numel(spec.faults)
    f=spec.faults(j);identifier='';message='';
    try,execute(f.input,f.cfg(:));catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record([f.id '_rejection'],~isempty(identifier)&&contains(message,f.expected_guard));prefix=[];
    if size(f.input,1)>1
        [prefix,~]=execute(f.input(1:end-1,:),f.cfg(:));ix=find(cellfun(@(r)strcmp(r.id,f.base_id),runs));
        record([f.id '_valid_prefix'],isequal(prefix,runs{ix}.trace(1:end-1,:)));
    end
    faults{end+1}=struct('id',f.id,'base_id',f.base_id,'input',f.input,'cfg',f.cfg,'identifier',identifier,'message',message,'expected_guard',f.expected_guard,'prefix',prefix); %#ok<AGROW>
end
record('actual_six_modes',isequal(unique(coverage)',0:5));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'),'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'),'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.69','scope','SAVED_V68_EVENT_APPLICABILITY_INTEGRATION_BLOCKER','new_model',false,'runs',{runs},'faults',{faults},'root_probes',{probes},'metadata',metadata,'mode_coverage',unique(coverage)','assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'event_applicability_v69.mat'),'report','-v7.3');reopened=load(fullfile(folder,'event_applicability_v69.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);
mkdir(fullfile(folder,'binary'));manifest=struct('id',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopened.report.runs)
    r=reopened.report.runs{j};for field={'cfg','input','trace'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('id',r.id,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);
fprintf('EVENT_APPLICABILITY_V69 PASS=%d FAIL=%d RUNS=%d REJECTIONS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v69:AuditFailure','Inspect retained evidence');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true)); %#ok<NASGU>
    end
    function [trace,out]=execute(ii,cfg)
        ticks=(0:size(ii,1)-1)';mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[ticks ii]);assignin(mw,'dispatch_cfg_v66',[ticks repmat(cfg',size(ii,1),1)]);
        out=sim(mdl,'StopTime',num2str(size(ii,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,256,[])';assert(size(trace,1)==size(ii,1));
    end
end
