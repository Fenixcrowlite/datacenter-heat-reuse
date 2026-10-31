function u = dchr_stateflow_hp_v22(x,E,p,h)
% Normal-mode adapter to the independently cross-checked v14 HP component.
% This host MATLAB call is intentionally not a standalone code-generation claim.
validateattributes(x,{'double'},{'real','finite','vector','numel',4});
validateattributes(p,{'double'},{'real','finite','vector','numel',8});
validateattributes(h,{'double'},{'real','finite','vector','numel',9});
if x(4)<0 || p(8)<0 || ~ismember(h(6),[0 1])
    error('DCHR:v22:InputDomain','Demand/backup must be nonnegative and backend flag must be 0 or 1.');
end
cfg.sim.dt_h=p(1);
cfg.storage.capacity_MWh=p(2); cfg.storage.charge_limit_MW=p(3);
cfg.storage.discharge_limit_MW=p(4); cfg.storage.eta_charge=p(5);
cfg.storage.eta_discharge=p(6); cfg.storage.loss_fraction_per_h=p(7);
cfg.hp.max_heat_output_MW=h(1); cfg.hp.carnot_efficiency=h(2);
cfg.hp.cop_min=h(3); cfg.hp.cop_max=h(4); cfg.hp.part_load_penalty=h(5);
cfg.hp.poly_c0=h(7); cfg.hp.poly_c1=h(8); cfg.hp.poly_c2=h(9);
if h(6)==0, cfg.model.hp_backend='carnot'; else, cfg.model.hp_backend='lift_polynomial'; end
st=dchr.components.storage_step_v16(E,0,0,cfg);
room=p(2)-st.energy_after_loss_MWh;
request=x(4)+min(p(3),room/p(1)/p(5));
hp=dchr.components.heat_pump_step_v14(x(1),x(2),x(3),request,cfg);
u=[x(4);hp.heat_output_MW;hp.electric_MW;hp.source_used_MW;request; ...
    hp.cop_operating;double(hp.available);max(0,x(1)-hp.source_used_MW)];
end
