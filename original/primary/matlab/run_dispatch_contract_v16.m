function results = run_dispatch_contract_v16(referenceFile, outputDir)
%RUN_DISPATCH_CONTRACT_V16 Independent sequential reference vs MATLAB kernel.
assert(isfile(referenceFile),'DCHR:v16:MissingReference','Reference CSV is absent.');
if ~isfolder(outputDir), mkdir(outputDir); end
files={'matlab_dispatch_trace_v16.csv','matlab_dispatch_contract_v16.csv', ...
    'matlab_dispatch_contract_v16.json'};
for j=1:numel(files)
    assert(~isfile(fullfile(outputDir,files{j})),'DCHR:v16:EvidenceExists', ...
        'Refusing to replace evidence %s.',files{j});
end
v=readtable(referenceFile,'TextType','string');
ids=unique(v.scenario_id,'stable'); actual=cell(numel(ids),1);
for j=1:numel(ids)
    r=v(v.scenario_id==ids(j),:); first=r(1,:);
    assert(isequal(r.step,(1:height(r))'),'Invalid sequence step order.');
    c=default_config_v2();
    c.sim.dt_h=first.dt_h;
    c.storage.capacity_MWh=first.storage_capacity_MWh;
    c.storage.charge_limit_MW=first.charge_limit_MW;
    c.storage.discharge_limit_MW=first.discharge_limit_MW;
    c.storage.eta_charge=first.eta_charge; c.storage.eta_discharge=first.eta_discharge;
    c.storage.loss_fraction_per_h=first.loss_fraction_per_h;
    c.storage.initial_soc=0;
    if c.storage.capacity_MWh>0
        c.storage.initial_soc=first.expected_Storage_E_Start_MWh/c.storage.capacity_MWh;
    end
    c.backup.max_heat_MW=first.boiler_capacity_MW;
    c.hp.max_heat_output_MW=first.hp_capacity_MW;
    c.hp.carnot_efficiency=first.carnot_efficiency;
    c.hp.cop_min=first.cop_min; c.hp.cop_max=first.cop_max;
    c.hp.part_load_penalty=first.part_load_penalty;
    c.model.hp_backend=first.backend;
    c.hp.poly_c0=first.poly_c0; c.hp.poly_c1=first.poly_c1; c.hp.poly_c2=first.poly_c2;
    o=dchr.simulate_dispatch_v16(c,r(:,{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'}));
    actual{j}=[r(:,{'scenario_id','step'}),o];
end
a=vertcat(actual{:});
assert(isequal(a.scenario_id,v.scenario_id) && isequal(a.step,v.step),'Reference row order differs.');
writetable(a,fullfile(outputDir,files{1}));
names=strings(0,1); passed=false(0,1); notes=strings(0,1); maxResidual=0;
expectedNames=v.Properties.VariableNames(startsWith(v.Properties.VariableNames,'expected_'));
for j=1:numel(expectedNames)
    expected=v.(expectedNames{j}); field=extractAfter(string(expectedNames{j}),9);
    observed=double(a.(field));
    bothNaN=isnan(expected) & isnan(observed); finite=isfinite(expected) & isfinite(observed);
    delta=abs(observed(finite)-expected(finite));
    localMax=max([0;delta]); maxResidual=max(maxResidual,localMax);
    record("python_sequence_match_"+field,all(bothNaN | finite) && ...
        all(delta<=1e-9+1e-11*abs(expected(finite))), ...
        sprintf('%d intervals; max absolute residual %.12g',height(v),localMax));
end
tol=1e-9; dt=v.dt_h;
record('heat_pump_first_law',all(abs(a.HP_Heat_MW-a.HP_Electric_MW-a.HP_Source_Used_MW)<tol), ...
    'Actual output uses HP v14 source-constrained operating COP.');
record('no_unallocated_hp_heat',all(abs(a.HP_Heat_MW-a.HP_Direct_MW-a.Storage_Charge_MW)<tol), ...
    'Condenser heat goes to current demand or feasible TES charging.');
record('demand_closure',all(abs(a.HP_Direct_MW+a.Storage_Discharge_MW+ ...
    a.Gas_Heat_MW+a.Unmet_Heat_MW-a.Heat_Demand_MW)<tol), ...
    'Finite boiler and explicitly unmet heat close the demand accounting.');
record('system_interval_energy_closure',all(abs(a.System_Balance_Residual_MWh)<tol), ...
    'Source + compressor + boiler + initial TES = supplied demand + final TES + all TES losses.');
storageResidual=a.Storage_E_Start_MWh+a.Storage_Charge_MW.*dt-a.Storage_Discharge_MW.*dt- ...
    a.Storage_E_Next_MWh-a.Storage_Standing_Loss_MWh-a.Storage_Charge_Loss_MWh-a.Storage_Discharge_Loss_MWh;
record('storage_port_energy_closure',all(abs(storageResidual)<tol),'Standing and conversion losses reported separately.');
record('source_hp_boiler_bounds',all(a.HP_Source_Used_MW>=0) && ...
    all(a.HP_Source_Used_MW<=a.Source_Heat_MW+tol) && all(a.HP_Heat_MW<=v.hp_capacity_MW+tol) && ...
    all(a.HP_Heat_MW<=a.HP_Request_MW+tol) && all(a.Gas_Heat_MW<=v.boiler_capacity_MW+tol), ...
    'All upstream, rated and backup heat limits respected.');
record('storage_state_power_bounds',all(a.Storage_E_Next_MWh>=0) && ...
    all(a.Storage_E_Next_MWh<=v.storage_capacity_MWh+tol) && ...
    all(a.Storage_Charge_MW<=v.charge_limit_MW+tol) && ...
    all(a.Storage_Discharge_MW<=v.discharge_limit_MW+tol) && ...
    all(a.Storage_Charge_MW>=0) && all(a.Storage_Discharge_MW>=0), ...
    'TES energy and both external-port power limits respected.');
record('storage_mutual_exclusivity',all(a.Storage_Charge_MW.*a.Storage_Discharge_MW==0), ...
    'One charging, discharging or idle action per interval.');
record('coverage_charge_discharge_unmet_off',any(a.Storage_Charge_MW>0) && ...
    any(a.Storage_Discharge_MW>0) && any(a.Unmet_Heat_MW>0) && any(~a.HP_Available) && ...
    any(a.Heat_Demand_MW==0 & a.Storage_Charge_MW>0), ...
    'Sequences actually exercise the declared dispatch branches.');
on=a.HP_Available; off=~on;
record('off_flows_undefined_cop',all(a.HP_Heat_MW(off)==0) && all(a.HP_Electric_MW(off)==0) && ...
    all(a.HP_Source_Used_MW(off)==0) && all(isnan(a.COP(off))), ...
    'No artificial COP at zero compressor work.');
carnot=(a.Sink_C+273.15)./(a.Sink_C-a.Source_C);
record('operating_cop_domain',all(a.COP(on)>=v.cop_min(on)-tol) && ...
    all(a.COP(on)<=carnot(on)+tol),'COP cutoff and reservoir Carnot bound respected.');

c=default_config_v2(); c.sim.dt_h=.5; c.storage.capacity_MWh=20;
c.storage.loss_fraction_per_h=.01; c.storage.eta_charge=.9; c.storage.eta_discharge=.8;
c.storage.charge_limit_MW=4; c.storage.discharge_limit_MW=3; c.backup.max_heat_MW=2;
s=dchr.components.storage_step_v16(10,4,0,c);
record('hand_charge_energy_and_losses',abs(s.energy_next_MWh-11.75)<tol && ...
    abs(s.standing_loss_MWh-.05)<tol && abs(s.charge_loss_MWh-.2)<tol, ...
    'Independent half-hour example: 9.95 + .9*4*.5 = 11.75 MWh.');
s=dchr.components.storage_step_v16(10,0,4,c);
record('hand_discharge_energy_and_losses',abs(s.energy_next_MWh-8.075)<tol && ...
    abs(s.discharge_loss_MWh-.375)<tol, ...
    'External discharge 3 MW removes 3*.5/.8 = 1.875 MWh.');
bad=c; bad.storage.charge_limit_MW=-2;
legacy=dchr.components.storage_step(10,5,0,bad);
record('legacy_negative_charge_defect_confirmed',legacy.charge_MW==-2 && legacy.energy_next_MWh<10, ...
    'Legacy component accepts negative external charging power.');
reject('reject_negative_charge_limit',@()dchr.components.storage_step_v16(10,5,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.discharge_limit_MW=-2;
legacy=dchr.components.storage_step(10,0,5,bad);
record('legacy_negative_discharge_defect_confirmed',legacy.discharge_MW==-2 && legacy.energy_next_MWh>10, ...
    'Legacy component produces a negative discharge and increases stored energy.');
reject('reject_negative_discharge_limit',@()dchr.components.storage_step_v16(10,0,5,bad),'DCHR:v16:StorageDomain');
reject('reject_overcapacity_state',@()dchr.components.storage_step_v16(21,0,0,c),'DCHR:v16:StorageDomain');
reject('reject_negative_state',@()dchr.components.storage_step_v16(-1,0,0,c),'DCHR:v16:StorageDomain');
reject('reject_both_storage_requests',@()dchr.components.storage_step_v16(10,1,1,c),'DCHR:v16:SimultaneousStorageRequests');
reject('reject_nan_state',@()dchr.components.storage_step_v16(NaN,0,0,c),'DCHR:v16:StorageDomain');
reject('reject_complex_state',@()dchr.components.storage_step_v16(1+1i,0,0,c),'DCHR:v16:StorageDomain');
reject('reject_vector_state',@()dchr.components.storage_step_v16([1;2],0,0,c),'DCHR:v16:StorageDomain');
bad=c; bad.sim.dt_h=0;
reject('reject_zero_dt',@()dchr.components.storage_step_v16(10,0,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.eta_charge=0;
reject('reject_zero_charge_efficiency',@()dchr.components.storage_step_v16(10,0,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.eta_discharge=1.01;
reject('reject_discharge_efficiency_above_one',@()dchr.components.storage_step_v16(10,0,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.loss_fraction_per_h=3;
reject('reject_loss_step_above_one',@()dchr.components.storage_step_v16(10,0,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.loss_fraction_per_h=-.01;
reject('reject_negative_loss',@()dchr.components.storage_step_v16(10,0,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.charge_limit_MW=Inf;
reject('reject_infinite_power_limit',@()dchr.components.storage_step_v16(10,0,0,bad),'DCHR:v16:StorageDomain');
bad=c; bad.storage.capacity_MWh=0;
reject('reject_nonzero_state_zero_capacity',@()dchr.components.storage_step_v16(1,0,0,bad),'DCHR:v16:StorageDomain');
s=dchr.components.storage_step_v16(0,5,0,bad);
record('zero_capacity_zero_flows',s.charge_MW==0 && s.energy_next_MWh==0,'Zero-capacity storage is an explicit supported scenario.');
input=table(5,35,70,8,'VariableNames',{'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'});
bad=c; bad.backup.max_heat_MW=Inf;
reject('reject_infinite_boiler',@()dchr.simulate_dispatch_v16(bad,input),'DCHR:v16:BoilerDomain');
bad=c; bad.storage.initial_soc=1.1;
reject('reject_invalid_initial_soc',@()dchr.simulate_dispatch_v16(bad,input),'DCHR:v16:StorageDomain');
badInput=input; badInput.Source_C=70;
reject('reject_zero_temperature_lift',@()dchr.simulate_dispatch_v16(c,badInput),'DCHR:v16:InputSeries');
badInput=input; badInput.Heat_Demand_MW=-1;
reject('reject_negative_demand',@()dchr.simulate_dispatch_v16(c,badInput),'DCHR:v16:InputSeries');
badInput=input; badInput.Source_Heat_MW=NaN;
reject('reject_nonfinite_source',@()dchr.simulate_dispatch_v16(c,badInput),'DCHR:v16:InputSeries');
reject('reject_missing_input_column',@()dchr.simulate_dispatch_v16(c,input(:,1:3)),'DCHR:v16:InputSeries');
reject('reject_empty_input',@()dchr.simulate_dispatch_v16(c,input([],:)),'DCHR:v16:InputSeries');
bad=c; bad.sim.dt_h=2; bad.storage.loss_fraction_per_h=.2;
one=dchr.components.storage_step_v16(10,0,0,bad); bad.sim.dt_h=1;
half=dchr.components.storage_step_v16(10,0,0,bad);
two=dchr.components.storage_step_v16(half.energy_next_MWh,0,0,bad);
record('linear_loss_time_partition_defect_exposed',abs(one.energy_next_MWh-6)<tol && ...
    abs(two.energy_next_MWh-6.4)<tol, ...
    'Positivity validation does not establish time-step invariance or continuous leakage accuracy.');

results=table(names,passed,notes,'VariableNames',{'Test','Passed','Observation'});
writetable(results,fullfile(outputDir,files{2}));
summary=struct('version','0.16','timestamp_utc',char(datetime('now','TimeZone','UTC', ...
    'Format',"yyyy-MM-dd'T'HH:mm:ssXXX")),'category','sequential_matlab_vs_independent_python', ...
    'matlab_version',version,'reference_file',char(referenceFile),'scenarios',numel(ids), ...
    'intervals',height(v),'total',height(results),'passed',sum(passed),'failed',sum(~passed), ...
    'max_absolute_residual',maxResidual,'primary_paper_replication',false, ...
    'equipment_validation',false,'annual_weather_dispatch',false, ...
    'simulink_executed',false,'stateflow_executed',false,'stateflow_availability_checked',false, ...
    'results',table2struct(results));
fid=fopen(fullfile(outputDir,files{3}),'w'); assert(fid>0,'Unable to write evidence.');
cleanup=onCleanup(@()fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(summary,PrettyPrint=true));
disp(results);
assert(all(passed),'DCHR:v16:ContractFailure','Dispatch contract failed.');

    function record(name,ok,note)
        names(end+1,1)=string(name); passed(end+1,1)=logical(ok); notes(end+1,1)=string(note);
    end
    function reject(name,callback,identifier)
        got="NO_ERROR";
        try, callback(); catch caught, got=string(caught.identifier); end
        record(name,got==string(identifier),"Expected "+string(identifier)+"; got "+got);
    end
end
