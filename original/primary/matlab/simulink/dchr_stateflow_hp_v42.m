function u = dchr_stateflow_hp_v42(x,E,p,h,model_dt)
% x=[sourceMW,sourceC,condenserC,demandMW,deliveryC]. Fixed common HP reservoir.
% p=[dt,cap,chargeLimit,dischargeLimit,etaC,etaD,lambda,Ec,C,Ta,boiler].
% C/Ta/Tmax/cutoff are frozen per simulation by Constant parameter blocks.
try
    validateattributes(model_dt,{'double'},{'real','finite','scalar','positive'});
    validateattributes(x,{'double'},{'real','finite','vector','numel',5});
    validateattributes(p,{'double'},{'real','finite','vector','numel',11});
    validateattributes(h,{'double'},{'real','finite','vector','numel',9});
    if p(1)~=model_dt, error('DCHR:v42:IntegrationStep','Physical dt differs from model sample time.'); end
    if x(4)<0 || p(11)<0 || ~ismember(h(6),[0 1])
        error('DCHR:v42:InputDomain','Nonnegative demand/boiler and defined HP backend required.');
    end
    cfg.sim.dt_h=p(1);
    cfg.storage.heat_capacity_MWh_per_K=p(9); cfg.storage.ambient_C=p(10);
    cfg.storage.max_temperature_C=p(10)+p(2)/p(9);
    cfg.storage.delivery_cutoff_C=p(10)+p(8)/p(9);
    cfg.storage.initial_temperature_C=p(10)+E/p(9);
    cfg.storage.charge_limit_MW=p(3); cfg.storage.discharge_limit_MW=p(4);
    cfg.storage.eta_charge=p(5); cfg.storage.eta_discharge=p(6);
    cfg.storage.continuous_loss_rate_per_h=p(7);
    st=dchr.components.storage_step_v30(E,0,0,cfg);
    if x(3)<cfg.storage.max_temperature_C || x(5)>cfg.storage.delivery_cutoff_C || ...
            x(5)<=-273.15 || x(3)<x(5)
        error('DCHR:v42:TemperaturePorts','Condenser must support tank maximum; delivery must not exceed cutoff.');
    end
    request=x(4)+min(p(3),st.charge_bound_MW);
    if ~isfinite(request), error('DCHR:v42:InputDomain','Nonfinite HP request.'); end
    cfg.hp.max_heat_output_MW=h(1); cfg.hp.carnot_efficiency=h(2);
    cfg.hp.cop_min=h(3); cfg.hp.cop_max=h(4); cfg.hp.part_load_penalty=h(5);
    cfg.hp.poly_c0=h(7); cfg.hp.poly_c1=h(8); cfg.hp.poly_c2=h(9);
    if h(6)==0, cfg.model.hp_backend='carnot'; else, cfg.model.hp_backend='lift_polynomial'; end
    hp=dchr.components.heat_pump_step_v40(x(1),x(2),x(3),request,cfg);
    u=[x(4);hp.heat_output_MW;hp.electric_MW;hp.source_used_MW;request; ...
        hp.cop_operating;double(hp.available);max(0,x(1)-hp.source_used_MW)];
catch original
    if strcmp(original.identifier,'DCHR:v42:IntegrationStep'), rethrow(original); end
    failure=MException('DCHR:v42:PhysicalDomain','Runtime physical-domain rejection: %s',original.message);
    failure=addCause(failure,original); throw(failure);
end
end
