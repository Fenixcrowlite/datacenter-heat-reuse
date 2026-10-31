function hp = heat_pump_capability(source_heat_MW, source_temp_C, cfg)
%HEAT_PUMP_CAPABILITY Heat-pump COP and maximum useful heat output.
% COP_h = eta_Carnot * T_hot/(T_hot - T_cold), bounded by engineering limits.
% Q_out = Q_source + W = Q_source * COP/(COP-1).

T_hot_K = cfg.hp.supply_temp_C + 273.15;
T_cold_K = source_temp_C + 273.15;
lift_K = max(1.0, T_hot_K - T_cold_K);

cop = cfg.hp.carnot_efficiency .* (T_hot_K ./ lift_K);
cop = min(cfg.hp.cop_max, max(cfg.hp.cop_min, cop));
if isscalar(cop) && ~isscalar(source_heat_MW)
    cop = repmat(cop,size(source_heat_MW));
end

qOutFromSource = source_heat_MW .* cop ./ (cop - 1.0);
qOutMax = min(cfg.hp.max_heat_output_MW, qOutFromSource);

hp.cop = cop;
hp.max_heat_output_MW = qOutMax;
hp.max_electric_MW = qOutMax ./ cop;
hp.max_source_used_MW = qOutMax - hp.max_electric_MW;
end
