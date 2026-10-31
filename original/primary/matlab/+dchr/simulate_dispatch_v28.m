function out = simulate_dispatch_v28(cfg, input)
%SIMULATE_DISPATCH_V28 HP v14 + exponential loss-first TES + finite backup.
% Each input row is one fixed-duration interval at the recovered-source
% boundary: Source_Heat_MW, Source_C, Sink_C, Heat_Demand_MW.
% Independent MATLAB dispatch path: no Stateflow allocation helper calls.
% lambda is the explicit storage.continuous_loss_rate_per_h in h^-1.
% Passive cooling is exact; charge/discharge use a loss-first operator split.
% Reservoir temperatures, hydraulics, cycling, auxiliaries and economics
% retain the screening-model limitations recorded for the v16 reference.
if ~istable(input) || height(input)==0
    error('DCHR:v28:InputSeries','Input must be a nonempty table.');
end
required={'Source_Heat_MW','Source_C','Sink_C','Heat_Demand_MW'};
for j=1:numel(required)
    name=required{j};
    if ~ismember(name,input.Properties.VariableNames)
        error('DCHR:v28:InputSeries','Missing input column %s.',name);
    end
    x=input.(name);
    if ~isnumeric(x) || ~isreal(x) || size(x,2)~=1 || any(~isfinite(x))
        error('DCHR:v28:InputSeries','%s must be a finite real numeric column.',name);
    end
end
if any(input.Source_Heat_MW<0) || any(input.Heat_Demand_MW<0) || ...
        any(input.Source_C<=-273.15) || any(input.Sink_C<=input.Source_C)
    error('DCHR:v28:InputSeries','Power or heating-mode temperature domain violated.');
end
if ~isfield(cfg,'backup') || ~isfield(cfg.backup,'max_heat_MW')
    error('DCHR:v28:BoilerDomain','Set explicit finite backup.max_heat_MW.');
end
boiler=cfg.backup.max_heat_MW; soc=cfg.storage.initial_soc;
if ~isnumeric(boiler) || ~isreal(boiler) || ~isscalar(boiler) || ~isfinite(boiler) || boiler<0
    error('DCHR:v28:BoilerDomain','Boiler capacity must be a finite nonnegative real scalar.');
end
if ~isnumeric(soc) || ~isreal(soc) || ~isscalar(soc) || ~isfinite(soc) || soc<0 || soc>1
    error('DCHR:v28:StorageDomain','initial_soc must be a finite real scalar in [0,1].');
end
% Validate the complete TES configuration before constructing initial state.
dchr.components.storage_step_v28(0,0,0,cfg);
E=double(soc)*double(cfg.storage.capacity_MWh);
N=height(input); rows=cell(N,1); dt=double(cfg.sim.dt_h);
for k=1:N
    preview=dchr.components.storage_step_v28(E,0,0,cfg);
    room=double(cfg.storage.capacity_MWh)-preview.energy_after_loss_MWh;
    chargeRoom=min(double(cfg.storage.charge_limit_MW), ...
        (room/dt)/double(cfg.storage.eta_charge));
    demand=double(input.Heat_Demand_MW(k));
    request=demand+chargeRoom;
    if ~isfinite(request)
        error('DCHR:v28:InputSeries','Demand plus charging request is nonfinite.');
    end
    h=dchr.components.heat_pump_step_v14(input.Source_Heat_MW(k), ...
        input.Source_C(k),input.Sink_C(k),request,cfg);
    direct=min(h.heat_output_MW,demand);
    st=dchr.components.storage_step_v28(E,max(0,h.heat_output_MW-demand), ...
        max(0,demand-h.heat_output_MW),cfg);
    deficit=max(0,demand-direct-st.discharge_MW);
    gas=min(double(boiler),deficit); unmet=max(0,deficit-gas);
    rows{k}=struct('HP_Request_MW',request,'HP_Heat_MW',h.heat_output_MW, ...
        'HP_Direct_MW',direct,'HP_Electric_MW',h.electric_MW, ...
        'HP_Source_Used_MW',h.source_used_MW,'COP',h.cop_operating, ...
        'HP_Available',h.available, ...
        'Source_Unused_MW',max(0,double(input.Source_Heat_MW(k))-h.source_used_MW), ...
        'Storage_Charge_MW',st.charge_MW,'Storage_Discharge_MW',st.discharge_MW, ...
        'Storage_E_Start_MWh',E,'Storage_E_After_Loss_MWh',st.energy_after_loss_MWh, ...
        'Storage_E_Next_MWh',st.energy_next_MWh, ...
        'Storage_Standing_Loss_MWh',st.standing_loss_MWh, ...
        'Storage_Charge_Loss_MWh',st.charge_loss_MWh, ...
        'Storage_Discharge_Loss_MWh',st.discharge_loss_MWh, ...
        'Gas_Heat_MW',gas,'Unmet_Heat_MW',unmet,'Supplied_Heat_MW',demand-unmet);
    E=st.energy_next_MWh;
end
out=[table((0:N-1)'*dt,'VariableNames',{'Time_h'}),input(:,required), ...
    struct2table(vertcat(rows{:}))];
% First law across HP, TES and demand ports over each complete interval.
closure=out.HP_Source_Used_MW*dt+out.HP_Electric_MW*dt+out.Gas_Heat_MW*dt+ ...
    out.Storage_E_Start_MWh-out.Supplied_Heat_MW*dt-out.Storage_E_Next_MWh- ...
    out.Storage_Standing_Loss_MWh-out.Storage_Charge_Loss_MWh-out.Storage_Discharge_Loss_MWh;
scale=max(1,out.Storage_E_Start_MWh+out.HP_Heat_MW*dt+out.Gas_Heat_MW*dt);
if any(~isfinite(closure)) || any(abs(closure)>1e-10.*scale)
    error('DCHR:v28:DispatchBalance','System interval first-law closure failed.');
end
out.System_Balance_Residual_MWh=closure;
end
