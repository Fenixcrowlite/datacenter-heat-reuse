function out = simulate_system_v13(cfg,input)
%SIMULATE_SYSTEM_V13 Finite backup capacity and explicit unmet demand.
% v13 additive wrapper: preserves the v2 HP/TES dispatch; caps only backup.
% The default boiler capacity is an explicit scenario assumption, not literature-calibrated.
if ~isfield(cfg,'backup') || ~isfield(cfg.backup,'max_heat_MW')
    error('DCHR:v13:MissingBoilerCap','Set cfg.backup.max_heat_MW explicitly.');
end
cap = cfg.backup.max_heat_MW;
if ~isnumeric(cap) || ~isscalar(cap) || ~isfinite(cap) || cap < 0
    error('DCHR:v13:InvalidBoilerCap','Boiler capacity must be finite and nonnegative.');
end
if ~isscalar(cfg.sim.dt_h) || ~isfinite(cfg.sim.dt_h) || cfg.sim.dt_h <= 0
    error('DCHR:v13:InvalidTimeStep','dt_h must be positive and finite.');
end
s=cfg.storage;
if ~isfinite(s.capacity_MWh) || s.capacity_MWh < 0 || ...
   ~isfinite(s.initial_soc) || s.initial_soc < 0 || s.initial_soc > 1 || ...
   ~isfinite(s.eta_charge) || s.eta_charge <= 0 || s.eta_charge > 1 || ...
   ~isfinite(s.eta_discharge) || s.eta_discharge <= 0 || s.eta_discharge > 1 || ...
   ~isfinite(s.loss_fraction_per_h) || s.loss_fraction_per_h < 0 || ...
   s.loss_fraction_per_h*cfg.sim.dt_h > 1
    error('DCHR:v13:InvalidStorage','Storage physical domain violated.');
end
out=dchr.simulate_system_v2(cfg,input);
requested=max(0,out.Gas_Heat_MW);
out.Gas_Heat_MW=min(requested,cap);
out.Unmet_Heat_MW=max(0,requested-out.Gas_Heat_MW);
out.Supplied_Heat_MW=out.Heat_Demand_MW-out.Unmet_Heat_MW;
balance=out.HP_Heat_Used_MW-out.Storage_Charge_MW+ ...
        out.Storage_Discharge_MW+out.Gas_Heat_MW+out.Unmet_Heat_MW;
if any(abs(balance-out.Heat_Demand_MW)>1e-7)
    error('DCHR:v13:Balance','Heat dispatch energy balance failed.');
end
end
