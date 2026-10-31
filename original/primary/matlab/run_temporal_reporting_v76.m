function run_temporal_reporting_v76(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};mutations={};coverage=[];
mdl='DCHR_Earliest_Dispatch_Stateflow_v75';load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
sldiagviewer.diary(fullfile(folder,'simulink_diagnostics.txt'));
for j=1:numel(spec.cases)
    c=spec.cases(j);a=dchr.adapt_held_schedule_v74(c.schedule,c.p,c.initial);
    mw=get_param(mdl,'ModelWorkspace');assignin(mw,'dispatch_input_v66',[a.protocol_ticks a.input]);
    assignin(mw,'dispatch_cfg_v66',[a.protocol_ticks repmat(a.p,size(a.input,1),1)]);
    out=sim(mdl,'StopTime',num2str(size(a.input,1)-1),'ReturnWorkspaceOutputs','on');trace=reshape(out.interval_trace_v66.Data,1380,[])';
    rr=dchr.report_held_schedule_v76(a,trace);prior=dchr.report_held_schedule_v75(a,trace);
    for field=fieldnames(prior)'
        if ~strcmp(field{1},'version'),record([c.id '_' field{1}],isequaln(rr.(field{1}),prior.(field{1})));end
    end
    runs{end+1}=struct('id',c.id,'adapter',a,'input',a.input,'p',a.p,'trace',trace,'summary',rr); %#ok<AGROW>
    coverage=[coverage;trace(:,1)]; %#ok<AGROW>
    save(fullfile(folder,[c.id '.mat']),'out','trace','a','rr','-v7.3');
    fprintf('TEMPORAL_V76 %s INTERVALS=%d SEGMENTS=%d\n',c.id,size(trace,1),sum(trace(:,13)));
end
record('actual_six_modes',isequal(unique(coverage)',0:5));
base=runs{find(cellfun(@(r)strcmp(r.id,'temporal_chain'),runs),1)};
controls={...
 'endpoint_latch',7,'toggle','EndpointMemory';...
 'endpoint_age',8:9,'shift','EndpointMemory';...
 'endpoint_contact',12,'contact','EndpointMemory';...
 'incoming_clock',58:59,'shift','MacroContinuity';...
 'boundary_clock',60:61,'shift','MacroContinuity';...
 'reported_clock',10:11,'widen','MacroContinuity';...
 'segment_start',105:106,'shift','SegmentClock';...
 'segment_elapsed',109:110,'shift','SegmentClock';...
 'segment_incoming_inventory',111:112,'shift','SegmentMemory';...
 'segment_incoming_latch',178,'toggle','SegmentMemory';...
 'segment_incoming_age',179:180,'shift','SegmentMemory';...
 'segment_incoming_contact',121,'contact','SegmentMemory';...
 'boundary_age',115:116,'shift','BoundaryMemory';...
 'boundary_latch',119,'toggle','BoundaryMemory';...
 'segment_endpoint_latch',120,'toggle','EventMemory';...
 'segment_endpoint_age',117:118,'shift','EventMemory';...
 'segment_endpoint_contact',122,'contact','EventMemory';...
 'unknown_boundary_reason',123,'unknown','TransitionDomain';...
 'segment_endpoint_inventory',113:114,'shift','EndpointMemory'};
for j=1:size(controls,1)
    t=base.trace;cols=controls{j,2};op=controls{j,3};
    if strcmp(op,'shift'),t(2,cols)=t(2,cols)+1;
    elseif strcmp(op,'toggle'),t(2,cols)=1-t(2,cols);
    elseif strcmp(op,'contact'),t(2,cols)=mod(t(2,cols)+1,4);
    elseif strcmp(op,'unknown'),t(2,cols)=4;
    else,t(2,cols)=t(2,cols)+[-1 1];end
    oldError='';newError='';
    try,dchr.report_held_schedule_v75(base.adapter,t);catch e,oldError=e.identifier;end
    try,dchr.report_held_schedule_v76(base.adapter,t);catch e,newError=e.identifier;end
    expected=['DCHR:v76:' controls{j,4}];
    record([controls{j,1} '_v75_accepts'],isempty(oldError));
    record([controls{j,1} '_v76_refuses'],strcmp(newError,expected));
    mutations{end+1}=struct('id',controls{j,1},'base_id',base.id,'row',2,'columns',cols, ...
        'trace',t,'legacy_accepted',isempty(oldError),'legacy_error',oldError,'new_error',newError,'expected_error',expected); %#ok<AGROW>
    fprintf('TEMPORAL_CONTROL %s V75_ACCEPTED=%d V76=%s\n',controls{j,1},isempty(oldError),newError);
end
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Six_Mode_Interval_Dispatch']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'), ...
    'chart_count',numel(ch),'action_language',ch.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'states',{arrayfun(@(x)x.Name,ch.find('-isa','Stateflow.State'),'UniformOutput',false)});
report=struct('version','0.76','saved_model_version','0.75','new_model',false,'metadata',metadata, ...
    'runs',{runs},'mutations',{mutations},'mode_coverage',unique(coverage)', ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'temporal_reporting_v76.mat'),'report','-v7.3');reopened=load(fullfile(folder,'temporal_reporting_v76.mat'));assert(isequaln(report,reopened.report));
writejson('report.json',report);writejson('mat_reopen.json',reopened.report);mkdir(fullfile(folder,'binary'));
manifest=struct('group',{},'index',{},'field',{},'rows',{},'columns',{},'file',{});
for group={'runs','mutations'}
    objs=reopened.report.(group{1});
    for j=1:numel(objs)
        for field={'input','p','trace'}
            if ~isfield(objs{j},field{1}),continue;end
            v=objs{j}.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
            assert(fwrite(fd,v','double')==numel(v));fclose(fd);
            manifest(end+1)=struct('group',group{1},'index',j,'field',field{1},'rows',size(v,1),'columns',size(v,2),'file',file); %#ok<AGROW>
        end
    end
end
writejson('binary_manifest.json',manifest);
fprintf('TEMPORAL_REPORTING_V76 PASS=%d FAIL=%d CONTROLS=%d\n',report.summary.passed,report.summary.failed,numel(mutations));
assert(all([checks.passed]),'DCHR:v76:AuditFailure','Inspect evidence');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,v),fd=fopen(fullfile(folder,name),'w');assert(fd>0);cl=onCleanup(@()fclose(fd));fprintf(fd,'%s\n',jsonencode(v,PrettyPrint=true));end %#ok<NASGU>
end
