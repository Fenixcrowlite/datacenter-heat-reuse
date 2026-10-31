function run_reporting_provenance_v75(folder)
% Build, reopen and simulate additive Stateflow v75; compare saved v73r2.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};mutations={};coverage=[];
models={'DCHR_Earliest_Dispatch_Stateflow_v75','DCHR_Earliest_Dispatch_Stateflow_v73r2'};
a=dchr.adapt_held_schedule_v74(spec.cases(1).schedule,spec.cases(1).p,spec.cases(1).initial);
if ~isfile(fullfile(root,'matlab','simulink',[models{1} '.slx']))
    build_earliest_dispatch_v75([a.protocol_ticks a.input],[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
end
for j=1:2,load_system(fullfile(root,'matlab','simulink',[models{j} '.slx']));end
cleanup=onCleanup(@()closeModels(models)); %#ok<NASGU>
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
for j=1:numel(spec.cases)
    c=spec.cases(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
    [trace,out]=execute(models{1},a);[prior,priorOut]=execute(models{2},a);
    mask=true(1,1380);mask([2 73:75])=false;
    record([c.id '_dispatch_bitwise_preserved'],isequal(trace(:,mask),prior(:,mask)));
    rr=dchr.report_held_schedule_v75(a,trace);legacy=dchr.report_held_schedule_v74(a,prior);
    for field=fieldnames(legacy)'
        if ~ismember(field{1},{'version','saved_model_version'}),record([c.id '_' field{1}],isequaln(rr.(field{1}),legacy.(field{1})));end
    end
    runs{end+1}=struct('id',c.id,'adapter',a,'input',a.input,'p',a.p,'trace',trace,'prior_trace',prior,'summary',rr); %#ok<AGROW>
    coverage=[coverage;trace(:,1)]; %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','priorOut','trace','prior','a','rr','-v7.3');
    fprintf('REPORTING_V75 %s INTERVALS=%d\n',c.id,size(trace,1));
end
record('actual_six_modes',isequal(unique(coverage)',0:5));
% Each single-fault control uses actual saved-model traces. Legacy acceptance
% is recorded as a defect, while the additive reporter must refuse it.
r=runs{find(cellfun(@(r)strcmp(r.id,'HP_only'),runs),1)};
corrupt('service_header',r,'trace',44,1,'DCHR:v75:CumulativeTotals');
corrupt('source_header',r,'trace',34,2,'DCHR:v75:CumulativeTotals');
corrupt('work_header',r,'trace',36,2,'DCHR:v75:CumulativeTotals');
corrupt('negative_aux_header',r,'trace',50,3,'DCHR:v75:CumulativeTotals');
corrupt('reversed_service_header',r,'trace',44,4,'DCHR:v75:CumulativeTotals');
corrupt('zero_segment_count',r,'trace',13,2,'DCHR:v75:SegmentCount');
corrupt('fractional_segment_count',r,'trace',13,5,'DCHR:v75:SegmentCount');
corrupt('mode_header',r,'trace',1,2,'DCHR:v75:ModeEvents');
corrupt('event_header',r,'trace',14,1,'DCHR:v75:ModeEvents');
corrupt('origin_header',r,'trace',52,1,'DCHR:v75:OriginBinding');
corrupt('residual_header',r,'trace',54,1,'DCHR:v75:RecomputedLaw');
corrupt('source_schedule',r,'source',0,0,'DCHR:v75:InputBinding');
corrupt('HP_enable_schedule',r,'hp_enable',0,0,'DCHR:v75:InputBinding');
corrupt('charge_enable_schedule',r,'charge_enable',0,0,'DCHR:v75:InputBinding');
corrupt('adapter_input_only',r,'input_only',0,0,'DCHR:v75:AdapterBinding');
r=runs{find(cellfun(@(r)strcmp(r.id,'insufficient_heat'),runs),1)};
corrupt('unmet_header',r,'trace',48,2,'DCHR:v75:CumulativeTotals');
r=runs{find(cellfun(@(r)strcmp(r.id,'boiler_limit'),runs),1)};
corrupt('backup_header',r,'trace',46,2,'DCHR:v75:CumulativeTotals');
% Source misattribution is substantive: executing the changed source schedule
% produces a different physical trajectory, although the legacy report accepts
% the old trace with the changed source operands.
r=runs{find(cellfun(@(r)strcmp(r.id,'HP_only'),runs),1)};changed=r.adapter.schedule;changed(:,4)=0;
ab=dchr.adapt_held_schedule_v74(changed,r.p,r.adapter.initial);[changedTrace,changedOut]=execute(models{1},ab);
changedReport=dchr.report_held_schedule_v75(ab,changedTrace);
record('changed_source_actual_heat_differs',~isequal(changedTrace(:,31:32),r.trace(:,31:32)));
record('changed_source_actual_work_differs',~isequal(changedTrace(:,35:36),r.trace(:,35:36)));
runs{end+1}=struct('id','changed_source_actual','adapter',ab,'input',ab.input,'p',ab.p,'trace',changedTrace,'prior_trace',[],'summary',changedReport);
save(fullfile(folder,'changed_source_actual.mat'),'changedOut','ab','changedTrace','changedReport','-v7.3');
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[models{1} '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(models{1},'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.75','new_model',true,'metadata',metadata,'runs',{runs},'mutations',{mutations}, ...
    'assertions',checks,'mode_coverage',unique(coverage)', ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'reporting_provenance_v75.mat'),'report','-v7.3');reopened=load(fullfile(folder,'reporting_provenance_v75.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);mkdir(fullfile(folder,'binary'));
manifest=struct('group',{},'index',{},'field',{},'rows',{},'columns',{},'file',{});
for group={'runs','mutations'}
    objs=reopened.report.(group{1});
    for j=1:numel(objs)
        for field={'input','p','trace','prior_trace'}
            if ~isfield(objs{j},field{1}),continue;end
            v=objs{j}.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
            assert(fwrite(fd,v','double')==numel(v));fclose(fd);
            manifest(end+1)=struct('group',group{1},'index',j,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
        end
    end
end
writejson('binary_manifest.json',manifest);
fprintf('REPORTING_PROVENANCE_V75 PASS=%d FAIL=%d MUTATIONS=%d\n',report.summary.passed,report.summary.failed,numel(mutations));
assert(all([checks.passed]),'DCHR:v75:AuditFailure','Inspect evidence');
    function corrupt(id,r,kind,column,op,expected)
        a=r.adapter;t=r.trace;prior=r.prior_trace;
        if strcmp(kind,'trace')
            if op==1
                if ismember(column,[14 54]),t(end,column)=t(end,column)+1;else,t(end,column-1:column)=t(end,column-1:column)+1;end
            elseif op==2,t(end,column-1+mod(column,2):column)=0;
            elseif op==3,t(end,column-1:column)=[-2 -1];
            elseif op==4,t(end,column-1:column)=fliplr(t(end,column-1:column));
            elseif op==5,t(end,column)=1.5;end
            prior=t;prior(:,2)=73;prior(:,73:75)=0;
        elseif strcmp(kind,'input_only'),a.input(:,7)=0;
        else
            if strcmp(kind,'source'),a.schedule(:,4)=0;elseif strcmp(kind,'hp_enable'),a.schedule(:,5)=0;else,a.schedule(:,6)=1-a.schedule(:,6);end
            a=dchr.adapt_held_schedule_v74(a.schedule,a.p,a.initial);
        end
        oldError='';newError='';oldSummary=[];
        try,oldSummary=dchr.report_held_schedule_v74(a,prior);catch e,oldError=e.identifier;end
        try,dchr.report_held_schedule_v75(a,t);catch e,newError=e.identifier;end
        record([id '_new_rejection'],strcmp(newError,expected));
        record([id '_legacy_acceptance_reproduced'],isempty(oldError));
        mutations{end+1}=struct('id',id,'base_id',r.id,'kind',kind,'adapter',a,'input',a.input,'p',a.p,'trace',t, ...
            'legacy_accepted',isempty(oldError),'legacy_error',oldError,'legacy_summary',oldSummary,'new_error',newError,'expected_error',expected); %#ok<AGROW>
        fprintf('REPORTING_MUTATION %s LEGACY_ACCEPTED=%d NEW=%s\n',id,isempty(oldError),newError);
    end
    function [trace,out]=execute(mdl,a)
        mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
        out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,1380,[])';
        assert(size(trace,1)==size(a.input,1));
    end
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,v),fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(v,PrettyPrint=true));end %#ok<NASGU>
end
function closeModels(models)
for j=1:numel(models),close_system(models{j},0);end
end
