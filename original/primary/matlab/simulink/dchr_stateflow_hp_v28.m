function u = dchr_stateflow_hp_v28(x,E,p,h,model_dt)
%DCHR_STATEFLOW_HP_V28 Runtime domain/clock contract and v14 HP adapter.
% x=[source_MW,source_C,sink_C,demand_MW].
% p=[dt_h,capacity_MWh,charge_MW,discharge_MW,etaC,etaD,lambda_h^-1,boiler_MW].
% h=[HP_capacity_MW,Carnot_fraction,COP_min,COP_max,part_load_penalty,
%    backend_flag,poly_c0,poly_c1,poly_c2], with flag 0=Carnot and 1=polynomial.
% This host MATLAB call does not establish standalone code generation.
try
    validateattributes(model_dt,{'double'},{'real','finite','scalar','positive'});
    validateattributes(x,{'double'},{'real','finite','vector','numel',4});
    validateattributes(p,{'double'},{'real','finite','vector','numel',8});
    validateattributes(h,{'double'},{'real','finite','vector','numel',9});
    validateattributes(p(1),{'double'},{'real','finite','scalar','positive'});
    if p(1)~=model_dt
        error('DCHR:v28:IntegrationStep', ...
            'Physical interval p(1)=%.17g h differs from model sample time %.17g h.',p(1),model_dt);
    end
    if x(4)<0 || p(8)<0 || ~ismember(h(6),[0 1])
        error('DCHR:v28:InputDomain','Demand/backup must be nonnegative and backend flag must be 0 or 1.');
    end
    cfg.sim.dt_h=p(1);
    cfg.storage.capacity_MWh=p(2); cfg.storage.charge_limit_MW=p(3);
    cfg.storage.discharge_limit_MW=p(4); cfg.storage.eta_charge=p(5);
    cfg.storage.eta_discharge=p(6); cfg.storage.continuous_loss_rate_per_h=p(7);
    cfg.hp.max_heat_output_MW=h(1); cfg.hp.carnot_efficiency=h(2);
    cfg.hp.cop_min=h(3); cfg.hp.cop_max=h(4); cfg.hp.part_load_penalty=h(5);
    cfg.hp.poly_c0=h(7); cfg.hp.poly_c1=h(8); cfg.hp.poly_c2=h(9);
    if h(6)==0, cfg.model.hp_backend='carnot'; else, cfg.model.hp_backend='lift_polynomial'; end
    st=dchr.components.storage_step_v28(E,0,0,cfg);
    room=p(2)-st.energy_after_loss_MWh;
    request=x(4)+min(p(3),(room/p(1))/p(5));
    if ~isfinite(request)
        error('DCHR:v28:InputDomain','Demand plus charging request is nonfinite.');
    end
    hp=dchr.components.heat_pump_step_v14(x(1),x(2),x(3),request,cfg);
    u=[x(4);hp.heat_output_MW;hp.electric_MW;hp.source_used_MW;request; ...
        hp.cop_operating;double(hp.available);max(0,x(1)-hp.source_used_MW)];
catch original
    if strcmp(original.identifier,'DCHR:v28:IntegrationStep'), rethrow(original); end
    failure=MException('DCHR:v28:PhysicalDomain','Runtime physical-domain rejection: %s',original.message);
    failure=addCause(failure,original); throw(failure);
end
end
