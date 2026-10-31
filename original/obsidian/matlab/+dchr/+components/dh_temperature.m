function t = dh_temperature(outdoor_C, cfg)
%DH_TEMPERATURE Supply/return schedule for the district-heating network.
if cfg.model.dh_temperature == "fixed"
    t.supply_C = repmat(cfg.hp.supply_temp_C,size(outdoor_C));
    t.return_C = t.supply_C - 30;
    return
end
span = cfg.dh.temperature_balance_C - cfg.dh.design_outdoor_temp_C;
f = (cfg.dh.temperature_balance_C - outdoor_C)./span;
f = max(0,min(1,f));
t.supply_C = cfg.dh.supply_min_C + f.*(cfg.dh.supply_max_C-cfg.dh.supply_min_C);
t.return_C = cfg.dh.return_min_C + f.*(cfg.dh.return_max_C-cfg.dh.return_min_C);
end
