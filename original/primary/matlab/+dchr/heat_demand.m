function demand_MW = heat_demand(outdoor_temp_C, cfg)
%HEAT_DEMAND Linear weather-compensated district-heating demand.
% Demand = domestic hot water base + space heating below balance temperature.

span = cfg.dh.balance_temp_C - cfg.dh.design_outdoor_temp_C;
loadFraction = (cfg.dh.balance_temp_C - outdoor_temp_C) ./ span;
loadFraction = max(0, min(1.15, loadFraction));

buildingDemand = cfg.dh.base_hot_water_MW ...
    + cfg.dh.space_heat_design_MW .* loadFraction;

% Heat that must enter the network, including distribution losses.
demand_MW = buildingDemand ./ cfg.dh.network_efficiency;
end
