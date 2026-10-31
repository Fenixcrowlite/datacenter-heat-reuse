function m=compute_metrics_v2(cfg,out)
%COMPUTE_METRICS_V2 Energy, exergy, emissions and screening economics.
dt=cfg.sim.dt_h; S=@(x) sum(x,'omitnan')*dt;
m.heat_demand_MWh=S(out.Heat_Demand_MW);
m.hp_heat_MWh=S(out.HP_Heat_Used_MW); m.hp_electric_MWh=S(out.HP_Electric_MW);
m.gas_heat_MWh=S(out.Gas_Heat_MW); m.curtailed_hp_heat_MWh=S(out.Curtailed_HP_Heat_MW);
m.it_energy_MWh=S(out.IT_MW); m.dc_total_energy_MWh=S(out.DC_Total_MW);
m.recovered_source_available_MWh=S(out.Source_Heat_Available_MW);
m.hx_to_hp_MWh=S(out.HX_Heat_to_HP_MW); m.exergy_delivered_MWh=S(out.Useful_Heat_Exergy_MW);
m.reused_to_network_MWh=max(0,m.heat_demand_MWh-m.gas_heat_MWh);
m.coverage_fraction=m.reused_to_network_MWh/max(eps,m.heat_demand_MWh);
m.erf=m.reused_to_network_MWh/max(eps,m.dc_total_energy_MWh);
m.ere_system=(m.dc_total_energy_MWh+m.hp_electric_MWh-m.reused_to_network_MWh)/max(eps,m.it_energy_MWh);
m.mean_cop=sum(out.COP.*out.HP_Heat_Used_MW,'omitnan')/max(eps,sum(out.HP_Heat_Used_MW,'omitnan'));
m.mean_lift_K=sum(out.Temperature_Lift_K.*out.HP_Heat_Used_MW,'omitnan')/max(eps,sum(out.HP_Heat_Used_MW,'omitnan'));

m.baseline_gas_fuel_MWh=m.heat_demand_MWh/cfg.backup.gas_boiler_efficiency;
m.scenario_gas_fuel_MWh=m.gas_heat_MWh/cfg.backup.gas_boiler_efficiency;
m.baseline_opex_EUR=m.baseline_gas_fuel_MWh*cfg.econ.gas_EUR_per_MWh_fuel;
m.scenario_opex_EUR=m.scenario_gas_fuel_MWh*cfg.econ.gas_EUR_per_MWh_fuel+m.hp_electric_MWh*cfg.econ.electricity_EUR_per_MWh;
m.opex_saving_EUR=m.baseline_opex_EUR-m.scenario_opex_EUR;
m.baseline_CO2_t=m.baseline_gas_fuel_MWh*cfg.econ.gas_tCO2_per_MWh_fuel;
m.scenario_CO2_t=m.scenario_gas_fuel_MWh*cfg.econ.gas_tCO2_per_MWh_fuel+m.hp_electric_MWh*cfg.econ.grid_tCO2_per_MWh;
m.CO2_saving_t=m.baseline_CO2_t-m.scenario_CO2_t;
m.CO2_saving_fraction=m.CO2_saving_t/max(eps,m.baseline_CO2_t);

m.capex_EUR=cfg.hp.max_heat_output_MW*1000*cfg.econ.hp_capex_EUR_per_kWth+ ...
 cfg.storage.capacity_MWh*1000*cfg.econ.storage_capex_EUR_per_kWh+cfg.hx.max_heat_MW*1000*cfg.econ.hx_capex_EUR_per_kW;
r=cfg.econ.discount_rate; n=cfg.econ.project_years; crf=r*(1+r)^n/((1+r)^n-1);
m.annualized_capex_EUR=m.capex_EUR*crf;
m.screening_LCOH_EUR_per_MWh=(m.annualized_capex_EUR+m.hp_electric_MWh*cfg.econ.electricity_EUR_per_MWh)/max(eps,m.reused_to_network_MWh);
m.simple_payback_y=m.capex_EUR/max(eps,m.opex_saving_EUR);
end
