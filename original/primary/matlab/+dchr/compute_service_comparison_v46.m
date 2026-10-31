function m=compute_service_comparison_v46(cfg,out)
% Gas-only comparator supplies exactly the heat actually delivered by out.
% Screening active-HP + boiler operational accounting, no CAPEX/auxiliary claim.
e=dchr.compute_energy_metrics_v45(cfg,out);
eta=cfg.backup.gas_boiler_efficiency;
v=[eta cfg.econ.gas_EUR_per_MWh_fuel cfg.econ.electricity_EUR_per_MWh ...
    cfg.econ.gas_tCO2_per_MWh_fuel cfg.econ.grid_tCO2_per_MWh];
validateattributes(v,{'numeric'},{'real','finite','row','numel',5,'nonnegative'});
assert(eta>0&&eta<=1,'DCHR:v46:Domain','Boiler efficiency must be in (0,1].');
m=struct('version','0.46','energy',e,'gas_boiler_efficiency',eta, ...
    'gas_price_EUR_per_MWh_fuel',v(2),'electricity_price_EUR_per_MWh',v(3), ...
    'gas_tCO2_per_MWh_fuel',v(4),'grid_tCO2_per_MWh',v(5));
m.equal_delivered_service_gas_fuel_MWh=e.total_delivered_MWh/eta;
m.scenario_gas_fuel_MWh=e.gas_heat_MWh/eta;
m.equal_delivered_service_baseline_opex_EUR=m.equal_delivered_service_gas_fuel_MWh*v(2);
m.scenario_active_HP_boiler_opex_EUR=m.scenario_gas_fuel_MWh*v(2)+e.hp_electric_MWh*v(3);
m.equal_delivered_service_opex_difference_EUR=m.equal_delivered_service_baseline_opex_EUR-m.scenario_active_HP_boiler_opex_EUR;
m.equal_delivered_service_baseline_CO2_t=m.equal_delivered_service_gas_fuel_MWh*v(4);
m.scenario_active_HP_boiler_CO2_t=m.scenario_gas_fuel_MWh*v(4)+e.hp_electric_MWh*v(5);
m.equal_delivered_service_CO2_difference_t=m.equal_delivered_service_baseline_CO2_t-m.scenario_active_HP_boiler_CO2_t;
% Diagnostic quantifies the spurious credit of a full-demand baseline.
m.full_demand_baseline_opex_EUR=e.heat_demand_MWh/eta*v(2);
m.full_demand_baseline_CO2_t=e.heat_demand_MWh/eta*v(4);
m.unmet_baseline_opex_credit_EUR=e.unmet_heat_MWh/eta*v(2);
m.unmet_baseline_CO2_credit_t=e.unmet_heat_MWh/eta*v(4);
fields=fieldnames(m);
for j=1:numel(fields)
    x=m.(fields{j});if isnumeric(x),assert(all(isfinite(x)),'DCHR:v46:Domain','Unrepresentable comparison.');end
end
m.service_boundary='EQUAL_ACTUALLY_DELIVERED_NETWORK_INLET_HEAT';
m.accounting_boundary='ACTIVE_HP_AND_BOILER_ONLY_CAPEX_AUXILIARIES_UNSPECIFIED';
m.comparator_boiler_capacity_policy='IDEAL_GAS_ONLY_COMPARATOR_SIZED_FOR_SAME_DELIVERED_PROFILE';
m.heat_inventory_boundary='INITIAL_TES_PROVENANCE_AND_TERMINAL_VALUE_UNPRICED';
end
