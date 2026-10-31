function c40_export_warm45_v2()
%C40_EXPORT_WARM45_V2 Native MATLAB reproducibility export, isolated output.
% This function is NOT run by creation. Never call run_experiment_v2:
% its default writetable() overwrites shared results and figures.
projectRoot = 'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse';
sourceDir = fullfile(projectRoot, 'matlab');
outDir = fileparts(mfilename('fullpath'));
outputCsv = fullfile(outDir, 'Warm45_Storage100_v2_MATLAB_NATIVE.csv');
outputJson = fullfile(outDir, 'C40_NATIVE_EXPORT_RESULT.json');
assert(isfolder(sourceDir), 'C40:SourceMissing');
assert(~isfile(outputCsv) && ~isfile(outputJson), 'C40:OutputExists');
assert(~isfile(fullfile(outDir,'STOP')) && ~isfile(fullfile(outDir,'PAUSE')), 'C40:Stopped');
assert(~isfile(fullfile(projectRoot,'STOP')) && ~isfile(fullfile(projectRoot,'PAUSE')), 'C40:Stopped');
addpath(sourceDir);
cfg = default_config_v2();
assert(cfg.sim.random_seed == 42 && cfg.sim.hours == 8760, 'C40:InputContract');
input = dchr.make_inputs(cfg);
% Scenario Warm45_Storage100 from run_experiment_v2.m, without the
% destructive shared CSV/figure writes in that original driver.
cfg.dc.source_temp_C = 45;
cfg.dc.recovery_fraction = 0.90;
cfg.storage.capacity_MWh = 100;
cfg.model.dh_temperature = "weather";
assert(cfg.storage.charge_limit_MW == 5 && cfg.storage.discharge_limit_MW == 5, 'C40:StorageContract');
out = dchr.simulate_system_v2(cfg, input);
m = dchr.compute_metrics_v2(cfg, out);
assert(height(out) == 8760 && width(out) == 23, 'C40:Shape');
assert(abs(m.gas_heat_MWh - 10542.548227789) < 0.001, 'C40:GasOracle');
assert(abs(m.hp_electric_MWh - 7969.875645450) < 0.001, 'C40:ElectricOracle');
assert(all(isfinite(out.Gas_Heat_MW)) && all(out.Gas_Heat_MW >= 0), 'C40:GasPhysical');
assert(~isfile(outputCsv) && ~isfile(outputJson), 'C40:OutputRace');
writetable(out, outputCsv);
report = struct('scope','DCHR_C40_NATIVE_MATLAB_EXPORT','scenario','Warm45_Storage100', ...
    'hours',height(out),'gas_MWh',m.gas_heat_MWh,'hp_electric_MWh',m.hp_electric_MWh, ...
    'random_seed',cfg.sim.random_seed,'synthetic_data',true, ...
    'stateflow_v85_parity',false,'physical_validation',false,'primary_sources_signed',0);
fid = fopen(outputJson, 'w', 'n', 'UTF-8');
assert(fid >= 0, 'C40:ReportOpen');
cleanup = onCleanup(@() fclose(fid));
fprintf(fid,'%s\n',jsonencode(report));
disp('C40_NATIVE_MATLAB_EXPORT_PASS');
end
