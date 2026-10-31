function p = storage_parameters_v30(cfg)
%STORAGE_PARAMETERS_V30 Validate dimensional TES data and derive energy bounds.
% Config carries C and absolute temperatures, rather than an independent
% arbitrary energy capacity. Ambient is fixed over all integration intervals.
if ~isstruct(cfg) || ~isfield(cfg,'storage') || ~isstruct(cfg.storage) || ...
        ~isfield(cfg,'sim') || ~isstruct(cfg.sim) || ~isfield(cfg.sim,'dt_h')
    error('DCHR:v30:StorageDomain','Set explicit sim and storage structures.');
end
s=cfg.storage;
names={'heat_capacity_MWh_per_K','ambient_C','delivery_cutoff_C', ...
    'max_temperature_C','initial_temperature_C','charge_limit_MW', ...
    'discharge_limit_MW','eta_charge','eta_discharge','continuous_loss_rate_per_h'};
for j=1:numel(names)
    if ~isfield(s,names{j})
        error('DCHR:v30:StorageDomain','Set explicit storage.%s.',names{j});
    end
    finiteScalar(s.(names{j}),names{j});
end
finiteScalar(cfg.sim.dt_h,'dt_h');
C=double(s.heat_capacity_MWh_per_K); Ta=double(s.ambient_C);
Tcut=double(s.delivery_cutoff_C); Tmax=double(s.max_temperature_C);
T0=double(s.initial_temperature_C); dt=double(cfg.sim.dt_h);
if dt<=0 || C<=0 || Ta<=-273.15 || Tcut<Ta || Tmax<Tcut || ...
        T0<Ta || T0>Tmax || s.charge_limit_MW<0 || s.discharge_limit_MW<0 || ...
        s.eta_charge<=0 || s.eta_charge>1 || s.eta_discharge<=0 || ...
        s.eta_discharge>1 || s.continuous_loss_rate_per_h<0
    error('DCHR:v30:StorageDomain','TES dimensional parameters violate their physical domain.');
end
cap=C*(Tmax-Ta); cut=C*(Tcut-Ta);
if ~isfinite(cap) || ~isfinite(cut) || ~isfinite(C*(T0-Ta)) || ...
        ~isfinite(double(s.continuous_loss_rate_per_h)*dt)
    error('DCHR:v30:StorageDomain','Derived TES energy or rate product is nonfinite.');
end
p=[dt;cap;double(s.charge_limit_MW);double(s.discharge_limit_MW); ...
    double(s.eta_charge);double(s.eta_discharge); ...
    double(s.continuous_loss_rate_per_h);cut;C;Ta];
% Also check exact coefficient/bound numerical representability at A=0.
try
    dchr.components.storage_kernel_v30(0,0,0,p);
catch original
    failure=MException('DCHR:v30:StorageDomain', ...
        'TES numerical domain rejection: %s',original.message);
    failure=addCause(failure,original); throw(failure);
end
end

function finiteScalar(value,name)
if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value)
    error('DCHR:v30:StorageDomain','%s must be a finite real numeric scalar.',name);
end
end
