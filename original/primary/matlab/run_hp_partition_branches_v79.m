function run_hp_partition_branches_v79(folder)
% Focused actual runtime coverage of work and OFF branches, no saved edits.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
report=jsondecode(fileread(fullfile(folder,'report.json')));checks=struct('name',{},'passed',{});faults={};
mdl='DCHR_Earliest_Dispatch_Stateflow_v79';prior='DCHR_Earliest_Dispatch_Stateflow_v78';
load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));load_system(fullfile(root,'matlab','simulink',[prior '.slx']));
cleanup=onCleanup(@()closemodels(mdl,prior)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
pch=rt.find('-isa','Stateflow.Chart','Path',[prior '/Six_Mode_Interval_Dispatch']);
k=ch.find('-isa','Stateflow.EMFunction','Name','earliest_dispatch_kernel_v75');
pk=pch.find('-isa','Stateflow.EMFunction','Name','earliest_dispatch_kernel_v75');original=k.Script;
states=ch.find('-isa','Stateflow.State');labels=arrayfun(@(x)x.LabelString,states,'UniformOutput',false);
gate='monitor_hp_partition_v79(horizon_input,policy_input,retained_memory,core);';
ids={'compressor_disjoint_source_wide','OFF_spurious_source'};
baseids={'HP_only','zero_demand'};
expected={'v79 compressor temperature partition','v79 OFF HP energies'};
for j=1:2
    base=report.runs(find(strcmp({report.runs.id},baseids{j}),1));
    a=dchr.adapt_held_schedule_v74(reshape(base.adapter.schedule,1,6),base.p,base.adapter.initial);
    base.trace=reshape(base.trace,1,1380);
    assert(size(base.trace,1)==1&&base.trace(1,13)==1);
    if j==1,expr='y(133)';upper=base.trace(1,133);else,expr='0.01';upper=.01;end
    injection=sprintf('\nif old(2)==0\ny(134:137)=[0;%s;0;0];y(150:151)=0;\ny(17:20)=y(134:137);y(33:36)=y(134:137);y(49:50)=0;\nend\n',expr);
    anchor="y(57)=limit;y(62:65)=[ageCert;ageHi;ageErr'];";
    assert(numel(strfind(original,anchor))==1);
    k.Script=strrep(original,anchor,[char(anchor) injection]);pk.Script=k.Script;
    legacy=execute(prior,a);pk.Script=original;
    errorText='';rejected=false;
    try,execute(mdl,a);catch e,errorText=getReport(e,'extended','hyperlinks','off');rejected=contains(errorText,expected{j});end
    for s=1:numel(states),states(s).LabelString=strrep(labels{s},gate,'');end
    bypass=execute(mdl,a);
    for s=1:numel(states),states(s).LabelString=labels{s};end
    k.Script=original;
    wanted=base.trace;wanted(1,[134:137 17:20 33:36])=repmat([0 upper 0 0],1,3);
    wanted(1,[150:151 49:50])=0;
    record([ids{j} '_actual_runtime_rejection'],rejected);
    record([ids{j} '_exact_bypass'],isequal(bypass,wanted));
    record([ids{j} '_v78_acceptance'],isequal(legacy,wanted));
    faults{end+1}=struct('id',ids{j},'base_id',base.id,'trace',bypass,'legacy_trace',legacy, ...
        'expected_trace',wanted,'input',a.input,'p',a.p,'expected_text',expected{j}, ...
        'runtime_rejected',rejected,'error_text',errorText,'columns',find(wanted(1,:)~=base.trace(1,:)));
    fd=fopen(fullfile(folder,[ids{j} '_runtime_fault.txt']),'w');assert(fd>0);fprintf(fd,'%s\n',errorText);fclose(fd);
    fprintf('HP_BRANCH_V79 %s REJECTED=%d EXACT=%d V78_ACCEPTED=%d\n',ids{j},rejected,isequal(bypass,wanted),isequal(legacy,wanted));
end
close_system(mdl,0);load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
clean=report.runs(find(strcmp({report.runs.id},'HP_only'),1));
a=dchr.adapt_held_schedule_v74(reshape(clean.adapter.schedule,1,6),clean.p,clean.adapter.initial);
record('clean_reopened_bitwise',isequal(execute(mdl,a),reshape(clean.trace,1,1380)));
branch=struct('version','0.79','faults',{faults},'checks',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'hp_branches_v79.mat'),'branch','-v7.3');b=load(fullfile(folder,'hp_branches_v79.mat'));assert(isequaln(branch,b.branch));
fd=fopen(fullfile(folder,'branch_report.json'),'w');assert(fd>0);fprintf(fd,'%s\n',jsonencode(b.branch,PrettyPrint=true));fclose(fd);
assert(all([checks.passed]),'DCHR:v79:BranchQA','Inspect branch report');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function trace=execute(mdl,a)
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);
assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,1380,[])';
end
function closemodels(mdl,prior)
if bdIsLoaded(mdl),close_system(mdl,0);end
if bdIsLoaded(prior),close_system(prior,0);end
end
