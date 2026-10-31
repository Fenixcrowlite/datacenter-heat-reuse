function run_hp_annual_audit_v47(folder)
% Fresh annual v13 and saved-v42 executions; do not modify accepted models.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);spec=jsondecode(fileread(fullfile(folder,'spec.json')));
checks=struct('name',{},'passed',{});cfg=default_config_v2();
cfg.sim.hours=spec.annual_hours;cfg.backup.max_heat_MW=spec.annual_boiler_cap_MW;
input=dchr.make_inputs(cfg);out=dchr.simulate_system_v13(cfg,input);
src=dchr.components.dc_source(input.it_power_MW,cfg);
hx=dchr.components.heat_exchanger(src.heat_MW,src.temperature_C,cfg);
legacy=dchr.components.heat_pump(hx.heat_to_hp_MW,hx.evaporator_source_C,out.DH_Supply_C,cfg);
% Compare the SAME chosen HP output/request to its source-feasible maximum.
% Separately compare unlimited HP capability; neither is a redispatched year.
request=out.Heat_Demand_MW+min(cfg.storage.charge_limit_MW, ...
    max(0,cfg.storage.capacity_MWh-out.Storage_E_MWh*(1-cfg.storage.loss_fraction_per_h*cfg.sim.dt_h))/(cfg.storage.eta_charge*cfg.sim.dt_h));
optimal=zeros(height(out),4);
for i=1:height(out)
    hp=dchr.components.heat_pump_step_v40(hx.heat_to_hp_MW(i),hx.evaporator_source_C(i),out.DH_Supply_C(i),request(i),cfg);
    optimal(i,:)=[request(i) hp.heat_output_MW hp.electric_MW hp.source_used_MW];
end
audit=array2table([hx.evaporator_source_C legacy.cop_nominal optimal], ...
    'VariableNames',{'HP_Source_C','COP_Nominal','Request_MW','Verified_Max_Heat_MW','Verified_Electric_MW','Verified_Source_MW'});
writetable(out,fullfile(folder,'annual_legacy.csv'));writetable(audit,fullfile(folder,'annual_capability.csv'));
save(fullfile(folder,'annual_v47.mat'),'cfg','input','out','audit');
record('annual_8760',height(out)==8760);
record('annual_source_feasible',all(out.HP_Source_Used_MW<=out.HX_Heat_to_HP_MW+1e-10));
record('annual_service_closed',max(abs(out.HP_Heat_Used_MW-out.Storage_Charge_MW+out.Storage_Discharge_MW+out.Gas_Heat_MW+out.Unmet_Heat_MW-out.Heat_Demand_MW))<1e-10);
record('annual_capability_nonmaximal_reproduced',any(optimal(:,2)-out.HP_Heat_Used_MW>1e-5));
% Component grid avoids lower-COP clipping, for matched legacy/new laws.
probes=[];
for penalty=spec.probe_penalties(:)'
    cc=cfg;cc.hp.part_load_penalty=penalty;
    for source=spec.probe_sources_MW(:)'
        for req=spec.probe_requests_MW(:)'
            old=dchr.components.heat_pump(source,spec.source_C,spec.sink_C,cc);
            q=min(old.heat_potential_MW,req);cop=dchr.components.part_load_cop(old.cop_nominal,q,cc);
            hp=dchr.components.heat_pump_step_v40(source,spec.source_C,spec.sink_C,req,cc);
            probes=[probes;source req penalty old.cop_nominal q cop q/cop max(0,q-q/cop) hp.heat_output_MW hp.electric_MW hp.source_used_MW]; %#ok<AGROW>
            record(sprintf('probe_%d_source',size(probes,1)),q-q/cop<=source+1e-10&&hp.source_used_MW<=source+1e-10);
            record(sprintf('probe_%d_monotone',size(probes,1)),hp.heat_output_MW>=q-1e-10);
        end
    end
end
probeTable=array2table(probes,'VariableNames',{'Source_MW','Request_MW','Penalty','Nominal_COP','Legacy_Heat_MW','Legacy_COP','Legacy_Electric_MW','Legacy_Source_MW','Verified_Heat_MW','Verified_Electric_MW','Verified_Source_MW'});
writetable(probeTable,fullfile(folder,'hp_probes.csv'));
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');mdl='DCHR_Dispatch_Stateflow_v42';
load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
metadata=struct('matlab_version',version,'products',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'thermal_states',{get(ch.find('-isa','Stateflow.State'),'Name')});
cases=spec.six_mode_cases;
for i=1:numel(spec.source_comparison_MW)
    c=cases(1);c.id=sprintf('source_limited_%g',spec.source_comparison_MW(i));
    c.p=[1 10 0 0 1 1 0 5 .2 20 2];
    c.h=[cfg.hp.max_heat_output_MW cfg.hp.carnot_efficiency cfg.hp.cop_min cfg.hp.cop_max cfg.hp.part_load_penalty 0 4 0 0];
    c.initial_energy_MWh=5;c.inputs=[spec.source_comparison_MW(i) spec.source_C spec.sink_C spec.request_MW 45];c.expected_mode=5;
    cases(end+1)=c; %#ok<AGROW>
end
items=[];allModes=[];
for j=1:numel(cases)
    c=cases(j);p=c.p(:)';h=c.h(:)';x=c.inputs;n=size(x,1);
    s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
    values={p(1),(n-1)*p(1),[(0:n-1)'*p(1) x],p,h,c.initial_energy_MWh,[8 0 0 64],[1;0;0;0]};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[c.id '_simulation.mat']),'result');
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),'%s',result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);segments=[];
    for i=1:n
        z=reshape(raw(i,:),28,64)';positive=find(z(:,2)>0);
        segments=[segments;[repmat(i,numel(positive),1) positive z(positive,:)]]; %#ok<AGROW>
    end
    record([c.id '_mode'],dispatch(1)==c.expected_mode);
    record([c.id '_first_law'],max(abs(dispatch(:,13)))<1e-10);
    record([c.id '_soc'],all(dispatch(:,8)>=0&dispatch(:,8)<=p(2)));
    record([c.id '_source'],all(dispatch(:,21)<=x(:,1)+1e-10));
    if j>6
        hp=dchr.components.heat_pump_step_v40(x(1),x(2),x(3),x(4),cfg);
        record([c.id '_verified_component'],abs(dispatch(19)-hp.heat_output_MW)<1e-10);
        old=dchr.components.heat_pump(x(1),x(2),x(3),cfg);
        record([c.id '_legacy_deficit_reproduced'],dispatch(19)>old.heat_potential_MW+1e-5);
    end
    allModes=[allModes;segments(:,3)]; %#ok<AGROW>
    writematrix(dispatch,fullfile(folder,[c.id '_dispatch.csv']));writematrix(segments,fullfile(folder,[c.id '_segments.csv']));
    item=struct('id',c.id,'intervals',n,'case',c,'error_message',result.ErrorMessage);
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
end
record('saved_actual_six_modes',isequal(unique(allModes),(0:5)'));
summary=struct('version','0.47','model_version','0.42','new_model',false,'saved_scenarios',numel(cases), ...
    'saved_intervals',sum([items.intervals]),'annual_intervals',height(out),'component_probes',size(probes,1), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]), ...
    'source_feasibility_violations',sum(out.HP_Source_Used_MW>out.HX_Heat_to_HP_MW+1e-10), ...
    'nonmaximal_intervals',sum(optimal(:,2)-out.HP_Heat_Used_MW>1e-8), ...
    'static_extra_heat_MWh',sum(max(0,optimal(:,2)-out.HP_Heat_Used_MW))*cfg.sim.dt_h);
report=struct('metadata',metadata,'cfg',cfg,'stateflow',items,'assertions',checks,'summary',summary);
save(fullfile(folder,'hp_annual_v47.mat'),'report','spec','probeTable');writejson(fullfile(folder,'hp_annual_v47.json'),report);
fprintf('HP_ANNUAL_V47 pass=%d fail=%d source_violations=%d nonmaximal=%d static_extra_MWh=%.16g\n',summary.harness_passed,summary.harness_failed,summary.source_feasibility_violations,summary.nonmaximal_intervals,summary.static_extra_heat_MWh);
assert(all([checks.passed]),'DCHR:v47:Failure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected trace dimensions.');end
end
function writejson(path,value)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(value,PrettyPrint=true));
end
