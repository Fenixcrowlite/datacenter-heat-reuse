function run_period_experiment_v46(folder)
% Additive reporting pipeline; finite-backup annual reference and saved v42.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');addpath(fullfile(root,'matlab'),here);
spec=jsondecode(fileread(fullfile(folder,'spec.json')));checks=struct('name',{},'passed',{});
snap=fullfile(folder,'source_snapshot');mkdir(snap);files=dir(fullfile(root,'matlab','**','*.m'));
for k=1:numel(files)
    path=fullfile(files(k).folder,files(k).name);relative=path(numel(root)+2:end);target=fullfile(snap,relative);
    if ~isfolder(fileparts(target)),mkdir(fileparts(target));end
    copyfile(path,target);
end
copyfile(fullfile(here,'DCHR_Dispatch_Stateflow_v42.slx'),fullfile(snap,'matlab','simulink'));
copyfile(fullfile(folder,'spec.json'),snap);
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');mdl='DCHR_Dispatch_Stateflow_v42';
load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
metadata=struct('matlab_version',version,'products',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'thermal_states',{get(ch.find('-isa','Stateflow.State'),'Name')});
cases=spec.six_mode_cases;periodCase=cases(1);fields=fieldnames(spec.period);
for k=1:numel(fields),if isfield(periodCase,fields{k}),periodCase.(fields{k})=spec.period.(fields{k});end,end
periodCase.expected_mode=-1;cases(end+1)=periodCase;
% The added period has a different shape than six single-interval fixtures.
stateflow=[];allModes=[];
for j=1:numel(cases)
    c=cases(j);isPeriod=j==numel(cases);p=c.p(:)';h=c.h(:)';x=c.inputs;n=size(x,1);
    control=[8 0 0 64];initialClock=[1;0;0;0];
    if isPeriod,control=spec.period.c(:)';initialClock=spec.period.initial_clock(:);end
    s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
    values={p(1),(n-1)*p(1),[(0:n-1)'*p(1) x],p,h,c.initial_energy_MWh,control,initialClock};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[c.id '_simulation.mat']),'result');
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),'%s',result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);segments=[];
    for i=1:n
        z=reshape(raw(i,:),28,64)';positive=find(z(:,2)>0);
        segments=[segments;[repmat(i,numel(positive),1) positive z(positive,:)]]; %#ok<AGROW>
    end
    ports=array2table(dispatch(:,[18 2 3 4 5 6 19 20]),'VariableNames',spec.port_columns);
    ports=dchr.adapt_dispatch_energy_v46(ports,'explicit_actual_v45');cfg=default_config_v2();cfg.sim.dt_h=p(1);
    m=dchr.compute_service_comparison_v46(cfg,ports);
    record([c.id '_samples'],size(dispatch,1)==n);
    record([c.id '_first_law'],max(abs(dispatch(:,13)))<1e-10);
    record([c.id '_soc'],all(dispatch(:,8)>=0&dispatch(:,8)<=p(2)));
    record([c.id '_service'],abs(m.energy.heat_demand_MWh-m.energy.total_delivered_MWh-m.energy.unmet_heat_MWh)<1e-10);
    if ~isPeriod,record([c.id '_mode'],dispatch(1)==c.expected_mode);
    else
        record('period_actual_transitions',sum(diff(segments(:,3))~=0)>=6);
        record('period_six_modes',isequal(unique(segments(:,3)),(0:5)'));
    end
    allModes=[allModes;segments(:,3)]; %#ok<AGROW>
    writetable(ports,fullfile(folder,[c.id '_ports.csv']));writematrix(dispatch,fullfile(folder,[c.id '_dispatch.csv']));
    writematrix(segments,fullfile(folder,[c.id '_segments.csv']));
    item=struct('id',c.id,'intervals',n,'dt_h',p(1),'p',p,'h',h,'inputs',x, ...
        'initial_energy_MWh',c.initial_energy_MWh,'report',m,'error_message',result.ErrorMessage);
    if isempty(stateflow),stateflow=item;else,stateflow(end+1)=item;end %#ok<AGROW>
    fprintf('FRESH_SAVED_V42 id=%s intervals=%d unmet_MWh=%.16g delivered_MWh=%.16g\n',c.id,n,m.energy.unmet_heat_MWh,m.energy.total_delivered_MWh);
end
record('actual_all_six_modes',isequal(unique(allModes),(0:5)'));
% Annual v13 retains its older lumped TES/HP assumptions, unlike saved v42.
annual=[];base=default_config_v2();base.sim.hours=spec.annual_hours;input=dchr.make_inputs(base);
for j=1:numel(spec.annual_boiler_caps_MW)
    cfg=base;cfg.backup.max_heat_MW=spec.annual_boiler_caps_MW(j);id=sprintf('annual_v13_cap_%g',cfg.backup.max_heat_MW);
    out=dchr.simulate_system_v13(cfg,input);ports=dchr.adapt_dispatch_energy_v46(out,'legacy_actual_v13');
    m=dchr.compute_service_comparison_v46(cfg,ports);old=dchr.compute_metrics_v2(cfg,out);
    save(fullfile(folder,[id '_reference.mat']),'out','ports','cfg','input','m','old');
    writetable(out,fullfile(folder,[id '_legacy.csv']));writetable(ports,fullfile(folder,[id '_ports.csv']));
    record([id '_8760_explicit_hours'],height(out)==8760&&m.energy.reported_period_h==8760);
    record([id '_boiler_limit'],all(out.Gas_Heat_MW<=cfg.backup.max_heat_MW));
    record([id '_legacy_unmet_credit'],abs(old.reused_to_network_MWh-m.energy.nonboiler_delivered_MWh-m.energy.unmet_heat_MWh)<1e-7);
    record([id '_full_demand_opex_credit'],abs(old.opex_saving_EUR-m.equal_delivered_service_opex_difference_EUR-m.unmet_baseline_opex_credit_EUR)<1e-6);
    record([id '_full_demand_CO2_credit'],abs(old.CO2_saving_t-m.equal_delivered_service_CO2_difference_t-m.unmet_baseline_CO2_credit_t)<1e-8);
    item=struct('id',id,'boiler_cap_MW',cfg.backup.max_heat_MW,'report',m,'legacy_report',old);
    if isempty(annual),annual=item;else,annual(end+1)=item;end %#ok<AGROW>
    fprintf('FINITE_BACKUP_ANNUAL id=%s hours=%.0f unmet_MWh=%.16g integrated_COP=%.16g\n', ...
        id,m.energy.reported_period_h,m.energy.unmet_heat_MWh,m.energy.hp_heating_COP_integrated);
end
record('annual_unmet_monotone',all(diff(arrayfun(@(a)a.report.energy.unmet_heat_MWh,annual))<=0));
record('annual_nonboiler_cap_independent',max(arrayfun(@(a)a.report.energy.nonboiler_delivered_MWh,annual))-min(arrayfun(@(a)a.report.energy.nonboiler_delivered_MWh,annual))<1e-8);
% Deliberately different potential/actual heat and unequal duration trap.
v=spec.reporting_fixture;out=array2table(v.legacy_rows,'VariableNames', ...
    {'Heat_Demand_MW','HP_Heat_Used_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW','HP_Heat_MW','HP_Electric_MW'});
cfg=base;cfg.sim.dt_h=v.dt_h(:);ports=dchr.adapt_dispatch_energy_v46(out,'legacy_actual_v13');fixture=dchr.compute_service_comparison_v46(cfg,ports);
record('actual_potential_schema_trap',fixture.energy.hp_heat_MWh==17&&abs(fixture.energy.hp_heating_COP_integrated-68/33)<1e-14);
record('adapter_input_preserved',isequal(out.HP_Heat_MW,[40;80]));
faults=[];
for j=1:12
    bad=out;cc=cfg;schema='legacy_actual_v13';
    switch j
        case 1,bad.Unmet_Heat_MW=[];
        case 2,bad.HP_Heat_Used_MW=[];
        case 3,schema='automatic';
        case 4,bad.Storage_Charge_MW(1)=5;
        case 5,cc.backup.gas_boiler_efficiency=0;
        case 6,cc.backup.gas_boiler_efficiency=1.1;
        case 7,cc.econ.gas_EUR_per_MWh_fuel=-1;
        case 8,cc.econ.grid_tCO2_per_MWh=NaN;
        case 9,cc.econ.electricity_EUR_per_MWh=Inf;
        case 10,bad.Heat_Demand_MW(1)=5;
        case 11,cc.sim.dt_h=[1;1;1];
        case 12,cc.econ.gas_EUR_per_MWh_fuel=realmax;
    end
    identifier='';message='';try,q=dchr.adapt_dispatch_energy_v46(bad,schema);dchr.compute_service_comparison_v46(cc,q);catch err,identifier=err.identifier;message=err.message;end
    z=struct('index',j,'rejected',~isempty(identifier),'error_id',identifier,'message',message);
    if isempty(faults),faults=z;else,faults(end+1)=z;end %#ok<AGROW>
    record(sprintf('report_fault_%d',j),z.rejected);
end
summary=struct('version','0.46','model_version','0.42','new_model',false,'saved_model_scenarios',numel(stateflow), ...
    'saved_model_intervals',sum([stateflow.intervals]),'annual_reference_scenarios',numel(annual), ...
    'annual_reference_intervals',8760*numel(annual),'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]), ...
    'report_domain_rejections',sum([faults.rejected]));
report=struct('metadata',metadata,'stateflow',stateflow,'annual',annual,'fixture',fixture,'faults',faults,'assertions',checks,'summary',summary);
save(fullfile(folder,'period_v46.mat'),'report','spec');writejson(fullfile(folder,'period_v46.json'),report);
fprintf('PERIOD_V46 passed=%d failed=%d saved_intervals=%d annual_intervals=%d\n',summary.harness_passed,summary.harness_failed,summary.saved_model_intervals,summary.annual_reference_intervals);
assert(all([checks.passed]),'DCHR:v46:Failure','Inspect retained evidence.');
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
