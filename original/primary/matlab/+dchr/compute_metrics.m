function m = compute_metrics(cfg, out)
%COMPUTE_METRICS Annual energy, economic, environmental and DC reuse KPIs.
dt = cfg.sim.dt_h;
S = @(x) sum(x,'omitnan')*dt;

m.heat_demand_MWh = S(out.Heat_Demand_MW);
m.hp_heat_MWh = S(out.HP_Heat_Used_MW);
m.hp_electric_MWh = S(out.HP_Electric_MW);
m.storage_charge_MWh = S(out.Storage_Charge_MW);
m.storage_discharge_MWh = S(out.Storage_Discharge_MW);
m.gas_heat_MWh = S(out.Gas_Heat_MW);
m.curtailed_hp_heat_MWh = S(out.Curtailed_HP_Heat_MW);
m.it_energy_MWh = S(out.IT_MW);
m.dc_total_energy_MWh = S(out.DC_Total_MW);
m.recovered_source_available_MWh = S(out.Source_Heat_Available_MW);

m.reused_to_network_MWh = max(0, m.heat_demand_MWh - m.gas_heat_MWh);
m.coverage_fraction = m.reused_to_network_MWh / max(eps,m.heat_demand_MWh);
m.erf = m.reused_to_network_MWh / max(eps,m.dc_total_energy_MWh);
m.ere = (1 - m.erf) * cfg.dc.pue;
m.mean_cop = sum(out.COP .* out.HP_Heat_Used_MW,'omitnan') / max(eps,sum(out.HP_Heat_Used_MW,'omitnan'));

m.baseline_gas_fuel_MWh = m.heat_demand_MWh / cfg.backup.gas_boiler_efficiency;
m.scenario_gas_fuel_MWh = m.gas_heat_MWh / cfg.backup.gas_boiler_efficiency;
m.baseline_opex_EUR = m.baseline_gas_fuel_MWh * cfg.econ.gas_EUR_per_MWh_fuel;
m.scenario_opex_EUR = m.scenario_gas_fuel_MWh * cfg.econ.gas_EUR_per_MWh_fuel ...
    + m.hp_electric_MWh * cfg.econ.electricity_EUR_per_MWh;
m.opex_saving_EUR = m.baseline_opex_EUR - m.scenario_opex_EUR;

m.baseline_CO2_t = m.baseline_gas_fuel_MWh * cfg.econ.gas_tCO2_per_MWh_fuel;
m.scenario_CO2_t = m.scenario_gas_fuel_MWh * cfg.econ.gas_tCO2_per_MWh_fuel ...
    + m.hp_electric_MWh * cfg.econ.grid_tCO2_per_MWh;
m.CO2_saving_t = m.baseline_CO2_t - m.scenario_CO2_t;
m.CO2_saving_fraction = m.CO2_saving_t / max(eps,m.baseline_CO2_t);
end
