function out = simulate_system_v2(cfg,input)
%SIMULATE_SYSTEM_V2 Component-oriented annual energy/thermal dispatch model.
N=numel(input.time); dt=cfg.sim.dt_h;
demand=dchr.heat_demand(input.outdoor_temp_C,cfg);
tDh=dchr.components.dh_temperature(input.outdoor_temp_C,cfg);
src=dchr.components.dc_source(input.it_power_MW,cfg);
hx=dchr.components.heat_exchanger(src.heat_MW,src.temperature_C,cfg);
hp=dchr.components.heat_pump(hx.heat_to_hp_MW,hx.evaporator_source_C,tDh.supply_C,cfg);

qUsed=zeros(N,1); pHp=zeros(N,1); qGas=zeros(N,1); qCharge=zeros(N,1);
qDis=zeros(N,1); qCurt=zeros(N,1); E=zeros(N+1,1); copAct=zeros(N,1);
sourceUsed=zeros(N,1); exUseful=zeros(N,1);
E(1)=cfg.storage.initial_soc*cfg.storage.capacity_MWh;

for k=1:N
    qPotential=hp.heat_potential_MW(k); qNeed=demand(k);
    qDirect=min(qPotential,qNeed);
    surplus=max(0,qPotential-qNeed); deficit=max(0,qNeed-qPotential);
    st=dchr.components.storage_step(E(k),surplus,deficit,cfg);
    qCharge(k)=st.charge_MW; qDis(k)=st.discharge_MW; E(k+1)=st.energy_next_MWh;
    qUsed(k)=qDirect+qCharge(k);
    qGas(k)=max(0,qNeed-qDirect-qDis(k));
    qCurt(k)=max(0,qPotential-qUsed(k));
    copAct(k)=dchr.components.part_load_cop(hp.cop_nominal(k),qUsed(k),cfg);
    pHp(k)=qUsed(k)/max(eps,copAct(k));
    sourceUsed(k)=max(0,qUsed(k)-pHp(k));
    usefulToNetwork=qDirect+qDis(k);
    exUseful(k)=dchr.components.exergy_heat(usefulToNetwork,tDh.supply_C(k),cfg.exergy.reference_temp_C);
end

out=table(input.time,input.outdoor_temp_C,input.it_utilization,input.it_power_MW,input.dc_total_power_MW, ...
 demand,tDh.supply_C,tDh.return_C,src.heat_MW,hx.heat_to_hp_MW,hx.rejected_MW, ...
 hp.lift_K,copAct,hp.heat_potential_MW,qUsed,pHp,sourceUsed,qCharge,qDis,E(1:end-1),qGas,qCurt,exUseful, ...
 'VariableNames',{'Time','Tout_C','IT_Util','IT_MW','DC_Total_MW','Heat_Demand_MW', ...
 'DH_Supply_C','DH_Return_C','Source_Heat_Available_MW','HX_Heat_to_HP_MW','HX_Rejected_MW', ...
 'Temperature_Lift_K','COP','HP_Heat_MW','HP_Heat_Used_MW','HP_Electric_MW','HP_Source_Used_MW', ...
 'Storage_Charge_MW','Storage_Discharge_MW','Storage_E_MWh','Gas_Heat_MW','Curtailed_HP_Heat_MW','Useful_Heat_Exergy_MW'});
end
