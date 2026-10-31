function a=adapt_stateflow_inputs_v49(cfg,input,policy)
% Explicit annual boundary adapter for saved v42; no model/controller edits.
% Every policy value is an engineering assumption, not equipment calibration.
dt=cfg.sim.dt_h;s=cfg.storage;N=numel(input.time);
validateattributes(dt,{'double'},{'real','finite','scalar','positive'});
assert(N>0&&iscolumn(input.time)&&all(~isnat(input.time))&& ...
    all(abs(hours(diff(input.time))-dt)<=32*eps(max(1,dt))), ...
    'DCHR:v49:InputDomain','Finite uniformly spaced datetime column required.');
for name={'outdoor_temp_C','it_power_MW'}
    validateattributes(input.(name{1}),{'double'},{'real','finite','column','numel',N});
end
assert(all(input.it_power_MW>=0),'DCHR:v49:InputDomain','Negative source electric power.');
validateattributes(cfg.dc.recovery_fraction,{'double'},{'scalar','real','finite','>=',0,'<=',1});
if cfg.hx.enabled
    validateattributes(cfg.hx.effectiveness,{'double'},{'scalar','real','finite','>=',0,'<=',1});
    validateattributes(cfg.hx.max_heat_MW,{'double'},{'scalar','real','finite','nonnegative'});
    validateattributes(cfg.hx.approach_K,{'double'},{'scalar','real','finite','nonnegative'});
end
v=[policy.ambient_C policy.tank_max_C policy.cutoff_C policy.restart_C ...
    policy.min_on_h policy.min_off_h policy.max_segments];
validateattributes(v,{'double'},{'row','real','finite','numel',7});
assert(policy.ambient_C<policy.cutoff_C&&policy.cutoff_C<policy.restart_C&& ...
    policy.restart_C<policy.tank_max_C,'DCHR:v49:PolicyDomain','Ordered tank temperature bands required.');
validateattributes(s.capacity_MWh,{'double'},{'scalar','real','finite','positive'});
validateattributes(s.initial_soc,{'double'},{'scalar','real','finite','>=',0,'<=',1});
validateattributes(s.loss_fraction_per_h,{'double'},{'scalar','real','finite','nonnegative'});
assert(s.loss_fraction_per_h*dt<1,'DCHR:v49:LossDomain','Finite exponential rate requires loss*dt<1.');
src=dchr.components.dc_source(input.it_power_MW,cfg);
hx=dchr.components.heat_exchanger(src.heat_MW,src.temperature_C,cfg);
dh=dchr.components.dh_temperature(input.outdoor_temp_C,cfg);
demand=dchr.heat_demand(input.outdoor_temp_C,cfg);
validateattributes(demand,{'double'},{'real','finite','column','numel',N,'nonnegative'});
sink=dh.supply_C;
if strcmp(policy.condenser_policy,'fixed_explicit')
    validateattributes(policy.condenser_C,{'double'},{'scalar','real','finite'});
    sink=repmat(policy.condenser_C,N,1);
elseif ~strcmp(policy.condenser_policy,'native_network_supply')
    error('DCHR:v49:PolicyDomain','Choose native_network_supply or fixed_explicit.');
end
assert(max(dh.supply_C)<=policy.cutoff_C&&policy.tank_max_C<=min(sink), ...
    'DCHR:v49:TemperatureEnvelope','Saved-v42 requires max delivery <= cutoff < tank maximum <= min condenser.');
C=s.capacity_MWh/(policy.tank_max_C-policy.ambient_C);
lambda=-log1p(-s.loss_fraction_per_h*dt)/dt;
p=[dt s.capacity_MWh s.charge_limit_MW s.discharge_limit_MW ...
    s.eta_charge s.eta_discharge lambda C*(policy.cutoff_C-policy.ambient_C) ...
    C policy.ambient_C cfg.backup.max_heat_MW];
h=[cfg.hp.max_heat_output_MW cfg.hp.carnot_efficiency cfg.hp.cop_min cfg.hp.cop_max ...
    cfg.hp.part_load_penalty 0 cfg.hp.poly_c0 cfg.hp.poly_c1 cfg.hp.poly_c2];
if strcmp(cfg.model.hp_backend,'lift_polynomial'),h(6)=1;
else,assert(strcmp(cfg.model.hp_backend,'carnot'),'DCHR:v49:PolicyDomain','Undefined HP backend.');end
c=[C*(policy.restart_C-policy.ambient_C) policy.min_on_h policy.min_off_h policy.max_segments];
E0=s.initial_soc*s.capacity_MWh;m0=[0;0;0;0];
x=[hx.heat_to_hp_MW hx.evaporator_source_C sink demand dh.supply_C];
% Host physical contract on every interval before any Simulink execution.
for k=1:N,dchr_stateflow_hp_v42(x(k,:)',E0,p,h,dt);end
dchr_segment_plan_v42(x(1,:)',E0,p,h,dt,m0,c);
a=struct('version','0.49','model_version','0.42','policy',policy,'p',p,'h',h, ...
    'c',c,'initial_energy_MWh',E0,'initial_clock',m0,'inputs',x, ...
    'preflight_intervals',N,'temperature_min_condenser_C',min(sink), ...
    'temperature_max_delivery_C',max(dh.supply_C), ...
    'passive_retention_mapping','lambda=-log(1-loss_fraction*dt)/dt', ...
    'evidence_class','SYNTHETIC_ENGINEERING_NOT_MEASURED');
end
