function run_energy_commit_v78(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};faults={};coverage=[];
first=spec.cases(1);a=dchr.adapt_held_schedule_v74(first.schedule,first.p,first.initial);
path=build_energy_commit_v78([a.protocol_ticks a.input],[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
mdl='DCHR_Earliest_Dispatch_Stateflow_v78';prior='DCHR_Earliest_Dispatch_Stateflow_v77';
load_system(path);load_system(fullfile(root,'matlab','simulink',[prior '.slx']));
cleanup=onCleanup(@()closemodels(mdl,prior)); %#ok<NASGU>
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
for j=1:numel(spec.cases)
    c=spec.cases(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
    [out,trace]=execute(mdl,a);[~,prior_trace]=execute(prior,a);
    record([c.id '_bitwise_saved_v77'],isequal(trace,prior_trace));
    rr=dchr.report_held_schedule_v76(a,trace);
    runs{end+1}=struct('id',c.id,'adapter',a,'input',a.input,'p',a.p,'trace',trace,'prior_trace',prior_trace,'summary',rr); %#ok<AGROW>
    coverage=[coverage;trace(:,1)]; %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','trace','prior_trace','a','rr','-v7.3');
    fprintf('COMMIT_V78 %s INTERVALS=%d SEGMENTS=%d EVENTS=%d BITWISE=%d\n',c.id,size(trace,1),sum(trace(:,13)),sum(trace(:,14)),isequal(trace,prior_trace));
end
record('actual_six_modes',isequal(unique(coverage)',0:5));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
kernel=ch.find('-isa','Stateflow.EMFunction','Name','earliest_dispatch_kernel_v75');original=kernel.Script;
priorCh=rt.find('-isa','Stateflow.Chart','Path',[prior '/Six_Mode_Interval_Dispatch']);
priorKernel=priorCh.find('-isa','Stateflow.EMFunction','Name','earliest_dispatch_kernel_v75');
assert(strcmp(priorKernel.Script,original));
states=ch.find('-isa','Stateflow.State');labels=arrayfun(@(x)x.LabelString,states,'UniformOutput',false);
gate='monitor_energy_commit_v78(horizon_input,policy_input,retained_memory,core);';
for j=1:numel(states),record(['state_' states(j).Name '_two_precommit_gates'],numel(strfind(labels{j},gate))==2);end
base=runs{find(cellfun(@(r)strcmp(r.id,'temporal_chain'),runs),1)};
for j=1:numel(spec.faults)
    f=spec.faults(j);target=base;
    if f.event>0
        found=false;
        for b=1:numel(runs)
            for k=1:size(runs{b}.trace,1)
                row=runs{b}.trace(k,:);
                for slot=1:row(13)
                    if row(100+80*(slot-1)+3)==f.event
                        target=runs{b};rowIndex=k;eventSlot=slot;found=true;break;
                    end
                end
                if found,break;end
            end
            if found,break;end
        end
        assert(found,'DCHR:v78:FixtureEvent','Requested actual event not exercised');
        col=100+80*(eventSlot-1)+f.local_columns(:)';
    else,rowIndex=2;col=f.columns(:)';end
    a=dchr.adapt_held_schedule_v74(target.adapter.schedule(1:rowIndex,:),target.p,target.adapter.initial);
    cols=mat2str(col);condition=sprintf('u(3)==%.17g',a.input(end,3));
    if strcmp(f.operation,'negative'),rhs='-1';
    elseif strcmp(f.operation,'smallshift'),rhs=['y(' cols ')+0.125'];
    elseif strcmp(f.operation,'toggle'),rhs=['1-y(' cols ')'];
    elseif strcmp(f.operation,'contact'),rhs=['mod(y(' cols ')+1,4)'];
    elseif strcmp(f.operation,'unknown'),rhs='4';
    elseif strcmp(f.operation,'widen'),rhs=['y(' cols ')+[-1;1]'];
    else,rhs=['y(' cols ')+1'];end
    injection=sprintf('\nif %s,y(%s)=%s;end\n',condition,cols,rhs);
    anchor="y(57)=limit;y(62:65)=[ageCert;ageHi;ageErr'];";
    assert(numel(strfind(original,anchor))==1);kernel.Script=strrep(original,anchor,[char(anchor) injection]);
    priorKernel.Script=strrep(original,anchor,[char(anchor) injection]);
    [~,legacy]=execute(prior,a);priorKernel.Script=original;
    expected=['v78 ' f.expected];errorText='';errorId='';rejected=false;
    try,execute(mdl,a);catch e,errorText=getReport(e,'extended','hyperlinks','off');errorId=e.identifier;rejected=contains(errorText,expected);end
    record([f.id '_runtime_refuses_expected'],rejected);
    for s=1:numel(states),states(s).LabelString=strrep(labels{s},gate,'');end
    [~,bypass]=execute(mdl,a);
    for s=1:numel(states),states(s).LabelString=labels{s};end
    kernel.Script=original;
    expectedTrace=target.trace(1:rowIndex,:);
    if strcmp(f.operation,'negative'),expectedTrace(end,col)=-1;
    elseif strcmp(f.operation,'smallshift'),expectedTrace(end,col)=expectedTrace(end,col)+0.125;
    elseif strcmp(f.operation,'toggle'),expectedTrace(end,col)=1-expectedTrace(end,col);
    elseif strcmp(f.operation,'contact'),expectedTrace(end,col)=mod(expectedTrace(end,col)+1,4);
    elseif strcmp(f.operation,'unknown'),expectedTrace(end,col)=4;
    elseif strcmp(f.operation,'widen'),expectedTrace(end,col)=expectedTrace(end,col)+[-1 1];
    else,expectedTrace(end,col)=expectedTrace(end,col)+1;end
    record([f.id '_bypass_is_exact_single_fault'],isequal(bypass,expectedTrace));
    record([f.id '_saved_v77_monitor_accepts_same_fault'],isequal(legacy,expectedTrace));
    faults{end+1}=struct('id',f.id,'base_id',target.id,'row',rowIndex,'columns',col,'event',f.event, ...
        'input',a.input,'p',a.p,'trace',bypass,'legacy_trace',legacy,'expected_text',expected,'runtime_rejected',rejected,'error_id',errorId,'error_text',errorText,'injection',injection); %#ok<AGROW>
    fd=fopen(fullfile(folder,[f.id '_runtime_fault.txt']),'w');assert(fd>0);fprintf(fd,'%s\n',errorText);fclose(fd);
    fprintf('RUNTIME_CONTROL %s REJECTED=%d EXPECTED=%s BYPASS_MATCH=%d\n',f.id,rejected,expected,isequal(bypass,expectedTrace));
end
record('restored_kernel',strcmp(kernel.Script,original));
record('restored_prior_kernel',strcmp(priorKernel.Script,original));
for s=1:numel(states),record(['restored_' states(s).Name],strcmp(states(s).LabelString,labels{s}));end
% Reload the saved artifact after all unsaved test instrumentation.
close_system(mdl,0);load_system(path);[~,restored]=execute(mdl,base.adapter);
record('reopened_saved_model_clean_bitwise',isequal(restored,base.trace));
ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'chart_count',numel(ch), ...
    'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.78','saved_model_version','0.78','trace_schema',75,'new_model',true,'metadata',metadata, ...
    'runs',{runs},'faults',{faults},'mode_coverage',unique(coverage)', ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'energy_commit_v78.mat'),'report','-v7.3');reopened=load(fullfile(folder,'energy_commit_v78.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);mkdir(fullfile(folder,'binary'));
manifest=struct('group',{},'index',{},'field',{},'rows',{},'columns',{},'file',{});
for group={'runs','faults'}
    objs=reopened.report.(group{1});
    for j=1:numel(objs)
        for field={'input','p','trace','prior_trace','legacy_trace'}
            if ~isfield(objs{j},field{1}),continue;end
            v=objs{j}.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
            assert(fwrite(fd,v','double')==numel(v));fclose(fd);
            manifest(end+1)=struct('group',group{1},'index',j,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
        end
    end
end
writejson('binary_manifest.json',manifest);
fprintf('ENERGY_COMMIT_V78 PASS=%d FAIL=%d RUNTIME_FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(faults));
assert(all([checks.passed]),'DCHR:v78:AuditFailure','Inspect evidence');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,v),fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(v,PrettyPrint=true));end %#ok<NASGU>
end
function [out,trace]=execute(mdl,a)
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);
assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,1380,[])';
end
function closemodels(mdl,prior)
if bdIsLoaded(mdl),close_system(mdl,0);end
if bdIsLoaded(prior),close_system(prior,0);end
end
