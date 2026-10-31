function run_restart_chain_v64(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));mdl='DCHR_Restart_Chain_Stateflow_v64';
runs={};checks=struct('name',{},'passed',{});faults={};
for j=1:numel(spec.cases)
    c=spec.cases(j);c.age=c.age(:)';[cfg,steps,z]=adapt(c);
    if ~isfile(fullfile(root,'matlab','simulink',[mdl '.slx'])),build_restart_chain_v64(cfg,steps);end
    load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
    [trace,out]=execute(cfg,steps,[]);id=c.id;
    record([id '_phases'],isequal(trace(:,34)',[0 1 2 3 4 4 4 5 6 6]));
    record([id '_schema'],all(trace(:,112)==64)&all(trace(:,113)==cfg(35)));
    record([id '_first_law'],all(trace(:,53)<=0&trace(:,54)>=0));
    record([id '_positive_ports'],all(all(trace(:,41:52)>=0)));
    record([id '_bounds'],all(trace(:,37)>=0&trace(:,38)<=trace(:,59)));
    record([id '_HP_switches'],isequal(trace(:,55)',[1 1 1 0 0 0 0 1 1 1]));
    record([id '_no_scalar_service'],all(trace(:,56)==0));
    record([id '_frozen_OFF_ports'],isequal(trace(4:7,[41:46 49:52]),repmat(trace(4,[41:46 49:52]),4,1)));
    record([id '_dwell_threeway'],isequal(trace(5:7,72)',[0 2 1]));
    record([id '_thermal_guard'],trace(8,99)<=cfg(35));
    record([id '_OFF_guard'],trace(8,96)>=cfg(34));
    record([id '_restart_inventory_retained'],isequal(trace(8:10,82:83),repmat(trace(7,37:38),3,1))&&trace(8,82)<trace(8,83));
    record([id '_restart_port_offsets'],isequal(trace(8:10,84:95),repmat(trace(7,41:52),3,1)));
    record([id '_restart_origin'],all(trace(8:10,81)==steps(7,3)));
    record([id '_recharge_increasing'],all(diff(trace(7:10,37))>0)&&all(diff(trace(7:10,41))>0));
    record([id '_restart_ON_age'],all(diff(trace(8:10,39))>0)&&all(trace(8:10,39)<=trace(8:10,40)));
    record([id '_finite_hot_water'],all(trace(8:10,60)>=0)&&all(trace(8:10,60)<=cfg(15))&&all(trace(8:10,61)>=cfg(2)/cfg(9)));
    references={};cap=cfg(5)*(cfg(19)-cfg(6));tc=mean(cfg(32:33));
    for tick=[3 7 8 10]
        span=steps(tick,3);initial=cfg(1);charge=cfg(2);
        if tick==7,span=span-tc;initial=cap;charge=0;end
        if tick>=8,span=span-steps(7,3);initial=mean(trace(7,37:38));end
        pp=[span;cap;cfg(18);4;cfg(3);.8;cfg(4);0;cfg(5);cfg(6)];
        ref=dchr.components.storage_kernel_v30(initial,charge,0,pp);
        record(sprintf('%s_v30_energy_tick%d',id,tick),ref(4)>=trace(tick,37)&&ref(4)<=trace(tick,38));
        references{end+1}=struct('tick',tick,'initial',initial,'charge_request',charge,'parameters',pp','output',ref'); %#ok<AGROW>
    end
    runs{end+1}=struct('id',id,'input',c,'host_certificate',z,'cfg',cfg','steps',steps,'trace',trace,'references_v30',{references},'solver_time',out.restart_trace_v64.Time'); %#ok<AGROW>
    save(fullfile(folder,[id '.mat']),'out','cfg','steps','trace','z','c','-v7.3');
end
base=runs{1};cfg=base.cfg';steps=base.steps;
labels={'thermal_not_ready','dwell_not_ready','unresolved_dwell','restart_floor_unsupported','skip_restart', ...
    'missing_restart_command','delayed_thermal_provenance','delayed_manifold','delayed_nan', ...
    'reverse_recharge','recharge_cross_capacity','invalid_hysteresis','wrong_continuation_command','unsupported_span'};
expected={'thermal restart not certified','OFF dwell not certified','OFF dwell not certified','floor branch unsupported','phase mismatch', ...
    'explicit restart continuation','restart provenance','immutable provenance','finite input', ...
    'horizon must advance','capacity or branch crossing','thermal hysteresis domain','explicit restart continuation','outward span exceeds one'};
for j=1:numel(labels)
    cc=repmat(cfg',10,1);ss=steps;
    switch j
        case 1,ss(7,3)=cfg(33)+cfg(34)+.1;
        case 2,cc(:,34)=base.trace(7,71)+1;
        case 3,cc(:,34)=mean(base.trace(7,70:71));
        case 4
            cc(:,35)=45;ss(7,3)=cfg(33)+log(50/24)/cfg(4);
            ss(8:10,3)=ss(7,3)+[.03;.09;.2];cc(:,23)=ss(7,3)+.5;
        case 5,ss(8,2)=6;
        case 6,ss(8,4)=0;
        case 7,cc(8:end,35)=cfg(35)-1;
        case 8,cc(8:end,2)=cfg(2)+.01;
        case 9,cc(8:end,2)=NaN;
        case 10,ss(9,3)=ss(8,3);
        case 11,cc(:,23)=cc(:,23)+10;ss(10,3)=ss(7,3)+10;
        case 12,cc(:,35)=cfg(19);
        case 13,ss(9,4)=0;
        case 14,cc(:,23)=200;ss(10,3)=150;
    end
    identifier='';message='';try,execute(cfg,ss,cc);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record(labels{j},~isempty(identifier)&&contains(message,expected{j}));
    faults{end+1}=struct('id',labels{j},'identifier',identifier,'message',message,'expected_guard',expected{j},'cfg_rows',cc,'steps',ss); %#ok<AGROW>
end
[prefix,~]=execute(cfg,steps,[],6);record('seven_tick_prefix',isequal(prefix,base.trace(1:7,:)));
rt=sfroot;chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Correlated_Capacity_Chain']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(chart),'states',{arrayfun(@(a)a.Name,chart.find('-isa','Stateflow.State'),'UniformOutput',false)}, ...
    'action_language',chart.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'));
report=struct('version','0.64','scope','CERTIFIED_HORIZON_INTERVAL_RESTART_COMPONENT', ...
    'new_model',true,'coupled_six_mode_plant_acceptance',false,'runs',{runs},'faults',{faults},'valid_prefix',prefix,'metadata',metadata, ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'restart_chain_v64.mat'),'report','-v7.3');reopen=load(fullfile(folder,'restart_chain_v64.mat'));
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
fprintf('RESTART_CHAIN_V64 PASS=%d FAIL=%d RUNS=%d FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v64:AcceptanceFailure','Inspect retained report');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        path=fullfile(folder,name);assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cleanup=onCleanup(@()fclose(fd)); %#ok<NASGU>
        fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
    end
    function [trace,out]=execute(cfg,steps,rows,stop)
        if nargin<4,stop=9;end
        if isempty(rows),rows=repmat(cfg',10,1);end
        mw=get_param(mdl,'ModelWorkspace');assignin(mw,'restart_cfg_v64',[(0:9)' rows]);assignin(mw,'restart_steps_v64',steps);
        out=sim(mdl,'StopTime',num2str(stop),'ReturnWorkspaceOutputs','on');trace=reshape(out.restart_trace_v64.Data,114,[])';assert(size(trace,1)==stop+1);
    end
end
function [cfg,steps,z]=adapt(c)
s=c.s;p=c.p;cap=p.heat_capacity_MWh_per_K*(s.tank_max_C-p.ambient_C);B=p.eta_charge*c.request;
tc=-log((B-p.loss_rate_per_h*cap)/(B-p.loss_rate_per_h*c.E))/p.loss_rate_per_h;
r=dchr.components.charge_regime_events_v56(s,p,c.E,c.request);
z=dchr.components.charge_branch_record_v61(s,p,c.E,(tc+r.next_event_h)/2,c.request,c.age,64,8);
width=max(1e-9,1e-10*tc);cp=[tc-width tc+width];
% A deliberate sampled horizon beyond both thresholds, not a scalar root reset.
restart=cp(2)+max(p.min_off_h,log((s.tank_max_C-p.ambient_C)/(p.restart_C-p.ambient_C))/p.loss_rate_per_h)+.1;
total=restart+.5;names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};ties=double(ismember(names,z.right_equivalent_limiters));
cfg=[c.E c.request p.eta_charge p.loss_rate_per_h p.heat_capacity_MWh_per_K p.ambient_C ...
    s.delivery_C s.direct_approach_K s.charge_approach_K s.condenser_approach_K s.source_in_C s.source_glide_K ...
    s.evaporator_approach_K s.cooling_factor s.hot_capacity_MW_per_K s.hp_capacity_MW s.source_capacity_MW_per_K ...
    p.charge_limit_MW s.tank_max_C s.aux_per_compressor c.age total 63 z.event_time_h_interval ties cp p.min_off_h p.restart_C]';
steps=[(0:9)' [0;1;2;3;4;4;4;5;6;6] ...
    [0;0;(cfg(26)+cp(1))/2;0;cp(2)+p.min_off_h/2;tc+p.min_off_h;restart;restart+.03;restart+.09;restart+.2] ...
    [zeros(7,1);ones(3,1)]];
end
