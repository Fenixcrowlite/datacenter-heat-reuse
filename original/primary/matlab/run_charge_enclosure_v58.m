function run_charge_enclosure_v58(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};
for j=1:numel(spec.cases)
    c=spec.cases(j);r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
    dt=min(.01,.1/(1+abs(r.k_per_h)));if isfinite(r.next_event_h),dt=min(dt,.1*r.next_event_h);end
    coarse=dchr.components.charge_enclosure_v58(c.s,c.p,c.E,dt,c.request,32);
    fine=dchr.components.charge_enclosure_v58(c.s,c.p,c.E,dt,c.request,256);
    record([c.id '_same_regime'],strcmp(fine.branch,r.branch)&&fine.limiter_index==r.limiter_index);
    record([c.id '_not_endpoint_authority'],~fine.event_transition_authorized);
    record([c.id '_positive_work'],fine.compressor_MWh_interval(1)>=0);
    record([c.id '_first_law_contains_zero'],fine.first_law_MWh_interval(1)<=0&&fine.first_law_MWh_interval(2)>=0);
    record([c.id '_narrowing'],diff(fine.source_MWh_interval)<=diff(coarse.source_MWh_interval)+1e-12);
    runs{end+1}=struct('input',c,'dt',dt,'coarse',coarse,'fine',fine); %#ok<AGROW>
end
c=spec.cases(1);badSpans=[0 -1 NaN Inf];faults=struct('id',{},'identifier',{});
for j=1:numel(badSpans)
    id='';try,dchr.components.charge_enclosure_v58(c.s,c.p,c.E,badSpans(j),c.request);catch e,id=e.identifier;end
    record(sprintf('bad_span_%d',j),strcmp(id,'DCHR:v58:Domain'));faults(end+1)=struct('id',sprintf('bad_span_%d',j),'identifier',id); %#ok<AGROW>
end
for n=[0 1.5 4097]
    id='';try,dchr.components.charge_enclosure_v58(c.s,c.p,c.E,.001,c.request,n);catch e,id=e.identifier;end
    record(sprintf('bad_cells_%g',n),strcmp(id,'DCHR:v58:Domain'));faults(end+1)=struct('id',sprintf('bad_cells_%g',n),'identifier',id); %#ok<AGROW>
end
% Preserve explicit failure at the mathematically nominal kink, rather than
% pretending an interval certificate authorizes a one-sided transition.
c=spec.cases(strcmp({spec.cases.id},'floor_branch'));r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
id='';try,dchr.components.charge_enclosure_v58(c.s,c.p,c.E,r.next_event_h,c.request);catch e,id=e.identifier;end
record('event_endpoint_rejected',strcmp(id,'DCHR:v58:EventUnresolved'));
faults(end+1)=struct('id','nominal_event_endpoint','identifier',id);
id='';try,dchr.components.coupled_temperature_boundary_v55(c.s,c.p,5.,c.request);catch e,id=e.identifier;end
record('original_kink_blocker_reproduced',strcmp(id,'DCHR:v55:UnresolvedBranch'));
blocker=struct('input',c,'energy_MWh',5.,'identifier',id,'nominal_event_h',r.next_event_h);
report=struct('version','0.58','new_model',false,'coupled_stateflow_acceptance',false, ...
    'runs',{runs},'faults',faults,'blocker',blocker,'assertions',checks, ...
    'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'charge_enclosure_v58.mat'),'report','-v7.3');
writejson(fullfile(folder,'report.json'),report);reopen=load(fullfile(folder,'charge_enclosure_v58.mat'),'report');
assert(isequaln(report,reopen.report));writejson(fullfile(folder,'mat_reopen.json'),reopen.report);
% Original MAT binary export, including all scalar source/policy inputs.
mkdir(fullfile(folder,'binary'));records={};
keys={'end_energy_MWh_interval','integral_energy_MWh_h_interval','heat_MWh_interval', ...
    'source_MWh_interval','compressor_MWh_interval','standing_loss_MWh_interval', ...
    'charge_loss_MWh_interval','aux_rejected_MWh_interval','first_law_MWh_interval', ...
    'alpha_interval','beta_interval','k_interval','B_interval','lift0_interval','lift1_interval','cooling_coefficient_interval'};
for j=1:numel(reopen.report.runs)
    item=reopen.report.runs{j};sn=fieldnames(item.input.s);pn=fieldnames(item.input.p);
    input=[item.input.E item.dt item.input.request];for n=1:numel(sn),input(end+1)=item.input.s.(sn{n});end %#ok<AGROW>
    for n=1:numel(pn),input(end+1)=item.input.p.(pn{n});end %#ok<AGROW>
    outputs=zeros(32,2);for n=1:numel(keys),outputs(n,:)=item.coarse.(keys{n});outputs(n+16,:)=item.fine.(keys{n});end
    file=sprintf('binary/case_%03d.bin',j);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
    fwrite(fd,[input reshape(outputs',1,[])],'double');fclose(fd);
    records{end+1}=struct('id',item.input.id,'file',file,'source_mat','charge_enclosure_v58.mat', ...
        's_names',{sn},'p_names',{pn},'output_names',{keys},'input_count',numel(input)); %#ok<AGROW>
end
writejson(fullfile(folder,'binary_manifest.json'),struct('source','ORIGINAL_REOPENED_MAT_BINARY64','records',{records}));
fprintf('CHARGE_ENCLOSURE_V58 PASS=%d FAIL=%d CASES=%d\n',report.summary.passed,report.summary.failed,numel(runs));
assert(all([checks.passed]),'DCHR:v58:AcceptanceFailure','Inspect preserved evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function writejson(path,value)
assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cl=onCleanup(@()fclose(fd)); %#ok<NASGU>
fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
end
