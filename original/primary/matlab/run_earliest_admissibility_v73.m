function run_earliest_admissibility_v73(folder)
% Build v73 only if absent, then execute its saved model without resaving it.
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));mdl='DCHR_Earliest_Dispatch_Stateflow_v73';
modelpath=fullfile(root,'matlab','simulink',[mdl '.slx']);if ~isfile(modelpath),c=spec.cases(1);ticks=(0:size(c.input,1)-1)';build_earliest_dispatch_v73([ticks c.input],[ticks repmat(c.p(:)',size(c.input,1),1)]);end
load_system(modelpath);
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
checks=struct('name',{},'passed',{});runs={};probes={};coverage=[];
for j=1:numel(spec.cases)
    c=spec.cases(j);p=c.p(:);ii=c.input;memory=zeros(1380,1);hostFailure='';faultTick=0;
    for k=1:size(ii,1)
        try,memory=earliest_dispatch_kernel_v73(ii(k,:)',p,memory);
        catch e,hostFailure=getReport(e,'extended','hyperlinks','off');faultTick=k;break;end
    end
    message='';identifier='';trace=[];out=[];
    try,[trace,out]=execute(ii,p);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record([c.id '_host_model_outcome'],(faultTick==0&&isempty(identifier))||(faultTick>0&&~isempty(identifier)));
    record([c.id '_expected_outcome'],c.expected_accept==isempty(identifier));
    if ~c.expected_accept,record([c.id '_expected_guard'],contains(message,c.expected_guard));end
    if isempty(identifier)
        saveRun(c.id,c.family,ii,p,trace,out);
    elseif faultTick>1
        [prefix,prefixOut]=execute(ii(1:faultTick-1,:),p);
        saveRun([c.id '_valid_prefix'],c.family,ii(1:faultTick-1,:),p,prefix,prefixOut);
    end
    probes{end+1}=struct('id',c.id,'family',c.family,'input',ii,'p',p','accepted',isempty(identifier), ...
        'fault_tick',faultTick,'identifier',identifier,'message',message,'host_message',hostFailure); %#ok<AGROW>
    fprintf('PROBE_V73 %s ACCEPTED=%d FIRST_REJECTED_TICK=%d\n',c.id,isempty(identifier),faultTick);
end
record('actual_six_modes',isequal(unique(coverage)',0:5));rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.73','saved_model_version','0.73','runs',{runs},'probes',{probes},'metadata',metadata, ...
    'mode_coverage',unique(coverage)','assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'earliest_admissibility_v73.mat'),'report','-v7.3');reopened=load(fullfile(folder,'earliest_admissibility_v73.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);mkdir(fullfile(folder,'binary'));
manifest=struct('id',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopened.report.runs)
    r=reopened.report.runs{j};for field={'p','input','trace'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('id',r.id,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
% Rejected input operands also come from the reopened original MAT.
for j=1:numel(reopened.report.probes)
    r=reopened.report.probes{j};for field={'p','input'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('id',['probe_' r.id],'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);
fprintf('EARLIEST_ADMISSIBILITY_V73 PASS=%d FAIL=%d ACCEPTED_RUNS=%d PROBES=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(probes));
assert(all([checks.passed]),'DCHR:v73:AuditFailure','Inspect preserved evidence');
    function saveRun(id,family,input,p,trace,out)
        record([id '_first_law'],all(trace(:,53)<=0&trace(:,54)>=0));record([id '_bounds'],all(trace(:,5)>=0&trace(:,5)<=trace(:,6)));
        memory=zeros(1380,1);modes=[];references={};
        for tick=1:size(input,1)
            host=earliest_dispatch_kernel_v73(input(tick,:)',p,memory);record(sprintf('%s_host_%d',id,tick),isequal(host',trace(tick,:)));memory=host;
            for slot=1:trace(tick,13)
                z=trace(tick,100+80*(slot-1)+(1:80));modes(end+1)=z(2); %#ok<AGROW>
                record(sprintf('%s_segment_%d_%d',id,tick,slot),z(7)>0&&z(26)*z(27)==0&&z(28)<=p(24));
                if z(11)==z(12)&&z(7)==z(8)
                    pp=[z(7);p(1)*(p(3)-p(2));p(9);p(10);p(7);p(8);p(6);p(1)*(p(4)-p(2));p(1);p(2)];
                    rr=dchr.components.storage_kernel_v30(z(11),z(26),z(27),pp);
                    record(sprintf('%s_v30_%d_%d',id,tick,slot),rr(4)>=z(13)&&rr(4)<=z(14));
                    references{end+1}=struct('parameters',pp','initial',z(11),'charge',z(26),'discharge',z(27),'output',rr'); %#ok<AGROW>
                end
            end
        end
        runs{end+1}=struct('id',id,'family',family,'p',p','input',input,'trace',trace,'reference_v30',{references},'mode_coverage',unique(modes)); %#ok<AGROW>
        save(fullfile(folder,[id '.mat']),'out','trace','p','input','-v7.3');coverage=[coverage;modes(:)]; %#ok<AGROW>
    end
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true)); %#ok<NASGU>
    end
    function [trace,out]=execute(ii,p)
        ticks=(0:size(ii,1)-1)';mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[ticks ii]);assignin(mw,'dispatch_cfg_v66',[ticks repmat(p',size(ii,1),1)]);
        out=sim(mdl,'StopTime',num2str(size(ii,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,1380,[])';assert(size(trace,1)==size(ii,1));
    end
end
