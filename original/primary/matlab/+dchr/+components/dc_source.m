function s = dc_source(it_power_MW, cfg)
%DC_SOURCE Recoverable low-grade heat at the data-centre boundary.
s.heat_MW = max(0,it_power_MW) .* cfg.dc.recovery_fraction;
s.temperature_C = repmat(cfg.dc.source_temp_C,size(it_power_MW));
end
