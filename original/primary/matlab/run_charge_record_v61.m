function run_charge_record_v61(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});runs={};faults=struct('id',{},'identifier',{},'expected',{});
for j=1:numel(spec.cases)
    c=spec.cases(j);c.age=c.age(:)';r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
    for factor=[1.2 1.5]
        total=factor*r.next_event_h;
        for iterations=[8 80]
            id=sprintf('%s_f%g_i%d',c.id,factor,iterations);
            z=dchr.components.charge_branch_record_v61(c.s,c.p,c.E,total,c.request,c.age,64,iterations);
            record([id '_positive_post_event'],z.post_event_duration_h_interval(1)>0&&z.end_energy_MWh_interval(1)>z.event_energy_MWh_interval(2));
            record([id '_first_law'],z.first_law_MWh_interval(1)<=0&&z.first_law_MWh_interval(2)>=0);
            record([id '_exact_manifold_retained'],ischar(z.exact_branch_energy_MWh.numerator)&&ischar(z.exact_branch_energy_MWh.denominator));
            record([id '_no_scalar_credit_or_memory'],~z.scalar_memory_handoff_authorized&&~z.compiled_stateflow_handoff_authorized);
            record([id '_expected_ties'],numel(z.right_equivalent_limiters)==c.expected_ties);
            record([id '_hp_age_no_reset'],z.event_hp_age_h_interval(1)>=c.age(1)&&z.end_hp_age_h_interval(1)>=c.age(1));
            runs{end+1}=struct('id',id,'input',c,'total_h',total,'iterations',iterations,'record',z); %#ok<AGROW>
        end
    end
end
c=spec.cases(1);c.age=c.age(:)';r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);total=1.5*r.next_event_h;
for j=1:8
    ss=c.s;pp=c.p;age=c.age;cells=64;it=80;tt=total;req=c.request;ee=c.E;
    expected='DCHR:v61:Domain';
    switch j
        case 1,age=[-.1 0];
        case 2,age=[1 0];
        case 3,cells=0;
        case 4,tt=NaN;
        case 5,tt=.5*r.next_event_h;expected='DCHR:v61:UnsupportedEvent';
        case 6,ss.hot_capacity_MW_per_K=.4;expected='DCHR:v61:UnsupportedEvent';
        case 7,it=1;expected='DCHR:v61:UnresolvedHorizon';
        case 8,ee=6.;expected='DCHR:v56:UnresolvedLimiter';
    end
    identifier='';try,dchr.components.charge_branch_record_v61(ss,pp,ee,tt,req,age,cells,it);catch e,identifier=e.identifier;end
    faults(end+1)=struct('id',sprintf('fault_%d',j),'identifier',identifier,'expected',expected); %#ok<AGROW>
    record(faults(end).id,strcmp(identifier,expected));
end
probes={};for value=[-.2 -1 0 eps(0) realmin .2 5 1e100]
    rr=dchr.components.exact_rational_v61('from',value);probes{end+1}=struct('value',value,'rational',rr); %#ok<AGROW>
    record(sprintf('rational_%d',numel(probes)),dchr.components.exact_rational_v61('cmp',rr,rr)==0);
end
report=struct('version','0.61','new_model',false,'coupled_stateflow_acceptance',false,'runs',{runs},'faults',faults, ...
    'rational_probes',{probes},'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'charge_record_v61.mat'),'report','-v7.3');writejson(fullfile(folder,'report.json'),report);
reopen=load(fullfile(folder,'charge_record_v61.mat'),'report');assert(isequaln(report,reopen.report));writejson(fullfile(folder,'mat_reopen.json'),reopen.report);
mkdir(fullfile(folder,'binary'));records=struct('id',{},'group',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopen.report.runs)
    item=reopen.report.runs{j};emit(item.id,'input','E_total_request_age',[item.input.E item.total_h item.input.request item.input.age]);
    for group={'s','p'}
        v=item.input.(group{1});names=fieldnames(v);for n=1:numel(names),emit(item.id,group{1},names{n},v.(names{n}));end
    end
    v=item.record;names=fieldnames(v);for n=1:numel(names),x=v.(names{n});if isnumeric(x)||islogical(x),emit(item.id,'record',names{n},double(x));end;end
end
writejson(fullfile(folder,'binary_manifest.json'),struct('source','ORIGINAL_REOPENED_MAT_BINARY64','source_mat','charge_record_v61.mat','records',records));
fprintf('CHARGE_RECORD_V61 PASS=%d FAIL=%d RUNS=%d\n',report.summary.passed,report.summary.failed,numel(runs));
assert(all([checks.passed]),'DCHR:v61:AcceptanceFailure','Inspect retained report.');
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

