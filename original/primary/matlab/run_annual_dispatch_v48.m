function run_annual_dispatch_v48(folder)
% Execute corrected full-year inventory trajectories and preserved saved v42.
root=fileparts(fileparts(mfilename('fullpath')));here=fullfile(root,'matlab','simulink');
addpath(fullfile(root,'matlab'),here);spec=jsondecode(fileread(fullfile(folder,'spec.json')));
checks=struct('name',{},'passed',{});base=default_config_v2();base.sim.hours=8760;
input=dchr.make_inputs(base);annual=[];
for j=1:numel(spec.boiler_caps_MW)
    cfg=base;cfg.backup.max_heat_MW=spec.boiler_caps_MW(j);id=sprintf('annual_cap_%g',cfg.backup.max_heat_MW);
    out=dchr.simulate_system_v48(cfg,input);legacy=dchr.simulate_system_v13(cfg,input);
    ports=dchr.adapt_dispatch_energy_v46(out,'explicit_actual_v45');
    m=dchr.compute_service_comparison_v46(cfg,ports);
    lm=dchr.compute_service_comparison_v46(cfg,dchr.adapt_dispatch_energy_v46(legacy,'legacy_actual_v13'));
    save(fullfile(folder,[id '.mat']),'cfg','input','out','legacy','ports','m','lm');
    writetable(out,fullfile(folder,[id '.csv']));writetable(legacy,fullfile(folder,[id '_legacy.csv']));
    writetable(ports,fullfile(folder,[id '_ports.csv']));
    record([id '_8760'],height(out)==8760&&m.energy.reported_period_h==8760);
    record([id '_source'],all(out.HP_Source_Used_MW<=out.HX_Heat_to_HP_MW+1e-10));
    record([id '_inventory'],all(out.Storage_E_Next_MWh>=0&out.Storage_E_Next_MWh<=cfg.storage.capacity_MWh+1e-10));
    record([id '_first_law'],max(abs(out.First_Law_Residual_MWh))<1e-10);
    record([id '_boiler'],all(out.Gas_Heat_MW<=cfg.backup.max_heat_MW));
    record([id '_unmet_reduction'],m.energy.unmet_heat_MWh<=lm.energy.unmet_heat_MWh+1e-8);
    item=struct('id',id,'cfg',cfg,'report',m,'legacy_report',lm, ...
        'initial_inventory_MWh',out.Storage_E_MWh(1),'terminal_inventory_MWh',out.Storage_E_Next_MWh(end));
    if isempty(annual),annual=item;else,annual(end+1)=item;end %#ok<AGROW>
    fprintf('ANNUAL_V48 %s delivered=%.16g unmet=%.16g HP=%.16g old_unmet=%.16g\n',id, ...
        m.energy.total_delivered_MWh,m.energy.unmet_heat_MWh,m.energy.hp_heat_MWh,lm.energy.unmet_heat_MWh);
end
record('boiler_unmet_monotone',all(diff(arrayfun(@(a)a.report.energy.unmet_heat_MWh,annual))<=0));
record('boiler_independent_HP',max(arrayfun(@(a)a.report.energy.hp_heat_MWh,annual))-min(arrayfun(@(a)a.report.energy.hp_heat_MWh,annual))<1e-9);
% Matched no-storage synthetic fixtures isolate HP/finite-backup differences.
fixtures=[];cases=spec.six_mode_cases;
for j=1:numel(spec.fixtures)
    f=spec.fixtures(j);cfg=base;cfg.backup.max_heat_MW=2;cfg.sim.hours=3;
    cfg.dc.recovery_fraction=1;cfg.dc.source_temp_C=35;cfg.hx.enabled=false;
    cfg.model.dh_temperature='fixed';cfg.hp.supply_temp_C=70;
    cfg.dh.base_hot_water_MW=f.demand_MW;cfg.dh.space_heat_design_MW=0;cfg.dh.network_efficiency=1;
    cfg.storage.capacity_MWh=0;cfg.storage.initial_soc=0;
    cfg.hp.part_load_penalty=f.penalty;cfg.hp.cop_min=f.cop_min;
    x=dchr.make_inputs(cfg);x.it_power_MW=repmat(f.source_MW,3,1);x.dc_total_power_MW=x.it_power_MW;
    out=dchr.simulate_system_v48(cfg,x);legacy=dchr.simulate_system_v13(cfg,x);
    save(fullfile(folder,[f.id '.mat']),'cfg','out','legacy','x');writetable(out,fullfile(folder,[f.id '.csv']));
    writetable(legacy,fullfile(folder,[f.id '_legacy.csv']));
    c=cases(1);c.id=f.id;c.p=[1 10 0 0 1 1 0 5 .2 20 2];
    c.h=[cfg.hp.max_heat_output_MW cfg.hp.carnot_efficiency cfg.hp.cop_min cfg.hp.cop_max f.penalty 0 4 0 0];
    c.initial_energy_MWh=5;c.inputs=repmat([f.source_MW 35 70 f.demand_MW 45],3,1);c.expected_mode=-1;
    cases(end+1)=c; %#ok<AGROW>
    fixtures=[fixtures;struct('id',f.id,'cfg',cfg)]; %#ok<AGROW>
    if f.penalty==0&&f.cop_min==2.2
        record([f.id '_zero_penalty_compatibility'],max(abs(out.HP_Heat_MW-legacy.HP_Heat_Used_MW))<1e-10);
    elseif f.cop_min==4.1
        record([f.id '_cutoff_distinction'],all(out.HP_Heat_MW==0)&&all(legacy.HP_Heat_Used_MW>0));
    end
end
% Preserve temporal coverage; this is a short actual Stateflow period, not a year.
c=cases(1);fields=fieldnames(spec.period);
for k=1:numel(fields),if isfield(c,fields{k}),c.(fields{k})=spec.period.(fields{k});end,end
c.expected_mode=-1;cases(end+1)=c;
work=fullfile(folder,'local_build');mkdir(work);
Simulink.fileGenControl('set','CacheFolder',fullfile(work,'cache'),'CodeGenFolder',fullfile(work,'codegen'),'createDir',true);
assert(license('test','Stateflow'),'Stateflow license unavailable');mdl='DCHR_Dispatch_Stateflow_v42';
load_system(fullfile(here,[mdl '.slx']));cleanup=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
rt=sfroot;ch=rt.find('-isa','Stateflow.Chart','Path',[mdl '/Execute_Segments/Thermal_Dispatch']);
metadata=struct('matlab_version',version,'products',ver,'stateflow_version',ver('Stateflow'), ...
    'stateflow_license_test',license('test','Stateflow'),'simulation_mode',get_param(mdl,'SimulationMode'), ...
    'thermal_states',{get(ch.find('-isa','Stateflow.State'),'Name')});
stateflow=[];allModes=[];
for j=1:numel(cases)
    c=cases(j);p=c.p(:)';h=c.h(:)';x=c.inputs;n=size(x,1);control=[8 0 0 64];clock=[1;0;0;0];
    if j==numel(cases),control=spec.period.c(:)';clock=spec.period.initial_clock(:);end
    s=Simulink.SimulationInput(mdl);names={'dt','stop','input','p','h','E0','c','m0'};
    values={p(1),(n-1)*p(1),[(0:n-1)'*p(1) x],p,h,c.initial_energy_MWh,control,clock};
    for k=1:numel(names),s=s.setVariable(['dchr_' names{k} '_v42'],values{k},'Workspace',mdl);end
    result=sim(s.setModelParameter('CaptureErrors','on'));save(fullfile(folder,[c.id '_simulation.mat']),'result');
    record([c.id '_executed'],isempty(result.ErrorMessage));assert(isempty(result.ErrorMessage),'%s',result.ErrorMessage);
    dispatch=samples(result.dispatch_trace_v42,25);raw=samples(result.segment_trace_v42,1792);segments=[];
    for i=1:n
        z=reshape(raw(i,:),28,64)';positive=find(z(:,2)>0);
        segments=[segments;[repmat(i,numel(positive),1) positive z(positive,:)]]; %#ok<AGROW>
    end
    record([c.id '_first_law'],max(abs(dispatch(:,13)))<1e-10);
    record([c.id '_soc'],all(dispatch(:,8)>=0&dispatch(:,8)<=p(2)));
    if c.expected_mode>=0,record([c.id '_mode'],dispatch(1)==c.expected_mode);end
    if j>6&&j<numel(cases)
        a=load(fullfile(folder,[c.id '.mat']),'out');out=a.out;
        record([c.id '_matched_annual_ports'],max(abs(dispatch(:,[19 20 21 2 5 6])- ...
            [out.HP_Heat_MW out.HP_Electric_MW out.HP_Source_Used_MW out.HP_Direct_MW out.Gas_Heat_MW out.Unmet_Heat_MW]),[],'all')<1e-10);
    end
    if j==numel(cases),record('period_six_modes_transitions',isequal(unique(segments(:,3)),(0:5)')&&sum(diff(segments(:,3))~=0)>=6);end
    allModes=[allModes;segments(:,3)]; %#ok<AGROW>
    writematrix(dispatch,fullfile(folder,[c.id '_dispatch.csv']));writematrix(segments,fullfile(folder,[c.id '_segments.csv']));
    item=struct('id',c.id,'case',c,'intervals',n,'error_message',result.ErrorMessage);
    if isempty(stateflow),stateflow=item;else,stateflow(end+1)=item;end %#ok<AGROW>
end
record('saved_actual_six_modes',isequal(unique(allModes),(0:5)'));
faults=[];cfg=base;cfg.backup.max_heat_MW=2;x=input;
for j=1:12
    cc=cfg;xx=x;
    switch j
        case 1,cc.sim.dt_h=0;
        case 2,cc.storage.eta_charge=0;
        case 3,cc.storage.eta_discharge=1.1;
        case 4,cc.storage.loss_fraction_per_h=2;
        case 5,cc.storage.charge_limit_MW=-1;
        case 6,cc.storage.initial_soc=2;
        case 7,cc.backup.max_heat_MW=NaN;
        case 8,xx.it_power_MW(1)=-1;
        case 9,xx.outdoor_temp_C(1)=NaN;
        case 10,xx.time(2)=xx.time(1);
        case 11,cc.hp.part_load_penalty=1;
        case 12,cc.hx.effectiveness=2;
    end
    identifier='';message='';try,dchr.simulate_system_v48(cc,xx);catch err,identifier=err.identifier;message=err.message;end
    z=struct('index',j,'rejected',~isempty(identifier),'error_id',identifier,'message',message);
    if isempty(faults),faults=z;else,faults(end+1)=z;end %#ok<AGROW>
    record(sprintf('annual_fault_%d',j),z.rejected);
end
summary=struct('version','0.48','model_version','0.42','new_model',false, ...
    'annual_intervals',8760*numel(annual),'saved_intervals',sum([stateflow.intervals]), ...
    'harness_passed',sum([checks.passed]),'harness_failed',sum(~[checks.passed]));
report=struct('metadata',metadata,'annual',annual,'fixtures',fixtures,'stateflow',stateflow, ...
    'faults',faults,'assertions',checks,'summary',summary);
save(fullfile(folder,'annual_dispatch_v48.mat'),'report','spec');writejson(fullfile(folder,'annual_dispatch_v48.json'),report);
fprintf('ANNUAL_DISPATCH_V48 pass=%d fail=%d annual_intervals=%d saved_intervals=%d\n', ...
    summary.harness_passed,summary.harness_failed,summary.annual_intervals,summary.saved_intervals);
assert(all([checks.passed]),'DCHR:v48:Failure','Inspect retained evidence.');
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
