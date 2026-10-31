function hp = heat_pump(q_source_MW, source_C, sink_C, cfg)
%HEAT_PUMP Pluggable heat-pump performance model.
lift = max(1,sink_C-source_C);
if cfg.model.hp_backend == "lift_polynomial"
    cop = cfg.hp.poly_c0 + cfg.hp.poly_c1.*lift + cfg.hp.poly_c2.*lift.^2;
else
    Th = sink_C + 273.15;
    Tc = source_C + 273.15;
    cop = cfg.hp.carnot_efficiency .* Th ./ max(1,Th-Tc);
end
cop = min(cfg.hp.cop_max,max(cfg.hp.cop_min,cop));
qPotential = q_source_MW .* cop ./ max(1e-6,cop-1);
hp.cop_nominal = cop;
hp.heat_potential_MW = min(cfg.hp.max_heat_output_MW,max(0,qPotential));
hp.lift_K = lift;
end
