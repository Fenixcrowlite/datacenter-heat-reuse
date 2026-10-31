function a=adapt_annual_stateflow_v49(cfg,input,policy)
% Explicit synthetic annual boundary adapter to preserved saved Stateflow v42.
% Preflight is a static input-domain check, not a state/event-budget guarantee.
dt=cfg.sim.dt_h;N=numel(input.time);
validateattributes(dt,{'double'},{'real','finite','scalar','positive'});
assert(N>0&&iscolumn(input.time)&&all(~isnat(input.time))&& ...
    all(abs(hours(diff(input.time))-dt)<=32*eps(max(1,dt))), ...
    'DCHR:v49:TimeDomain','Nonempty regular datetime column required.');
for name={'outdoor_temp_C','it_power_MW','it_utilization','dc_total_power_MW'}
    validateattributes(input.(name{1}),{'double'},{'real','finite','column','numel',N});
end
assert(all(input.it_power_MW>=0)&all(input.dc_total_power_MW>=0), ...
    'DCHR:v49:InputDomain','Nonnegative electric power required.');
assert(string(cfg.model.hp_backend)=="carnot"&&string(cfg.model.dh_temperature)=="weather", ...
    'DCHR:v49:SupportedBoundary','This adapter certifies the explicit weather/Carnot boundary only.');
validateattributes(cfg.dc.recovery_fraction,{'double'},{'real','finite','scalar','>=',0,'<=',1});
assert(islogical(cfg.hx.enabled)&&isscalar(cfg.hx.enabled),'DCHR:v49:HXDomain','Logical HX flag required.');
if cfg.hx.enabled
    validateattributes(cfg.hx.effectiveness,{'double'},{'real','finite','scalar','>=',0,'<=',1});
    validateattributes(cfg.hx.max_heat_MW,{'double'},{'real','finite','scalar','nonnegative'});
    validateattributes(cfg.hx.approach_K,{'double'},{'real','finite','scalar','nonnegative'});
end
for name={'ambient_C','max_temperature_C','delivery_cutoff_C','restart_energy_MWh', ...
        'min_on_h','min_off_h','continuous_loss_rate_per_h','condenser_C'}
    validateattributes(policy.(name{1}),{'double'},{'real','finite','scalar'});
end
s=cfg.storage;validateattributes(s.capacity_MWh,{'double'},{'real','finite','scalar','positive'});
validateattributes(s.initial_soc,{'double'},{'real','finite','scalar','>=',0,'<=',1});
assert(policy.max_temperature_C>policy.delivery_cutoff_C&&policy.delivery_cutoff_C>policy.ambient_C, ...
    'DCHR:v49:TankDomain','Require ambient < cutoff < maximum.');
C=s.capacity_MWh/(policy.max_temperature_C-policy.ambient_C);
Ec=C*(policy.delivery_cutoff_C-policy.ambient_C);
p=[dt s.capacity_MWh s.charge_limit_MW s.discharge_limit_MW s.eta_charge s.eta_discharge ...
    policy.continuous_loss_rate_per_h Ec C policy.ambient_C cfg.backup.max_heat_MW];
h=[cfg.hp.max_heat_output_MW cfg.hp.carnot_efficiency cfg.hp.cop_min cfg.hp.cop_max ...
    cfg.hp.part_load_penalty 0 cfg.hp.poly_c0 cfg.hp.poly_c1 cfg.hp.poly_c2];
c=[policy.restart_energy_MWh policy.min_on_h policy.min_off_h 64];E0=s.capacity_MWh*s.initial_soc;
etol=64*eps(max(1,s.capacity_MWh));
assert(c(1)>Ec+2*etol&&c(1)<s.capacity_MWh-2*etol&&Ec>2*etol&&all(c(2:3)>=0), ...
    'DCHR:v49:ControlDomain','Resolved restart band and nonnegative dwell required.');
m=policy.initial_clock(:);validateattributes(m,{'double'},{'real','finite','column','numel',4});
assert(ismember(m(1),[0 1])&&m(2)>=0&&m(4)>=0,'DCHR:v49:ClockDomain','Invalid initial clock.');
stateflow_clock_add_v42(m(2),m(3),m(4),0);
source=dchr.components.dc_source(input.it_power_MW,cfg);
hx=dchr.components.heat_exchanger(source.heat_MW,source.temperature_C,cfg);
dh=dchr.components.dh_temperature(input.outdoor_temp_C,cfg);
demand=dchr.heat_demand(input.outdoor_temp_C,cfg);
validateattributes(demand,{'double'},{'real','finite','column','numel',N,'nonnegative'});
mode=string(policy.condenser_policy);
assert(isscalar(mode)&&any(mode==["scheduled","fixed"]),'DCHR:v49:PolicyDomain','Explicit scheduled or fixed condenser required.');
sink=dh.supply_C;if mode=="fixed",sink=repmat(policy.condenser_C,N,1);end
x=[hx.heat_to_hp_MW hx.evaporator_source_C sink demand dh.supply_C];
ok=false(N,1);identifier=strings(N,1);message=strings(N,1);
for i=1:N
    try,dchr_stateflow_hp_v42(x(i,:),E0,p,h,dt);ok(i)=true;
    catch err,identifier(i)=string(err.identifier);message(i)=string(err.message);end
end
preflight=table((1:N)',ok,identifier,message,'VariableNames',{'Interval','Admissible','Error_ID','Message'});
a=struct('version','0.49','model_version','0.42','new_model',false,'p',p,'h',h,'c',c, ...
    'initial_energy_MWh',E0,'initial_clock',m,'inputs',x,'sample_times_h',(0:N-1)'*dt, ...
    'policy',policy,'preflight',preflight,'admissible',all(ok), ...
    'static_preflight_only',true,'evidence_class','EXPLICIT_SYNTHETIC_ENGINEERING_NOT_CALIBRATED');
end
