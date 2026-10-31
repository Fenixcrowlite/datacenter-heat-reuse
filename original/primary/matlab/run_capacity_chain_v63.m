function run_capacity_chain_v63(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));mdl='DCHR_Capacity_Chain_Stateflow_v63';
runs={};checks=struct('name',{},'passed',{});faults={};
for j=1:numel(spec.cases)
    c=spec.cases(j);c.age=c.age(:)';[cfg,steps,z]=adapt(c);
    if ~isfile(fullfile(root,'matlab','simulink',[mdl '.slx'])),build_charge_memory_v63(cfg,steps);end
    load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
    [trace,out]=execute(cfg,steps,[]);id=c.id;
    record([id '_phases'],isequal(trace(:,34)',[0 1 2 3 4 4 4]));
    record([id '_provenance'],isequal(trace(:,1:31),repmat(cfg(1:31)',7,1))&&isequal(trace(:,65:67),repmat(cfg(32:34)',7,1)));
    record([id '_first_law'],all(trace(:,53)<=0&trace(:,54)>=0));
    record([id '_positive_ports'],all(all(trace(:,41:52)>=0)));
    record([id '_capacity_symbolic'],isequal(trace(4,37:38),trace(4,58:59))&&all(trace(:,56)==0));
    record([id '_bounds'],all(trace(:,37)>=0&trace(:,38)<=trace(:,59)));
    record([id '_HP_safety_OFF'],isequal(trace(:,55)',[1 1 1 0 0 0 0])&&all(all(trace(4:end,60:63)==0)));
    record([id '_frozen_charge_ports'],isequal(trace(4:end,[41:46 49:52]),repmat(trace(4,[41:46 49:52]),4,1)));
    record([id '_frozen_ON_age'],isequal(trace(4:end,39:40),repmat(trace(4,39:40),4,1)));
    record([id '_OFF_age'],all(diff(trace(4:end,70))>0)&all(diff(trace(4:end,71))>0));
    record([id '_dwell_threeway'],isequal(trace(5:end,72)',[0 2 1]));
    if cfg(4)==0
        record([id '_passive_identity'],isequal(trace(4:end,37:38),repmat(trace(4,37:38),4,1)));
    else
        record([id '_passive_cooling'],all(diff(trace(4:end,37))<0)&&all(diff(trace(4:end,47))>0));
    end
    references={};cap=cfg(5)*(cfg(19)-cfg(6));tc=mean(cfg(32:33));
    for tick=[3 5 6 7]
        span=steps(tick,3);initial=cfg(1);charge=cfg(2);
        if tick>3,span=span-tc;initial=cap;charge=0;end
        pp=[span;cap;cfg(18);4;cfg(3);.8;cfg(4);0;cfg(5);cfg(6)];
        ref=dchr.components.storage_kernel_v30(initial,charge,0,pp);
        record(sprintf('%s_v30_energy_tick%d',id,tick),ref(4)>=trace(tick,37)&&ref(4)<=trace(tick,38));
        references{end+1}=struct('tick',tick,'initial',initial,'charge_request',charge,'parameters',pp','output',ref'); %#ok<AGROW>
    end
    runs{end+1}=struct('id',id,'input',c,'host_certificate',z,'cfg',cfg','steps',steps,'trace',trace,'references_v30',{references},'solver_time',out.charge_trace_v63.Time'); %#ok<AGROW>
    save(fullfile(folder,[id '.mat']),'out','cfg','steps','trace','z','c','-v7.3');
end
base=runs{1};cfg=base.cfg';steps=base.steps;
labels={'skip_branch','skip_capacity','repeated_capacity','active_cross_capacity','passive_reverse', ...
    'bad_capacity_bracket','delayed_capacity_provenance','delayed_age_reset','early_restart','ready_restart_unsupported', ...
    'negative_dwell','delayed_nan','corrupt_tie','nonincreasing_trajectory'};
expected={'phase mismatch','phase mismatch','capacity contact sequence','crosses capacity','must advance', ...
    'capacity bracket','immutable manifold','immutable manifold','restart unsupported','restart unsupported', ...
    'OFF dwell domain','finite input','strict request limiter','increasing whole trajectory'};
for j=1:numel(labels)
    cc=repmat(cfg',7,1);ss=steps;
    switch j
        case 1,ss(2,2)=2;ss(2,3)=ss(3,3);
        case 2,ss(4,2)=4;ss(4,3)=ss(5,3);
        case 3,ss(5,2)=3;ss(5,3)=0;
        case 4,ss(3,3)=cfg(33)+.001;
        case 5,ss(6,3)=ss(5,3);
        case 6,cc(:,32:33)=cc(:,32:33)-.1;
        case 7,cc(5:end,32)=cc(5:end,32)+.001;
        case 8,cc(5:end,21:22)=0;
        case 9,ss(5,4)=1;
        case 10,ss(7,4)=1;
        case 11,cc(:,34)=-1;
        case 12,cc(5:end,2)=NaN;
        case 13,cc(:,29)=0;
        case 14,cc(:,4)=10;
    end
    identifier='';message='';try,execute(cfg,ss,cc);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record(labels{j},~isempty(identifier)&&contains(message,'v63')&&contains(message,expected{j}));
    faults{end+1}=struct('id',labels{j},'identifier',identifier,'message',message,'expected_guard',expected{j},'cfg_rows',cc,'steps',ss); %#ok<AGROW>
end
% Independent valid-prefix replay: same saved model, not inferred from a failed sim.
prefix=execute_prefix(cfg,steps);record('four_tick_prefix_before_delayed_fault',isequal(prefix,base.trace(1:4,:)));
rt=sfroot;chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Correlated_Capacity_Chain']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(chart),'states',{arrayfun(@(a)a.Name,chart.find('-isa','Stateflow.State'),'UniformOutput',false)}, ...
    'action_language',chart.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'));
report=struct('version','0.63','scope','CAPACITY_SAFETY_OFF_PASSIVE_COOLING_DWELL_ENCLOSURE_COMPONENT', ...
    'new_model',true,'coupled_six_mode_plant_acceptance',false,'runs',{runs},'faults',{faults},'valid_prefix',prefix,'metadata',metadata, ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'capacity_chain_v63.mat'),'report','-v7.3');reopen=load(fullfile(folder,'capacity_chain_v63.mat'));
assert(isequaln(reopen.report,report));writejson('report.json',report);writejson('mat_reopen.json',reopen.report);
mkdir(fullfile(folder,'binary'));manifest=struct('id',{},'field',{},'rows',{},'columns',{},'file',{});
for j=1:numel(reopen.report.runs)
    item=reopen.report.runs{j};for field={'cfg','steps','trace'}
        value=item.(field{1});file=sprintf('binary/%04d.bin',numel(manifest)+1);fd=fopen(fullfile(folder,file),'w','ieee-le');assert(fd>0);
        assert(fwrite(fd,value','double')==numel(value));fclose(fd);
        manifest(end+1)=struct('id',item.id,'field',field{1},'rows',size(value,1),'columns',size(value,2),'file',file); %#ok<AGROW>
    end
end
writejson('binary_manifest.json',manifest);close_system(mdl,0);
fprintf('CAPACITY_CHAIN_V63 PASS=%d FAIL=%d RUNS=%d FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v63:AcceptanceFailure','Inspect retained report');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        path=fullfile(folder,name);assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cleanup=onCleanup(@()fclose(fd)); %#ok<NASGU>
        fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
    end
    function [trace,out]=execute(cfg,steps,rows)
        if isempty(rows),rows=repmat(cfg',7,1);end
        mw=get_param(mdl,'ModelWorkspace');assignin(mw,'charge_cfg_v63',[(0:6)' rows]);assignin(mw,'charge_steps_v63',steps);
        out=sim(mdl,'StopTime','6','ReturnWorkspaceOutputs','on');trace=reshape(out.charge_trace_v63.Data,80,[])';assert(isequal(size(trace),[7 80]));
    end
    function trace=execute_prefix(cfg,steps)
        mw=get_param(mdl,'ModelWorkspace');assignin(mw,'charge_cfg_v63',[(0:6)' repmat(cfg',7,1)]);assignin(mw,'charge_steps_v63',steps);
        out=sim(mdl,'StopTime','3','ReturnWorkspaceOutputs','on');trace=reshape(out.charge_trace_v63.Data,80,[])';
    end
end
function [cfg,steps,z]=adapt(c)
s=c.s;p=c.p;cap=p.heat_capacity_MWh_per_K*(s.tank_max_C-p.ambient_C);B=p.eta_charge*c.request;
if p.loss_rate_per_h==0,tc=(cap-c.E)/B;else,tc=-log((B-p.loss_rate_per_h*cap)/(B-p.loss_rate_per_h*c.E))/p.loss_rate_per_h;end
r=dchr.components.charge_regime_events_v56(s,p,c.E,c.request);
z=dchr.components.charge_branch_record_v61(s,p,c.E,(tc+r.next_event_h)/2,c.request,c.age,64,8);
width=max(1e-9,1e-10*tc);cp=[tc-width tc+width];total=cp(2)+p.min_off_h+.2;
names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};ties=double(ismember(names,z.right_equivalent_limiters));
cfg=[c.E c.request p.eta_charge p.loss_rate_per_h p.heat_capacity_MWh_per_K p.ambient_C ...
    s.delivery_C s.direct_approach_K s.charge_approach_K s.condenser_approach_K s.source_in_C s.source_glide_K ...
    s.evaporator_approach_K s.cooling_factor s.hot_capacity_MW_per_K s.hp_capacity_MW s.source_capacity_MW_per_K ...
    p.charge_limit_MW s.tank_max_C s.aux_per_compressor c.age total 63 z.event_time_h_interval ties cp p.min_off_h]';
steps=[(0:6)' [0;1;2;3;4;4;4] [0;0;(cfg(26)+cp(1))/2;0;cp(2)+p.min_off_h/2;tc+p.min_off_h;total] zeros(7,1)];
end
