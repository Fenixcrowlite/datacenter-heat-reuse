function results = run_tests_v3()
%RUN_TESTS_V3 Physics invariants plus directional sanity checks.
run_tests_v2();
base = default_config_v2();
input = dchr.make_inputs(base);

cfg = base; cfg.model.dh_temperature="fixed"; cfg.hp.supply_temp_C=70;
cfg.storage.capacity_MWh=0; cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0;
cfg.dc.recovery_fraction=0.85;
cfg.dc.source_temp_C=25; a=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
cfg.dc.source_temp_C=45; b=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
source_temp_improves_cop = b.mean_cop > a.mean_cop;

cfg = base; cfg.model.dh_temperature="fixed"; cfg.dc.source_temp_C=35; cfg.dc.recovery_fraction=0.85;
cfg.storage.capacity_MWh=0; cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0;
cfg.hp.supply_temp_C=60; c=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
cfg.hp.supply_temp_C=80; d=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
lower_supply_improves_cop = c.mean_cop > d.mean_cop;

cfg = base; cfg.model.dh_temperature="weather"; cfg.dc.source_temp_C=45;
cfg.storage.capacity_MWh=0; cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0;
cfg.dc.recovery_fraction=0.70; e=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
cfg.dc.recovery_fraction=0.90; f=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
more_recovery_not_worse = f.coverage_fraction >= e.coverage_fraction-1e-9;

cfg = base; cfg.model.dh_temperature="weather"; cfg.dc.source_temp_C=45; cfg.dc.recovery_fraction=0.90;
cfg.storage.capacity_MWh=0; cfg.storage.charge_limit_MW=0; cfg.storage.discharge_limit_MW=0;
g=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
cfg.storage.capacity_MWh=100; cfg.storage.charge_limit_MW=5; cfg.storage.discharge_limit_MW=5;
h=dchr.compute_metrics_v2(cfg,dchr.simulate_system_v2(cfg,input));
storage_not_worse_for_coverage = h.coverage_fraction >= g.coverage_fraction-1e-9;

checks={ ...
 'source_temperature_improves_COP',source_temp_improves_cop; ...
 'lower_DH_supply_improves_COP',lower_supply_improves_cop; ...
 'more_recovery_not_worse_for_coverage',more_recovery_not_worse; ...
 'storage_not_worse_for_coverage',storage_not_worse_for_coverage};
results=cell2table(checks,'VariableNames',{'Test','Passed'});
rootDir=fileparts(fileparts(mfilename('fullpath')));
writetable(results,fullfile(rootDir,'results','tests_v3.csv'));
disp(results);
if ~all(results.Passed), error('DCHR:v3Tests','One or more v0.3 directional checks failed.'); end
end
