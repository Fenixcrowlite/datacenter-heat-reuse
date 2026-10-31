function out = simulate_system(cfg, input)
%SIMULATE_SYSTEM Hourly dispatch of DC waste heat, heat pump, storage and gas backup.

N = numel(input.time);
dt = cfg.sim.dt_h;

demand = dchr.heat_demand(input.outdoor_temp_C, cfg);
sourceAvailable = input.it_power_MW .* cfg.dc.recovery_fraction;
hp = dchr.heat_pump_capability(sourceAvailable, cfg.dc.source_temp_C, cfg);

qHp = zeros(N,1); pHp = zeros(N,1); qGas = zeros(N,1);
qCharge = zeros(N,1); qDischarge = zeros(N,1); qCurtail = zeros(N,1);
E = zeros(N+1,1);
E(1) = cfg.storage.initial_soc * cfg.storage.capacity_MWh;

for k = 1:N
    Eavail = E(k) * (1 - cfg.storage.loss_fraction_per_h * dt);
    qPotential = hp.max_heat_output_MW(k);
    qNeed = demand(k);

    if qPotential >= qNeed
        qDirect = qNeed;
        surplus = qPotential - qNeed;
        if cfg.storage.capacity_MWh > 0
            roomMWh = max(0, cfg.storage.capacity_MWh - Eavail);
            qCharge(k) = min([surplus, cfg.storage.charge_limit_MW, roomMWh/(cfg.storage.eta_charge*dt)]);
        end
        qHp(k) = qDirect + qCharge(k);
        qCurtail(k) = max(0, qPotential - qHp(k));
        E(k+1) = Eavail + cfg.storage.eta_charge*qCharge(k)*dt;
    else
        qHp(k) = qPotential;
        deficit = qNeed - qPotential;
        if cfg.storage.capacity_MWh > 0
            qDischarge(k) = min([deficit, cfg.storage.discharge_limit_MW, Eavail*cfg.storage.eta_discharge/dt]);
        end
        E(k+1) = max(0, Eavail - qDischarge(k)*dt/cfg.storage.eta_discharge);
        qGas(k) = max(0, deficit - qDischarge(k));
    end

    pHp(k) = qHp(k) / hp.cop(k);
end

out = table(input.time, input.outdoor_temp_C, input.it_utilization, input.it_power_MW, ...
    input.dc_total_power_MW, demand, sourceAvailable, hp.cop, hp.max_heat_output_MW, ...
    qHp, pHp, qCharge, qDischarge, E(1:end-1), qGas, qCurtail, ...
    'VariableNames', {'Time','Tout_C','IT_Util','IT_MW','DC_Total_MW','Heat_Demand_MW', ...
    'Source_Heat_Available_MW','COP','HP_Heat_MW','HP_Heat_Used_MW','HP_Electric_MW', ...
    'Storage_Charge_MW','Storage_Discharge_MW','Storage_E_MWh','Gas_Heat_MW','Curtailed_HP_Heat_MW'});
end
