function run_partition_sensitivity_v81(folder)
% Execute the preserved v80 SLX on identical held inputs split dyadically.
root=fileparts(fileparts(mfilename('fullpath')));
addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));
mdl='DCHR_Earliest_Dispatch_Stateflow_v80';
path=fullfile(root,'matlab','simulink',[mdl '.slx']);assert(isfile(path));
load_system(path);cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
checks=struct('name',{},'passed',{});runs={};attempts={};coverage=[];
for j=1:numel(spec.cases)
    c=spec.cases(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
    accepted=false;message='';identifier='';trace=[];
    try
        [out,trace]=execute(mdl,a);
        rr=dchr.report_held_schedule_v76(a,trace);
        accepted=true;
        runs{end+1}=struct('id',c.id,'family',c.family,'factor',c.factor, ...
            'adapter',a,'input',a.input,'p',a.p,'trace',trace,'summary',rr); %#ok<AGROW>
        coverage=[coverage;trace(:,1)]; %#ok<AGROW>
        save(fullfile(folder,[c.id '.mat']),'out','trace','a','rr','-v7.3');
        record([c.id '_finite_trace'],all(isfinite(trace),'all'));
        record([c.id '_all_holds_executed'],size(trace,1)==size(a.input,1));
    catch e
        identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');
        fd=fopen(fullfile(folder,[c.id '_failure.txt']),'w');assert(fd>0);
        fprintf(fd,'%s\n',message);fclose(fd);
    end
    record([c.id '_schedule_accepted'],accepted);
    attempts{end+1}=struct('id',c.id,'accepted',accepted,'identifier',identifier,'message',message); %#ok<AGROW>
    fprintf('PARTITION_V81 %s FACTOR=%d ACCEPTED=%d ROWS=%d\n',c.id,c.factor,accepted,size(trace,1));
end
record('six_required_final_modes',isequal(unique(coverage)',0:5));
assert(~isempty(runs));base=runs{1};
close_system(mdl,0);load_system(path);[~,replay]=execute(mdl,base.adapter);
record('clean_saved_model_reopened_bitwise',isequal(replay,base.trace));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(s)s.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.81','saved_model_version','0.80','new_model',false,'trace_schema',75, ...
    'metadata',metadata,'runs',{runs},'attempts',{attempts},'mode_coverage',unique(coverage)', ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'partition_sensitivity_v81.mat'),'report','-v7.3');
reopened=load(fullfile(folder,'partition_sensitivity_v81.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);
mkdir(fullfile(folder,'binary'));manifest=struct('group',{},'index',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopened.report.runs)
    r=reopened.report.runs{j};
    for field={'input','p','trace'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);
        fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('group','runs','index',j,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);
fprintf('PARTITION_V81 PASS=%d FAIL=%d COMPLETE_RUNS=%d\n',report.summary.passed,report.summary.failed,numel(runs));
assert(all([checks.passed]),'DCHR:v81:AcceptanceFailure','Inspect retained schedule failures');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,v)
        fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
        fprintf(fd,'%s\n',jsonencode(v,PrettyPrint=true));
    end
end
function [out,trace]=execute(mdl,a)
mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);
assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');
trace=reshape(out.interval_trace_v66.Data,1380,[])';
end
