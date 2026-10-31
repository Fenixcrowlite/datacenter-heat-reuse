function run_horizon_sensitivity_v86(folder)
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));
checks=struct('name',{},'passed',{});runs={};faults={};coverage=[];
c=getcase(1);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
mdl='DCHR_Electrical_Dispatch_Stateflow_v85';
path=fullfile(root,'matlab','simulink',[mdl '.slx']);
cfg=[a.protocol_ticks repmat([a.p c.ceiling_MW c.horizon_h],size(a.input,1),1)];
assert(isfile(path),'Accepted saved v85 is required; this experiment does not build a model');
load_system(path);cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
for j=1:numel(spec.cases)
    c=getcase(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
    raw=[a.p c.ceiling_MW c.horizon_h];[effective,Ebound]=electrical_policy_v85(raw',c.initial(1));a.p=effective';
    [out,trace,certificate]=execute(mdl,a,raw);
    rr=dchr.report_held_schedule_v76(a,trace);
    record([c.id '_finite'],all(isfinite([trace certificate]),'all'));
    record([c.id '_complete'],size(trace,1)==size(a.input,1));
    record([c.id '_certificate'],isequal(certificate,repmat([raw a.p(11) Ebound],size(trace,1),1)));
    record([c.id '_cap_never_increased'],a.p(11)<=raw(11));
    comparison=[];
    if c.compare80
        legacy='DCHR_Earliest_Dispatch_Stateflow_v80';
        load_system(fullfile(root,'matlab','simulink',[legacy '.slx']));
        [old,comparison]=execute(legacy,a,a.p); %#ok<ASGLU>
        close_system(legacy,0);
        record([c.id '_saved_v80_bitwise'],isequal(trace,comparison));
    end
    globalModel='DCHR_Electrical_Dispatch_Stateflow_v83r2';
    load_system(fullfile(root,'matlab','simulink',[globalModel '.slx']));
    [~,globalTrace]=execute(globalModel,a,raw(1:26));close_system(globalModel,0);
    runs{end+1}=struct('id',c.id,'family',c.family,'adapter',a,'input',a.input, ...
        'p',a.p,'raw_policy',raw,'trace',trace,'certificate',certificate,'summary',rr,'reference_trace',comparison,'global_trace',globalTrace); %#ok<AGROW>
    coverage=[coverage;trace(:,1)]; %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','trace','certificate','a','raw','rr','comparison','-v7.3');
    fprintf('HORIZON_V86 %s COMPLETE ROWS=%d CAP=%.17g PMAX=%.17g\n',c.id,size(trace,1),a.p(11),raw(26));
end
record('six_required_modes',isequal(unique(coverage)',0:5));
% Invalid raw operands reach the saved compiled chart, bypassing host adapter.
base=runs{2};
for j=1:7
    bad=repmat(base.raw_policy,size(base.input,1),1);
    faultAdapter=base.adapter;
    if j==1,bad(:,26)=-1;guard='v85 finite nonnegative compressor ceiling';name='negative';
    elseif j==2,bad(:,26)=NaN;guard='v85 finite nonnegative compressor ceiling';name='NaN';
    elseif j==3,bad(:,26)=Inf;guard='v85 finite nonnegative compressor ceiling';name='Inf';
    elseif j==5,bad(:,27)=base.input(1,5)/2;guard='v85 declared horizon exceeded';name='horizon_exceeded';
    elseif j==6,bad(2:end,27)=bad(2:end,27)*2;guard='v85 immutable electrical policy';name='delayed_horizon_change';
    elseif j==7,faultAdapter.input(:,8)=0;faultAdapter.input(:,12)=0;guard='v73 ON dwell not certified';name='ON_dwell';
    else,bad(2:end,26)=bad(2:end,26)/2;guard='v85 immutable electrical policy';name='delayed_nonbinding_change';end
    rejected=false;message='';
    try,execute(mdl,faultAdapter,bad);catch e,message=getReport(e,'extended','hyperlinks','off');rejected=contains(message,guard);end
    fd=fopen(fullfile(folder,['fault_' name '.txt']),'w');assert(fd>0);fprintf(fd,'%s',message);fclose(fd);
    record(['runtime_' name '_expected_rejection'],rejected);
    faults{end+1}=struct('id',name,'expected_guard',guard,'rejected',rejected,'message',message); %#ok<AGROW>
end
% Execute the exact one-hour declared endpoint, retaining either outcome.
probeIndex=find(arrayfun(@(j)contains(getcase(j).id,'service_E3.0_a1.0_H1_dt0.25'),1:numel(spec.cases)),1);
c=getcase(probeIndex);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
raw=[a.p c.ceiling_MW 1];a.p=electrical_policy_v85(raw',c.initial(1))';
probeTrace=[];probeCertificate=[];probeMessage='';probeAccepted=false;
try
    [~,probeTrace,probeCertificate]=execute(mdl,a,raw);probeAccepted=true;
catch e
    probeMessage=getReport(e,'extended','hyperlinks','off');
end
record('exact_horizon_probe_classified',probeAccepted||contains(probeMessage,'v85 declared horizon exceeded'));
endpoint_probe=struct('accepted',probeAccepted,'horizon_h',1,'adapter',a,'raw_policy',raw, ...
    'trace',probeTrace,'certificate',probeCertificate,'message',probeMessage);
writejson('exact_horizon_probe.json',endpoint_probe);
save(fullfile(folder,'exact_horizon_probe.mat'),'endpoint_probe','-v7.3');
close_system(mdl,0);load_system(path);
[~,replay,certReplay]=execute(mdl,runs{1}.adapter,runs{1}.raw_policy);
record('clean_saved_model_reopen_bitwise',isequal(replay,runs{1}.trace)&&isequal(certReplay,runs{1}.certificate));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(s)s.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.86','saved_model_version','0.85','trace_schema',75,'metadata',metadata, ...
    'runs',{runs},'faults',{faults},'mode_coverage',unique(coverage)', ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'horizon_sensitivity_v86.mat'),'report','-v7.3');
reopened=load(fullfile(folder,'horizon_sensitivity_v86.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);
mkdir(fullfile(folder,'binary'));manifest=struct('group',{},'index',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopened.report.runs)
    r=reopened.report.runs{j};
    for field={'input','p','trace','raw_policy','certificate','reference_trace','global_trace'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);
        fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('group','runs','index',j,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);
fprintf('HORIZON_V86 PASS=%d FAIL=%d COMPLETE_RUNS=%d FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v85:AcceptanceFailure','Inspect retained failures');
    function c=getcase(j)
        if iscell(spec.cases),c=spec.cases{j};else,c=spec.cases(j);end
    end
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,v)
        fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
        fprintf(fd,'%s\n',jsonencode(v,PrettyPrint=true));
    end
end
function [out,trace,certificate]=execute(mdl,a,raw)
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);
if size(raw,1)==1,raw=repmat(raw,size(a.input,1),1);end
assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks raw]);
out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');
trace=reshape(out.interval_trace_v66.Data,1380,[])';certificate=[];
if strcmp(mdl,'DCHR_Electrical_Dispatch_Stateflow_v85'),certificate=reshape(out.electrical_certificate_v83.Data,29,[])';end
end
