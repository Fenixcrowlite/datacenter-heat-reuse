function st = storage_step_v30(A_MWh,surplus_MW,deficit_MW,cfg)
%STORAGE_STEP_V30 Fixed-ambient temperature state with exact active ports.
% A=C*(T-Ta) is physical sensible energy above ambient, in MWh. Useful
% deliverable inventory max(0,A-Acut) is a reported service metric, not the
% physical state. Passive cooling may move the state below delivery cutoff.
p=dchr.components.storage_parameters_v30(cfg);
scalar(A_MWh,'A_MWh',0,p(2));
scalar(surplus_MW,'surplus_MW',0,Inf);
scalar(deficit_MW,'deficit_MW',0,Inf);
if surplus_MW>0 && deficit_MW>0
    error('DCHR:v30:SimultaneousStorageRequests','Charge and discharge requests must be mutually exclusive.');
end
try
    z=dchr.components.storage_kernel_v30(double(A_MWh),double(surplus_MW), ...
        double(deficit_MW),p);
catch original
    failure=MException('DCHR:v30:StorageBalance', ...
        'Exact TES integration rejection: %s',original.message);
    failure=addCause(failure,original); throw(failure);
end
st=struct('charge_MW',z(1),'discharge_MW',z(2), ...
    'energy_after_loss_MWh',z(3),'energy_next_MWh',z(4), ...
    'standing_loss_MWh',z(5),'charge_loss_MWh',z(6),'discharge_loss_MWh',z(7), ...
    'temperature_start_C',z(8),'temperature_next_C',z(9), ...
    'usable_energy_start_MWh',z(10),'usable_energy_next_MWh',z(11), ...
    'charge_bound_MW',z(12),'discharge_bound_MW',z(13), ...
    'capacity_MWh',p(2),'cutoff_energy_MWh',p(8));
end

function scalar(value,name,lo,hi)
if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value)
    error('DCHR:v30:StorageDomain','%s must be a finite real numeric scalar.',name);
end
if value<lo || value>hi
    error('DCHR:v30:StorageDomain','%s is outside its physical domain.',name);
end
end
