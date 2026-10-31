function run_earliest_dispatch_v71(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));mdl='DCHR_Earliest_Dispatch_Stateflow_v71';modelpath=fullfile(root,'matlab','simulink',[mdl '.slx']);
if iscell(spec.faults),spec.faults=cellfun(@orderfields,spec.faults,'UniformOutput',false);spec.faults=[spec.faults{:}];end
if ~isfile(modelpath)
    c=spec.cases(1);ticks=(0:size(c.input,1)-1)';build_earliest_dispatch_v71([ticks c.input],[ticks repmat(c.p(:)',size(c.input,1),1)]);
end
load_system(modelpath);cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
checks=struct('name',{},'passed',{});runs={};faults={};coverage=[];
for j=1:numel(spec.cases)
    c=spec.cases(j);p=c.p(:);input=c.input;[trace,out]=execute(input,p);
    record([c.id '_schema'],all(trace(:,2)==71));record([c.id '_first_law'],all(trace(:,53)<=0&trace(:,54)>=0));
    record([c.id '_bounds'],all(trace(:,5)>=0&trace(:,5)<=trace(:,6)));
    record([c.id '_segments'],all(trace(:,13)>=1&trace(:,13)<=16));
    memory=zeros(1380,1);modes=[];references={};
    for k=1:size(input,1)
        host=earliest_dispatch_kernel_v71(input(k,:)',p,memory);record(sprintf('%s_host_%d',c.id,k),isequal(host',trace(k,:)));memory=host;
        for s=1:trace(k,13)
            z=trace(k,100+80*(s-1)+(1:80));modes(end+1)=z(2); %#ok<AGROW>
            record(sprintf('%s_positive_%d_%d',c.id,k,s),z(7)>0&&z(7)<=z(8));
            record(sprintf('%s_exclusive_%d_%d',c.id,k,s),z(26)*z(27)==0);
            record(sprintf('%s_boiler_%d_%d',c.id,k,s),z(28)<=p(24));
            record(sprintf('%s_service_%d_%d',c.id,k,s),abs(input(k,6)-sum(z([25 27 28 29])))<=1e-12);
            % v30 comparison only on genuinely exact singleton segment starts
            % and durations: no midpoint is fed into a scalar reference.
            if z(11)==z(12)&&z(7)==z(8)
                pp=[z(7);p(1)*(p(3)-p(2));p(9);p(10);p(7);p(8);p(6);p(1)*(p(4)-p(2));p(1);p(2)];
                rr=dchr.components.storage_kernel_v30(z(11),z(26),z(27),pp);
                record(sprintf('%s_v30_%d_%d',c.id,k,s),rr(4)>=z(13)&&rr(4)<=z(14));
                references{end+1}=struct('parameters',pp','initial',z(11),'charge',z(26),'discharge',z(27),'output',rr'); %#ok<AGROW>
            end
        end
    end
    record([c.id '_required_modes'],all(ismember(c.expected_modes,unique(modes))));
    record([c.id '_min_events'],sum(trace(:,14))>=c.min_events);
    runs{end+1}=struct('id',c.id,'p',p','input',input,'trace',trace,'reference_v30',{references},'mode_coverage',unique(modes),'solver_time',out.interval_trace_v66.Time'); %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','trace','p','input','-v7.3');coverage=[coverage;modes(:)]; %#ok<AGROW>
end
for j=1:numel(spec.faults)
    f=spec.faults(j);identifier='';message='';
    try,execute(f.input,f.p(:));catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record([f.id '_rejection'],~isempty(identifier)&&contains(message,f.expected_guard));prefix=[];
    if size(f.input,1)>1
        [prefix,~]=execute(f.input(1:end-1,:),f.p(:));ix=find(cellfun(@(r)strcmp(r.id,f.base_id),runs));
        record([f.id '_valid_prefix'],isequal(prefix,runs{ix}.trace(1:size(prefix,1),:)));
    end
    faults{end+1}=struct('id',f.id,'base_id',f.base_id,'input',f.input,'p',f.p,'identifier',identifier,'message',message,'expected_guard',f.expected_guard,'prefix',prefix); %#ok<AGROW>
end
record('actual_six_modes',isequal(unique(coverage)',0:5));rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'),'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'),'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.71','scope','CORRELATED_EARLIEST_EVENT_SEGMENTS','runs',{runs},'faults',{faults},'metadata',metadata,'mode_coverage',unique(coverage)','assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'earliest_dispatch_v71.mat'),'report','-v7.3');reopened=load(fullfile(folder,'earliest_dispatch_v71.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);mkdir(fullfile(folder,'binary'));manifest=struct('id',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopened.report.runs)
    r=reopened.report.runs{j};for field={'p','input','trace'}
        v=r.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        manifest(end+1)=struct('id',r.id,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);fprintf('EARLIEST_DISPATCH_V71 PASS=%d FAIL=%d RUNS=%d REJECTIONS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v71:AuditFailure','Inspect retained evidence');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true)); %#ok<NASGU>
    end
    function [trace,out]=execute(ii,p)
        ticks=(0:size(ii,1)-1)';mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[ticks ii]);assignin(mw,'dispatch_cfg_v66',[ticks repmat(p',size(ii,1),1)]);
        out=sim(mdl,'StopTime',num2str(size(ii,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,1380,[])';assert(size(trace,1)==size(ii,1));
    end
end
