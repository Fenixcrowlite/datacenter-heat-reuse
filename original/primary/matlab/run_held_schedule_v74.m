function run_held_schedule_v74(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};probes={};references={};coverage=[];
models={'DCHR_Earliest_Dispatch_Stateflow_v73r2','DCHR_Interval_Dispatch_Stateflow_v66','DCHR_Dispatch_Stateflow_v57'};
for j=1:3,load_system(fullfile(root,'matlab','simulink',[models{j} '.slx']));end
cleanup=onCleanup(@()closeModels(models)); %#ok<NASGU>
for j=1:numel(spec.cases)
    c=spec.cases(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);ii=a.input;p=a.p;
    if strcmp(c.family,'raw_clock_refusal'),ii(2,3)=ii(1,3);end
    faultTick=0;memory=zeros(1380,1);hostMessage='';
    for k=1:size(ii,1)
        try,memory=earliest_dispatch_kernel_v73r2(ii(k,:)',p(:),memory);
        catch e,faultTick=k;hostMessage=getReport(e,'extended','hyperlinks','off');break;end
    end
    identifier='';message='';trace=[];out=[];
    try,[trace,out]=execute(models{1},ii,p,1380);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    accepted=isempty(identifier);record([c.id '_host_actual_outcome'],accepted==(faultTick==0));
    record([c.id '_expected_outcome'],accepted==isempty(c.expected_guard));
    if ~isempty(c.expected_guard),record([c.id '_actual_guard'],contains(message,c.expected_guard)&&contains(hostMessage,c.expected_guard));end
    probes{end+1}=struct('id',c.id,'family',c.family,'adapter',a,'input',ii,'p',p,'accepted',accepted, ...
        'fault_tick',faultTick,'identifier',identifier,'message',message,'host_message',hostMessage,'expected_guard',c.expected_guard); %#ok<AGROW>
    if accepted
        rr=dchr.report_held_schedule_v74(a,trace);saveRun(c.id,a,ii,p,trace,out,rr,true);
        if c.compare66
            cfg=[spec.v66_prefix_cfg(:)' p];[t66,o66]=execute(models{2},ii,cfg,205);
            record([c.id '_v66_count'],size(t66,1)==size(ii,1));record([c.id '_v66_law'],all(t66(:,53)<=0&t66(:,54)>=0));
            references{end+1}=struct('id',c.id,'model','v66','p',p,'cfg',cfg,'input',ii,'trace',t66); %#ok<AGROW>
            save(fullfile(folder,[c.id '_v66.mat']),'o66','t66','cfg','ii','-v7.3');
        end
        if c.compare57
            [legacy,legacyOut]=execute57(c.id,a);
            record([c.id '_v57_observed_outcome'],isempty(legacy.error_message));
            record([c.id '_v57_prefix_count'],size(legacy.dispatch,1)<=size(ii,1));
            record([c.id '_v57_law'],all(abs(legacy.accounting(:,5))<1e-9));
            references{end+1}=legacy; %#ok<AGROW>
            save(fullfile(folder,[c.id '_v57.mat']),'legacy','legacyOut','-v7.3');
        end
    elseif faultTick>1
        ap=dchr.adapt_held_schedule_v74(c.schedule(1:faultTick-1,:),c.p,c.initial);
        [prefix,prefixOut]=execute(models{1},ap.input,p,1380);
        pr=dchr.report_held_schedule_v74(ap,prefix);saveRun([c.id '_valid_prefix'],ap,ap.input,p,prefix,prefixOut,pr,false);
    end
    fprintf('HELD_V74 %s ACCEPTED=%d REJECTED_TICK=%d\n',c.id,accepted,faultTick);
end
record('actual_six_final_modes',isequal(unique(coverage)',0:5));
% Adapter controls reject malformed labels/flags; valid future inputs cannot
% alter the executed prefix. Reporter must refuse an incomplete schedule.
a=runs{1}.adapter;bad=a.schedule;bad(1,2)=bad(1,2)+.01;expect(@()dchr.adapt_held_schedule_v74(bad,a.p,a.initial),'DCHR:v74:PhysicalLabels');
bad=a.schedule;bad(1,5)=2;expect(@()dchr.adapt_held_schedule_v74(bad,a.p,a.initial),'DCHR:v74:ScheduleDomain');
r=runs{find(cellfun(@(r)strcmp(r.id,'equal_service_HP'),runs),1)};
expect(@()dchr.report_held_schedule_v74(r.adapter,r.trace(1:end-1,:)),'DCHR:v74:IncompleteSchedule');
bad=r.adapter;bad.initial(1)=bad.initial(1)+1;bad.input(:,10)=bad.initial(1);
expect(@()dchr.report_held_schedule_v74(bad,r.trace),'DCHR:v74:InitialTrace');
bad=r.adapter;bad.schedule(:,3)=bad.schedule(:,3)+1;bad.input(:,6)=bad.schedule(:,3);
expect(@()dchr.report_held_schedule_v74(bad,r.trace),'DCHR:v74:DemandTrace');
future=r.adapter;future.input(end,6)=3;[changed,~]=execute(models{1},future.input,future.p,1380);
record('future_input_preserves_entire_prefix',isequal(changed(1:end-1,:),r.trace(1:end-1,:)));
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[models{1} '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(models{1},'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.74','new_model',false,'saved_model_version','0.73r2','metadata',metadata, ...
    'runs',{runs},'probes',{probes},'references',{references},'mode_coverage',unique(coverage)', ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'held_schedule_v74.mat'),'report','-v7.3');reopened=load(fullfile(folder,'held_schedule_v74.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);mkdir(fullfile(folder,'binary'));
manifest=struct('group',{},'index',{},'id',{},'field',{},'rows',{},'columns',{},'file',{});
for group={'runs','probes','references'}
    objs=reopened.report.(group{1});
    for j=1:numel(objs)
        r=objs{j};fields={'input','p'};
        if ~strcmp(group{1},'probes'),fields{end+1}='trace';end
        if strcmp(group{1},'references')
            if strcmp(r.model,'v66'),fields{end+1}='cfg';else,fields={'input','p','c','m0','dispatch','segments','boundary','accounting','clock_start','clock_end','energy_start'};end
        end
        for f=fields
            v=r.(f{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
            assert(fwrite(fd,v','double')==numel(v));fclose(fd);
            manifest(end+1)=struct('group',group{1},'index',j,'id',r.id,'field',f{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
        end
    end
end
writejson('binary_manifest.json',manifest);
fprintf('HELD_SCHEDULE_V74 PASS=%d FAIL=%d RUNS=%d REFERENCES=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(references));
assert(all([checks.passed]),'DCHR:v74:AuditFailure','Inspect retained evidence');
    function saveRun(id,a,input,p,trace,out,summary,complete)
        modes=[];memory=zeros(1380,1);
        for k=1:size(input,1)
            host=earliest_dispatch_kernel_v73r2(input(k,:)',p(:),memory);record(sprintf('%s_saved_host_%d',id,k),isequal(host',trace(k,:)));memory=host;
            for slot=1:trace(k,13),z=trace(k,100+80*(slot-1)+(1:80));modes(end+1)=z(2);end %#ok<AGROW>
        end
        record([id '_service_demand_enclosures_overlap'],summary.service_plus_unmet_MWh_hull(1)<=summary.demand_MWh_hull(2)&&summary.service_plus_unmet_MWh_hull(2)>=summary.demand_MWh_hull(1));
        runs{end+1}=struct('id',id,'adapter',a,'input',input,'p',p,'trace',trace,'summary',summary,'complete_original_schedule',complete,'solver_time',out.interval_trace_v66.Time'); %#ok<AGROW>
        coverage=[coverage;trace(:,1)];save(fullfile(folder,[id '.mat']),'a','input','p','trace','out','summary','-v7.3');
    end
    function [trace,out]=execute(mdl,ii,p,width)
        ticks=(0:size(ii,1)-1)';mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[ticks ii]);assignin(mw,'dispatch_cfg_v66',[ticks repmat(p(:)',size(ii,1),1)]);
        out=sim(mdl,'StopTime',num2str(size(ii,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,width,[])';assert(size(trace,1)==size(ii,1));
    end
    function [r,out]=execute57(id,a)
        pp=a.p;dt=a.schedule(1,1);assert(all(a.schedule(:,1)==dt));n=size(a.input,1);
        assert(all(a.schedule(:,5)==(a.schedule(:,4)>0))&&all(a.schedule(:,6)==1|pp(9)==0|a.schedule(:,4)==0), ...
            'DCHR:v74:LegacyUnsupported','v57 cannot express independent enable/charge changes');
        v=[pp(12:14) pp(18) pp(3) pp(19) pp(17) pp(4)-pp(19) pp(20) pp(2) 0 pp(16) pp(11) pp(15) pp(21) 0 0];
        inputs=repmat(v,n,1);inputs(:,11)=a.schedule(:,4);inputs(:,17)=a.schedule(:,3);
        p57=[dt pp(1)*(pp(3)-pp(2)) pp(9:10) pp(7:8) pp(6) pp(1)*(pp(4)-pp(2)) pp(1:2) pp(24)];
        c57=[pp(1)*(pp(5)-pp(2)) pp(22:23) 64];m0=[a.initial(2);a.initial(3);0;0];
        si=Simulink.SimulationInput(models{3});names={'dt','stop','input','p','E0','c','m0'};
        values={dt,(n-1)*dt,[(0:n-1)'*dt inputs],p57,a.initial(1),c57,m0};
        for k=1:numel(names),si=si.setVariable(['dchr_' names{k} '_v57'],values{k},'Workspace',models{3});end
        out=sim(si.setModelParameter('CaptureErrors','on'));
        label='v57';if ~isempty(out.ErrorMessage),label='v57_refusal';end
        r=struct('id',id,'model',label,'input',inputs,'p',p57,'c',c57,'m0',m0', ...
            'initial',a.initial,'dt',dt,'dispatch',samples(out.dispatch_trace_v57,25), ...
            'segments',samples(out.segment_trace_v57,1792),'boundary',samples(out.finite_boundary_trace_v57,13), ...
            'accounting',samples(out.finite_accounting_trace_v57,7),'clock_start',samples(out.clock_start_trace_v57,4), ...
            'clock_end',samples(out.clock_end_trace_v57,4),'energy_start',samples(out.energy_start_trace_v57,1), ...
            'error_message',out.ErrorMessage,'completed_intervals',numel(out.dispatch_trace_v57.Time), ...
            'boundary_semantics','FIXED_MAX_TANK_CONDENSER_BOUNDARY; NO_STOP_TEMPERATURE_GUARD; NO_INDEPENDENT_ENABLE_COMMAND');
        fprintf('LEGACY_V57 %s COMPLETED=%d/%d REFUSED=%d\n',id,r.completed_intervals,n,~isempty(r.error_message));
    end
    function v=samples(ts,width)
        n=numel(ts.Time);raw=ts.Data;
        if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;else,v=reshape(raw,width,n)';end
    end
    function expect(fn,id),caught='';try,fn();catch e,caught=e.identifier;end;record(id,strcmp(caught,id));end
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value),fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));end %#ok<NASGU>
end
function closeModels(models)
for i=1:numel(models),close_system(models{i},0);end
end
