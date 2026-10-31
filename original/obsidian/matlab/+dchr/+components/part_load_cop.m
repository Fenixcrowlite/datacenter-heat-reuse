function cop = part_load_cop(cop_nominal, heat_used_MW, cfg)
%PART_LOAD_COP Mild efficiency penalty at low heat-pump loading.
plr = heat_used_MW ./ max(eps,cfg.hp.max_heat_output_MW);
plr = max(0,min(1,plr));
penalty = cfg.hp.part_load_penalty .* max(0,1-plr);
cop = cop_nominal .* (1-penalty);
cop = min(cfg.hp.cop_max,max(cfg.hp.cop_min,cop));
end
