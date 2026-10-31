function st = storage_step(E_MWh, surplus_MW, deficit_MW, cfg)
%STORAGE_STEP One-node storage state update for one simulation step.
dt=cfg.sim.dt_h;
E0=max(0,E_MWh*(1-cfg.storage.loss_fraction_per_h*dt));
charge=0; discharge=0;
if cfg.storage.capacity_MWh>0 && surplus_MW>0
    room=max(0,cfg.storage.capacity_MWh-E0);
    charge=min([surplus_MW,cfg.storage.charge_limit_MW,room/(cfg.storage.eta_charge*dt)]);
    E1=E0+cfg.storage.eta_charge*charge*dt;
elseif cfg.storage.capacity_MWh>0 && deficit_MW>0
    discharge=min([deficit_MW,cfg.storage.discharge_limit_MW,E0*cfg.storage.eta_discharge/dt]);
    E1=max(0,E0-discharge*dt/cfg.storage.eta_discharge);
else
    E1=E0;
end
st.charge_MW=charge; st.discharge_MW=discharge; st.energy_next_MWh=E1;
end
