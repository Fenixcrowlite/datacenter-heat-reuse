function cfg=dchr_config_real_2025_SK()
% Projektove predpoklady + NASA 2025, samostatna vetva bez zmeny povodneho cfg.
cfg=default_config();
cfg.sim.start=datetime(2025,1,1,0,0,0);
cfg.sim.hours=8760;
cfg.sim.dt_h=1;
cfg.dc.pue=1.36; % Uptime 2026 capacity weighted benchmark; not site measured
cfg.dc.source_temp_C=35;
end
