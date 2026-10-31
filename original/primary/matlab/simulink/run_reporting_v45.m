function run_reporting_v45(folder)
% Fresh saved-v42 six-mode execution plus additive reporting-boundary QA.
here=fileparts(mfilename('fullpath'));root=fileparts(fileparts(here));addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});
snap=fullfile(folder,'source_snapshot');mkdir(snap);
for pattern={'*v42.m','DCHR_Dispatch_Stateflow_v42.slx','stateflow_time_tolerance_v36.m','*reporting_v45.m'}
    files=dir(fullfile(here,pattern{1}));for k=1:numel(files),copyfile(fullfile(files(k).folder,files(k).name),snap);end
end
for name={'compute_energy_metrics_v45.m','compute_metrics.m','compute_metrics_v2.m','simulate_dispatch_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr',name{1}),snap);
end
for name={'heat_pump_step_v40.m','heat_pump_step_v14.m','storage_step_v30.m','storage_kernel_v30.m','storage_parameters_v30.m'}
    copyfile(fullfile(root,'matlab','+dchr','+components',name{1}),snap);
end
copyfile(fullfile(folder,'spec.json'),snap);copyfile(fullfile(root,'matlab','default_config.m'),snap);
copyfile(fullfile(root,'matlab','default_config_v2.m'),snap);
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');
mdl='DCHR_Dispatch_Stateflow_v42';load_system(fullfile(here,[mdl '.slx']));
cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
ch=sfroot;chart=ch.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
metadata=struct('matlab_version',version,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'thermal_states',{get(chart.find('-isa','Stateflow.State'),'Name')});
items=[];traces=[];
for j=1:numel(spec.cases)
    c=spec.cases(j);p=c.p(:)';h=c.h(:)';x=c.inputs(:)';s=Simulink.SimulationInput(mdl);
    names={'dt','stop','input','p','h','E0','c','m0'};
    vals={p(1),0,[0 x],p,h,c.initial_energy_MWh,[8 0 0 64],[1;0;0;0]};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],vals{k},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[c.id '_simulation.mat']),'result');
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),'%s',result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);
    segments=reshape(raw(1,:),28,64)';ports=dispatch(:,[18 2 3 4 5 6 19 20]);
    cfg=referencecfg(p,h,c.initial_energy_MWh);out=array2table(ports,'VariableNames',spec.port_columns);
    m=dchr.compute_energy_metrics_v45(cfg,out);
    input=array2table(x([1 2 3 4 5]),'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW','Delivery_C'});
    ref=dchr.simulate_dispatch_v30(cfg,input);reference=table2array(ref(:,1:26));
    % v42 zeros the supervisor request while OFF; v30 records requested demand.
    % Compare every physical port/state and operating COP, not that policy diagnostic.
    record([c.id '_verified_reference'],max(abs(dispatch(:,[1:21 24:25])-reference(:,[1:21 24:25])),[],'all')<1e-10);
    record([c.id '_reference_COP'],isequaln(dispatch(23),reference(23))||abs(dispatch(23)-reference(23))<1e-10);
    record([c.id '_mode'],dispatch(1)==c.expected_mode);
    record([c.id '_first_law'],abs(dispatch(13))<1e-10);
    record([c.id '_soc'],dispatch(8)>=0&&dispatch(8)<=p(2));
    record([c.id '_delivered'],abs(m.nonboiler_delivered_MWh-(dispatch(2)+dispatch(4))*p(1))<1e-11);
    old=legacy(cfg,out,x(1));
    item=struct('id',c.id,'ports',ports,'dt_h',p(1),'report',m,'legacy',old, ...
        'dispatch',dispatch,'segments',segments,'reference',reference,'error_message',result.ErrorMessage);
    if isempty(items),items=item;else,items(end+1)=item;end %#ok<AGROW>
    traces=[traces;[j dispatch]]; %#ok<AGROW>
    fprintf('FRESH_SAVED_V42 id=%s mode=%d nonboiler_MWh=%.16g unmet_MWh=%.16g legacy_MWh=%.16g\n', ...
        c.id,dispatch(1),m.nonboiler_delivered_MWh,m.unmet_heat_MWh,old.v2.reused_to_network_MWh);
end
record('all_six_actual_modes',isequal(sort(traces(:,2)),(0:5)'));
record('legacy_unmet_credit_reproduced',items(6).legacy.v2.reused_to_network_MWh==3&&items(6).report.nonboiler_delivered_MWh==0);
vectors=[];
for j=1:numel(spec.reporting_vectors)
    z=spec.reporting_vectors(j);cfg.sim.dt_h=z.dt(:);out=array2table(z.ports,'VariableNames',spec.port_columns);
    m=dchr.compute_energy_metrics_v45(cfg,out);old=[];
    if j==1
        cfg.sim.dt_h=1;old=legacy(cfg,out,10);
        record('integrated_cop_two_intervals',abs(m.hp_heating_COP_integrated-12/5)<1e-14);
        record('diagnostic_cop_two_intervals',abs(m.hp_heat_weighted_COP_diagnostic-8/3)<1e-14);
        record('legacy_mean_cop_is_diagnostic',abs(old.v2.mean_cop-8/3)<1e-14);
    elseif j==2
        record('unequal_duration_ratio',abs(m.hp_heating_COP_integrated-68/33)<1e-14);
    elseif j==3
        record('inventory_is_not_hp_cop',isnan(m.hp_heating_COP_integrated)&&m.nonboiler_delivered_MWh==3);
    else
        record('zero_denominators_undefined',isnan(m.hp_heating_COP_integrated)&&isnan(m.nonboiler_coverage_fraction));
    end
    z.report=m;z.legacy=old;
    if isempty(vectors),vectors=z;else,vectors(end+1)=z;end %#ok<AGROW>
end
% Domain faults exercise the new reporting boundary, not inherited controller gates.
base=array2table(spec.reporting_vectors(1).ports,'VariableNames',spec.port_columns);cfg.sim.dt_h=1;faults=[];
for j=1:12
    bad=base;cc=cfg;
    switch j
        case 1,bad.Unmet_Heat_MW(1)=NaN;
        case 2,bad.Storage_Discharge_MW(1)=-1;
        case 3,bad.Heat_Demand_MW(1)=5;
        case 4,bad.HP_Heat_MW(1)=5;
        case 5,bad.HP_Electric_MW(1)=0;
        case 6,bad.HP_Electric_MW(1)=5;
        case 7,bad.Unmet_Heat_MW=[];
        case 8,cc.sim.dt_h=0;
        case 9,cc.sim.dt_h=[1 1 1];
        case 10,bad.HP_Heat_MW(1)=Inf;
        case 11,cc.sim.dt_h=realmax;
        case 12,bad=bad([],:);
    end
    id='';msg='';try,dchr.compute_energy_metrics_v45(cc,bad);catch err,id=err.identifier;msg=err.message;end
    z=struct('index',j,'rejected',~isempty(id),'error_id',id,'message',msg);
    if isempty(faults),faults=z;else,faults(end+1)=z;end %#ok<AGROW>
    record(sprintf('report_domain_fault_%d',j),z.rejected);
end
summary=struct('version','0.45','model_version','0.42','new_model',false, ...
    'fresh_saved_model_scenarios',numel(items),'six_modes_executed',true, ...
    'reporting_vectors',numel(vectors),'runtime_reporting_rejections',sum([faults.rejected]), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]));
report=struct('metadata',metadata,'cases',items,'vectors',vectors,'faults',faults,'assertions',checks,'summary',summary);
save(fullfile(folder,'reporting_v45.mat'),'report','spec');
writejson(fullfile(folder,'reporting_v45.json'),report);
writematrix(traces,fullfile(folder,'stateflow_numeric_trace_v45.csv'));
fprintf('REPORTING_V45 scenarios=%d passed=%d failed=%d\n',numel(items),summary.harness_passed,summary.harness_failed);
assert(all([checks.passed]),'DCHR:v45:Failure','Inspect retained evidence.');
    function record(name,ok),checks(end+1)=struct('name',name,'passed',logical(ok));end
end
function cfg=referencecfg(p,h,E)
cfg=default_config_v2();cfg.sim.dt_h=p(1);cfg.backup.max_heat_MW=p(11);
cfg.storage.heat_capacity_MWh_per_K=p(9);cfg.storage.ambient_C=p(10);
cfg.storage.max_temperature_C=p(10)+p(2)/p(9);cfg.storage.delivery_cutoff_C=p(10)+p(8)/p(9);
cfg.storage.initial_temperature_C=p(10)+E/p(9);cfg.storage.charge_limit_MW=p(3);cfg.storage.discharge_limit_MW=p(4);
cfg.storage.eta_charge=p(5);cfg.storage.eta_discharge=p(6);cfg.storage.continuous_loss_rate_per_h=p(7);
cfg.hp.max_heat_output_MW=h(1);cfg.hp.carnot_efficiency=h(2);cfg.hp.cop_min=h(3);cfg.hp.cop_max=h(4);
cfg.hp.part_load_penalty=h(5);cfg.hp.poly_c0=h(7);cfg.hp.poly_c1=h(8);cfg.hp.poly_c2=h(9);cfg.model.hp_backend='lift_polynomial';
end
function old=legacy(cfg,out,source)
n=height(out);out.HP_Heat_Used_MW=out.HP_Heat_MW;out.COP=NaN(n,1);active=out.HP_Electric_MW>0;
out.COP(active)=out.HP_Heat_MW(active)./out.HP_Electric_MW(active);
out.Curtailed_HP_Heat_MW=zeros(n,1);out.IT_MW=10*ones(n,1);out.DC_Total_MW=12*ones(n,1);
out.Source_Heat_Available_MW=source*ones(n,1);out.HX_Heat_to_HP_MW=out.Source_Heat_Available_MW;
out.Useful_Heat_Exergy_MW=zeros(n,1);out.Temperature_Lift_K=40*ones(n,1);
old=struct('v1',dchr.compute_metrics(cfg,out),'v2',dchr.compute_metrics_v2(cfg,out));
end
function v=samples(ts,width)
n=numel(ts.Time);raw=ts.Data;if ismatrix(raw)&&isequal(size(raw),[n width]),v=raw;
elseif numel(raw)==n*width,v=reshape(raw,width,n)';else,error('Unexpected trace dimensions.');end
end
function writejson(path,v)
assert(~isfile(path));fid=fopen(path,'w');assert(fid>0);clean=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(v,PrettyPrint=true));
end
