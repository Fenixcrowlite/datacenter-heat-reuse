function run_charge_memory_v62(folder)
root=fileparts(fileparts(mfilename('fullpath')));addpath(fullfile(root,'matlab'),fullfile(root,'matlab','simulink'));
assert(isfolder(folder)&&~isfile(fullfile(folder,'report.json')));
spec=jsondecode(fileread(fullfile(folder,'spec.json')));mdl='DCHR_Charge_Memory_Stateflow_v62';
runs={};checks=struct('name',{},'passed',{});faults={};
for j=1:numel(spec.cases)
    c=spec.cases(j);c.age=c.age(:)';r=dchr.components.charge_regime_events_v56(c.s,c.p,c.E,c.request);
    for factor=[1.2 1.5]
        total=factor*r.next_event_h;z=dchr.components.charge_branch_record_v61(c.s,c.p,c.E,total,c.request,c.age,64,8);
        [cfg,steps]=adapt(c,z);
        if ~isfile(fullfile(root,'matlab','simulink',[mdl '.slx'])),build_charge_memory_v62(cfg,steps);end
        load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
        [trace,out]=execute(cfg,steps,[]);id=sprintf('%s_f%g',c.id,factor);
        record([id '_phases'],isequal(trace(:,34)',[0 1 2 2 2]));
        record([id '_immutable_provenance'],isequal(trace(:,1:31),repmat(cfg',5,1)));
        record([id '_clock_continuity'],all(diff(trace(:,39))>0)&&all(diff(trace(:,40))>0)&&all(trace(:,55)==1));
        record([id '_no_scalar_snap'],all(trace(:,56)==0)&&all(trace(:,57)==62)&&all(trace(3:end,37)>trace(2,33)));
        record([id '_first_law'],all(trace(:,53)<=0&trace(:,54)>=0));
        record([id '_bounds'],all(trace(:,37)>=0&trace(:,38)<trace(:,58)));
        record([id '_positive_ports'],all(all(trace(:,41:52)>=0)));
        record([id '_tank_linked_boundary'],all(diff(trace(3:end,62))>0));
        runs{end+1}=struct('id',id,'input',c,'total_h',total,'host_certificate',z,'cfg',cfg', ...
            'steps',steps,'trace',trace,'solver_time',out.charge_trace_v62.Time'); %#ok<AGROW>
        save(fullfile(folder,[id '.mat']),'out','cfg','steps','trace','z','c','total','-v7.3');
    end
end
% Mutations execute inside the actual saved chart, including valid-prefix faults.
base=runs{1};cfg=base.cfg';steps=base.steps;
labels={'skip_contact','repeat_contact','reverse_horizon','beyond_horizon','negative_source', ...
    'corrupt_provenance','corrupt_event_window','reset_age','corrupt_tie','scalar_schema','nan_parameter','nonincreasing_trajectory'};
for j=1:numel(labels)
    cc=repmat(cfg',5,1);ss=steps;
    switch j
        case 1,ss(2,2)=2;ss(2,3)=ss(3,3);
        case 2,ss(3,2)=1;ss(3,3)=0;
        case 3,ss(4,3)=ss(3,3);
        case 4,ss(5,3)=cfg(23)*2;
        case 5,cc(1,17)=-1;
        case 6,cc(3:end,7)=cc(3:end,7)+1;
        case 7,cc(1,25)=cc(1,26);
        case 8,cc(3:end,21:22)=0;
        case 9,cc(1,29)=0;
        case 10,cc(1,24)=0;
        case 11,cc(1,1)=NaN;
        case 12,cc(:,4)=10;
    end
    identifier='';message='';try,execute(cfg,ss,cc);catch e,identifier=e.identifier;message=getReport(e,'extended','hyperlinks','off');end
    record(labels{j},~isempty(identifier)&&contains(message,'v62'));
    faults{end+1}=struct('id',labels{j},'identifier',identifier,'message',message,'cfg_rows',cc,'steps',ss); %#ok<AGROW>
end
close_system(mdl,0);rt=sfroot;load_system(fullfile(root,'matlab','simulink',[mdl '.slx']));
chart=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Correlated_Charge_Memory']);
metadata=struct('matlab_version',version,'license_observed',license('test','Stateflow'),'stateflow_ver',ver('stateflow'), ...
    'chart_count',numel(chart),'states',{arrayfun(@(a)a.Name,chart.find('-isa','Stateflow.State'),'UniformOutput',false)}, ...
    'action_language',chart.ActionLanguage,'simulation_mode',get_param(mdl,'SimulationMode'));
report=struct('version','0.62','scope','COMPILED_CORRELATED_CONSTANT_REQUEST_BRANCH_MEMORY_ONLY', ...
    'new_model',true,'coupled_six_mode_plant_acceptance',false,'runs',{runs},'faults',{faults},'metadata',metadata, ...
    'assertions',checks,'summary',struct('passed',sum([checks.passed]),'failed',sum(~[checks.passed])));
save(fullfile(folder,'charge_memory_v62.mat'),'report','-v7.3');reopen=load(fullfile(folder,'charge_memory_v62.mat'));
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
fprintf('CHARGE_MEMORY_V62 PASS=%d FAIL=%d RUNS=%d FAULTS=%d\n',report.summary.passed,report.summary.failed,numel(runs),numel(faults));
assert(all([checks.passed]),'DCHR:v62:AcceptanceFailure','Inspect retained report');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
    function writejson(name,value)
        path=fullfile(folder,name);assert(~isfile(path));fd=fopen(path,'w');assert(fd>0);cleanup=onCleanup(@()fclose(fd)); %#ok<NASGU>
        fprintf(fd,'%s\n',jsonencode(value,PrettyPrint=true));
    end
    function [trace,out]=execute(cfg,steps,rows)
        if isempty(rows),rows=repmat(cfg',5,1);end
        mw=get_param(mdl,'ModelWorkspace');assignin(mw,'charge_cfg_v62',[(0:4)' rows]);assignin(mw,'charge_steps_v62',steps);
        out=sim(mdl,'StopTime','4','ReturnWorkspaceOutputs','on');x=out.charge_trace_v62.Data;
        trace=reshape(x,64,[])';assert(isequal(size(trace),[5 64]));
    end
end
function [cfg,steps]=adapt(c,z)
s=c.s;p=c.p;names={'REQUEST','NAMEPLATE','HOT_FLOW','SOURCE','TES_PORT'};ties=double(ismember(names,z.right_equivalent_limiters));
cfg=[c.E c.request p.eta_charge p.loss_rate_per_h p.heat_capacity_MWh_per_K p.ambient_C ...
    s.delivery_C s.direct_approach_K s.charge_approach_K s.condenser_approach_K s.source_in_C s.source_glide_K ...
    s.evaporator_approach_K s.cooling_factor s.hot_capacity_MW_per_K s.hp_capacity_MW s.source_capacity_MW_per_K ...
    p.charge_limit_MW s.tank_max_C s.aux_per_compressor c.age z.total_h 62 z.event_time_h_interval ties]';
hi=cfg(26);T=cfg(23);steps=[(0:4)' [0;1;2;2;2] [0;0;hi+.25*(T-hi);hi+.5*(T-hi);T]];
end
