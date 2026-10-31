function cfg = default_config_v2()
%DEFAULT_CONFIG_V2 Extended, backwards-comparable configuration.
cfg = default_config();
cfg.meta.version = "0.2.0";
cfg.model.hp_backend = "carnot";
cfg.hp.carnot_efficiency = 0.45;
cfg.model.dh_temperature = "weather";
cfg.hx.enabled = true;
cfg.hx.effectiveness = 0.97;
cfg.hx.max_heat_MW = 20.0;
cfg.hx.approach_K = 3.0;
cfg.hp.part_load_min = 0.15;
cfg.hp.part_load_penalty = 0.08;
cfg.hp.poly_c0 = 7.2;
cfg.hp.poly_c1 = -0.075;
cfg.hp.poly_c2 = 2.2e-4;
cfg.dh.supply_min_C = 55.0;
cfg.dh.supply_max_C = 80.0;
cfg.dh.return_min_C = 35.0;
cfg.dh.return_max_C = 50.0;
cfg.dh.temperature_balance_C = 16.0;
cfg.exergy.reference_temp_C = 10.0;
cfg.econ.hp_capex_EUR_per_kWth = 650;
cfg.econ.storage_capex_EUR_per_kWh = 35;
cfg.econ.hx_capex_EUR_per_kW = 80;
cfg.econ.project_years = 20;
cfg.econ.discount_rate = 0.06;
end
