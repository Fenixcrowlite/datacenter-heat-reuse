function run_charge_events_v59(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};faults=struct('id',{},'identifier',{});
for j=1:numel(spec.cases)
    c=spec.cases(j);r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
    ceiling=100;if r.k_per_h~=0,ceiling=min(ceiling,.5/abs(r.k_per_h));end
    horizons=[min(.001,ceiling) ceiling];
    if isfinite(r.next_event_h),horizons=[horizons min(.5*r.next_event_h,ceiling) min(1.1*r.next_event_h,ceiling) min(r.next_event_h,ceiling)];end %#ok<AGROW>
    horizons=unique(horizons);
    for h=1:numel(horizons)
        dt=horizons(h);id=sprintf('%s_h%d',c.id,h);
        z=dchr.components.charge_event_window_v59(c.s,c.p,c.E,dt,c.request);
        record([id '_strict_prefix'],all(z.safe_prefix_guard_intervals(:,1)>0));
        record([id '_window_order'],z.first_event_window_h(1)<=z.first_event_window_h(2)&&z.first_event_window_h(2)<=dt);
        record([id '_no_transition_or_memory_reset'],~z.event_transition_authorized&&~z.memory_handoff_authorized);
        record([id '_event_upper'],~z.crossing_isolated||any(z.upper_crossing_certified));
        % Retain integrated ports on an interior certified physical prefix.
        % Event brackets are NOT integrated as physical time or service.
        integratedSpan=z.safe_prefix_h/2;
        assert(integratedSpan>0,'DCHR:v59:Fixture','Fixture needs a positive safe prefix.');
        prefix=dchr.components.charge_enclosure_v58(c.s,c.p,c.E,integratedSpan,c.request,128);
        record([id '_prefix_port_balance'],prefix.first_law_MWh_interval(1)<=0&&prefix.first_law_MWh_interval(2)>=0);
        runs{end+1}=struct('id',id,'input',c,'horizon_h',dt,'event',z,'integrated_span_h',integratedSpan,'integrated_prefix',prefix); %#ok<AGROW>
    end
end
c=spec.cases(1);
for t=[0 -1 NaN Inf]
    identifier='';try,dchr.components.charge_event_window_v59(c.s,c.p,c.E,t,c.request);catch e,identifier=e.identifier;end
    faults(end+1)=struct('id',sprintf('horizon_%d',numel(faults)+1),'identifier',identifier); %#ok<AGROW>
    record(faults(end).id,strcmp(identifier,'DCHR:v59:Domain'));
end
for n=[0 1.5 129]
    identifier='';try,dchr.components.charge_event_window_v59(c.s,c.p,c.E,.01,c.request,n);catch e,identifier=e.identifier;end
    faults(end+1)=struct('id',sprintf('iterations_%d',numel(faults)+1),'identifier',identifier); %#ok<AGROW>
    record(faults(end).id,strcmp(identifier,'DCHR:v59:Domain'));
end
c=spec.cases(strcmp({spec.cases.id},'stationary_exact'));identifier='';
try,dchr.components.charge_event_window_v59(c.s,c.p,c.E,8,c.request);catch e,identifier=e.identifier;end
faults(end+1)=struct('id','span_excess','identifier',identifier);record('span_excess',strcmp(identifier,'DCHR:v59:Span'));
% A coarse iteration budget cannot turn an event window into a point event.
c=spec.cases(strcmp({spec.cases.id},'simultaneous_branch_hot'));r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
coarse=dchr.components.charge_event_window_v59(c.s,c.p,c.E,1.1*r.next_event_h,c.request,1);
record('one_iteration_remains_blocked',coarse.crossing_isolated&&~coarse.memory_handoff_authorized&&diff(coarse.first_event_window_h)>0);
% Original binary endpoint and adjacent representable value; preserve both.
c=spec.cases(strcmp({spec.cases.id},'simultaneous_branch_hot'));endpoints=[5 5+eps(5)];gaps=zeros(2,2);ids=cell(1,2);
for n=1:2
    cert=dchr.components.coupled_branch_certificate_v55(c.s,c.p,endpoints(n),c.request);gaps(n,:)=cert.gap_K_interval;
    ids{n}='';try,dchr.components.charge_regime_events_v56(c.s,c.p,endpoints(n),c.request);catch e,ids{n}=e.identifier;end
end
record('scalar_kink_continuation_rejects',all(~cellfun(@isempty,ids)));
tieId='';try,dchr.components.charge_regime_events_v56(c.s,c.p,6.,c.request);catch e,tieId=e.identifier;end
record('resolved_post_branch_persistent_tie_rejects',strcmp(tieId,'DCHR:v56:UnresolvedLimiter'));
blocker=struct('input',c,'adjacent_energy_MWh',endpoints,'gap_K_intervals',gaps,'rejection_identifiers',{ids}, ...
    'resolved_tank_energy_MWh',6.,'persistent_tie_identifier',tieId, ...
    'scope','NO_REPRESENTABLE_EXACT_BRANCH_ENDPOINT_NO_CORRELATED_INTERVAL_HANDOFF');
report=struct('version','0.59','new_model',false,'coupled_stateflow_acceptance',false,'runs',{runs},'faults',faults, ...
    'coarse_event',coarse,'blocker',blocker,'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'charge_events_v59.mat'),'report','-v7.3');writejson(fullfile(folder,'report.json'),report);
reopen=load(fullfile(folder,'charge_events_v59.mat'),'report');assert(isequaln(report,reopen.report));writejson(fullfile(folder,'mat_reopen.json'),reopen.report);
mkdir(fullfile(folder,'binary'));records=struct('id',{},'group',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopen.report.runs)
    item=reopen.report.runs{j};emit(item.id,'input','E_horizon_request_span',[item.input.E item.horizon_h item.input.request item.integrated_span_h]);
    for group={'s','p'}
        value=item.input.(group{1});names=fieldnames(value);for n=1:numel(names),emit(item.id,group{1},names{n},value.(names{n}));end
    end
    for group={'event','integrated_prefix'}
        value=item.(group{1});names=fieldnames(value);
        for n=1:numel(names),v=value.(names{n});if isnumeric(v)||islogical(v),emit(item.id,group{1},names{n},double(v));end;end
    end
end
emit('blocker','witness','adjacent_energy_MWh',reopen.report.blocker.adjacent_energy_MWh);
emit('blocker','witness','gap_K_intervals',reopen.report.blocker.gap_K_intervals);
emit('blocker','witness','resolved_tank_energy_MWh',reopen.report.blocker.resolved_tank_energy_MWh);
writejson(fullfile(folder,'binary_manifest.json'),struct('source','ORIGINAL_REOPENED_MAT_BINARY64','source_mat','charge_events_v59.mat','records',records));
fprintf('CHARGE_EVENTS_V59 PASS=%d FAIL=%d RUNS=%d\n',report.summary.passed,report.summary.failed,numel(runs));
assert(all([checks.passed]),'DCHR:v59:AcceptanceFailure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function emit(id,group,field,v)
        file=sprintf('binary/%05d.bin',numel(records)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,v','double')==numel(v));fclose(fd);
        records(end+1)=struct('id',id,'group',group,'field',field,'rows',size(v,1),'columns',size(v,2),'file',file);
    end
end
function writejson(path,value)
assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
end
