function cfg = default_config()
%DEFAULT_CONFIG Reference configuration for the data-centre heat-reuse model.
% All values are explicit scenario assumptions unless a source is listed in docs/.

cfg.meta.name = "DataCenter Heat Reuse - reference model";
cfg.meta.version = "0.1.0";

cfg.sim.start = datetime(2026,1,1,0,0,0);
cfg.sim.dt_h = 1.0;
cfg.sim.hours = 8760;
cfg.sim.random_seed = 42;

% Data centre
cfg.dc.it_capacity_MW = 10.0;
cfg.dc.pue = 1.20;
cfg.dc.util_mean = 0.82;
cfg.dc.util_daily_amp = 0.06;
cfg.dc.util_weekly_amp = 0.03;
cfg.dc.util_noise_sigma = 0.025;
cfg.dc.util_min = 0.55;
cfg.dc.util_max = 0.98;
cfg.dc.recovery_fraction = 0.85;
cfg.dc.source_temp_C = 35.0;

% Heat pump
cfg.hp.supply_temp_C = 70.0;
cfg.hp.carnot_efficiency = 0.50;
cfg.hp.cop_min = 2.2;
cfg.hp.cop_max = 7.0;
cfg.hp.max_heat_output_MW = 12.0;

% District heating demand model
cfg.dh.balance_temp_C = 16.0;
cfg.dh.design_outdoor_temp_C = -12.0;
cfg.dh.space_heat_design_MW = 18.0;
cfg.dh.base_hot_water_MW = 2.0;
cfg.dh.network_efficiency = 0.94;

% Thermal storage
cfg.storage.capacity_MWh = 50.0;
cfg.storage.initial_soc = 0.00;
cfg.storage.charge_limit_MW = 5.0;
cfg.storage.discharge_limit_MW = 5.0;
cfg.storage.eta_charge = 0.95;
cfg.storage.eta_discharge = 0.95;
cfg.storage.loss_fraction_per_h = 1.0e-4;

% Backup boiler
cfg.backup.gas_boiler_efficiency = 0.90;

% Economic and emissions assumptions for the demonstration experiment.
% They are NOT claimed as current Slovak market values.
cfg.econ.electricity_EUR_per_MWh = 100.0;
cfg.econ.gas_EUR_per_MWh_fuel = 50.0;
cfg.econ.grid_tCO2_per_MWh = 0.20;
cfg.econ.gas_tCO2_per_MWh_fuel = 0.202;

% Synthetic Bratislava-like weather generator parameters.
cfg.weather.annual_mean_C = 10.5;
cfg.weather.seasonal_amplitude_C = 11.0;
cfg.weather.daily_amplitude_C = 1.8;
cfg.weather.noise_sigma_C = 1.8;
cfg.weather.warmest_day = 200;
end
