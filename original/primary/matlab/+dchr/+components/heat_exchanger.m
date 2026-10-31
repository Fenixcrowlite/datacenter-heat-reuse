function hx = heat_exchanger(q_source_MW, source_temp_C, cfg)
%HEAT_EXCHANGER Aggregate recovery interface with capacity and approach limits.
if ~cfg.hx.enabled
    hx.heat_to_hp_MW = q_source_MW;
    hx.evaporator_source_C = source_temp_C;
    hx.rejected_MW = zeros(size(q_source_MW));
    return
end
q = min(q_source_MW .* cfg.hx.effectiveness, cfg.hx.max_heat_MW);
hx.heat_to_hp_MW = max(0,q);
hx.evaporator_source_C = source_temp_C - cfg.hx.approach_K;
hx.rejected_MW = max(0,q_source_MW - hx.heat_to_hp_MW);
end
