function out = simulate_system_v48(cfg,input)
%SIMULATE_SYSTEM_V48 Actual source-constrained HP, finite boiler, legacy TES.
% Loss-first Euler TES is retained deliberately to isolate the HP correction.
% This annual MATLAB adapter is not the v42 exact/event Stateflow controller.
% COP minimum is an operating cutoff; off COP is NaN, with zero power ports.
dt=cfg.sim.dt_h;s=cfg.storage;
validateattributes(dt,{'numeric'},{'real','finite','scalar','positive'});
fields={'capacity_MWh','initial_soc','charge_limit_MW','discharge_limit_MW', ...
    'eta_charge','eta_discharge','loss_fraction_per_h'};
for j=1:numel(fields)
    validateattributes(s.(fields{j}),{'numeric'},{'real','finite','scalar','nonnegative'});
end
assert(s.initial_soc<=1&&s.eta_charge>0&&s.eta_charge<=1&& ...
    s.eta_discharge>0&&s.eta_discharge<=1&&s.loss_fraction_per_h*dt<=1, ...
    'DCHR:v48:StorageDomain','Invalid loss-first storage domain.');
validateattributes(cfg.backup.max_heat_MW,{'numeric'},{'real','finite','scalar','nonnegative'});
validateattributes(cfg.dc.recovery_fraction,{'numeric'},{'real','finite','scalar','>=',0,'<=',1});
if cfg.hx.enabled
    validateattributes(cfg.hx.effectiveness,{'numeric'},{'real','finite','scalar','>=',0,'<=',1});
    validateattributes(cfg.hx.max_heat_MW,{'numeric'},{'real','finite','scalar','nonnegative'});
    validateattributes(cfg.hx.approach_K,{'numeric'},{'real','finite','scalar','nonnegative'});
end
N=numel(input.time);assert(N>0&&iscolumn(input.time)&&all(~isnat(input.time)), ...
    'DCHR:v48:InputDomain','Require nonempty finite datetime column.');
assert(all(abs(hours(diff(input.time))-dt)<=32*eps(max(1,dt))), ...
    'DCHR:v48:InputDomain','Timestamp spacing must equal dt_h.');
names={'outdoor_temp_C','it_utilization','it_power_MW','dc_total_power_MW'};
for j=1:numel(names)
    validateattributes(input.(names{j}),{'numeric'},{'real','finite','column','numel',N});
end
assert(all(input.it_power_MW>=0)&&all(input.dc_total_power_MW>=0), ...
    'DCHR:v48:InputDomain','Nonnegative input electric powers required.');
demand=dchr.heat_demand(input.outdoor_temp_C,cfg);
tDh=dchr.components.dh_temperature(input.outdoor_temp_C,cfg);
validateattributes(demand,{'numeric'},{'real','finite','column','numel',N,'nonnegative'});
src=dchr.components.dc_source(input.it_power_MW,cfg);
hx=dchr.components.heat_exchanger(src.heat_MW,src.temperature_C,cfg);
% Q, W, source, direct, charge, discharge, gas, unmet, request, COP,
% nominal COP, next inventory, standing loss, conversion loss, balance.
v=zeros(N,15);status=strings(N,1);E=zeros(N+1,1);
E(1)=s.initial_soc*s.capacity_MWh;
for k=1:N
    retained=E(k)*(1-s.loss_fraction_per_h*dt);
    chargeBound=min(s.charge_limit_MW,max(0,s.capacity_MWh-retained)/(s.eta_charge*dt));
    request=demand(k)+chargeBound;
    hp=dchr.components.heat_pump_step_v40(hx.heat_to_hp_MW(k), ...
        hx.evaporator_source_C(k),tDh.supply_C(k),request,cfg);
    q=hp.heat_output_MW;direct=min(q,demand(k));
    st=dchr.components.storage_step(E(k),max(0,q-demand(k)),max(0,demand(k)-q),cfg);
    E(k+1)=st.energy_next_MWh;
    remaining=max(0,demand(k)-direct-st.discharge_MW);
    gas=min(remaining,cfg.backup.max_heat_MW);unmet=max(0,remaining-gas);
    standing=E(k)-retained;
    conversion=((1-s.eta_charge)*st.charge_MW+(1/s.eta_discharge-1)*st.discharge_MW)*dt;
    delivered=direct+st.discharge_MW+gas;
    residual=E(k)+(hp.source_used_MW+hp.electric_MW+gas-delivered)*dt ...
        -E(k+1)-standing-conversion;
    tol=256*eps(max([1 E(k) E(k+1) demand(k)*dt q*dt]));
    assert(abs(q-direct-st.charge_MW)*dt<=tol&&abs(residual)<=tol&& ...
        E(k+1)>=-tol&&E(k+1)<=s.capacity_MWh+tol, ...
        'DCHR:v48:Balance','Unallocated HP heat or inventory/first-law violation.');
    v(k,:)=[q hp.electric_MW hp.source_used_MW direct st.charge_MW st.discharge_MW ...
        gas unmet request hp.cop_operating hp.cop_nominal E(k+1) standing conversion residual];
    status(k)=hp.status;
end
out=table(input.time,input.outdoor_temp_C,input.it_power_MW,demand,tDh.supply_C, ...
    hx.evaporator_source_C,hx.heat_to_hp_MW,E(1:end-1), ...
    'VariableNames',{'Time','Tout_C','IT_MW','Heat_Demand_MW','DH_Supply_C', ...
    'HP_Source_C','HX_Heat_to_HP_MW','Storage_E_MWh'});
out=[out array2table(v,'VariableNames',{'HP_Heat_MW','HP_Electric_MW','HP_Source_Used_MW', ...
    'HP_Direct_MW','Storage_Charge_MW','Storage_Discharge_MW','Gas_Heat_MW','Unmet_Heat_MW', ...
    'HP_Request_MW','COP','COP_Nominal','Storage_E_Next_MWh','Storage_Standing_Loss_MWh', ...
    'Storage_Conversion_Loss_MWh','First_Law_Residual_MWh'})];
out.HP_Status=status;
end
