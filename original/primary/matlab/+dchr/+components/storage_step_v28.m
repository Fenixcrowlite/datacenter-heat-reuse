function st = storage_step_v28(E_MWh, surplus_MW, deficit_MW, cfg)
%STORAGE_STEP_V28 Exponential passive cooling, then bounded port allocation.
% lambda=continuous_loss_rate_per_h is a continuous decay rate in h^-1.
% LOSS-FIRST operator split: E_after=E_start*exp(-lambda*dt), followed by
% interval charge/discharge. Passive cooling is exact; forcing is split,
% so fresh charge experiences no standing loss until the next interval.
% This is an engineering one-node energy model, not a calibrated UA model.
% Charge input and discharge output are measured at the external TES ports.
s=cfg.storage; dt=cfg.sim.dt_h;
scalar(dt,'dt_h',0,Inf,true);
scalar(s.capacity_MWh,'capacity_MWh',0,Inf,false);
scalar(s.charge_limit_MW,'charge_limit_MW',0,Inf,false);
scalar(s.discharge_limit_MW,'discharge_limit_MW',0,Inf,false);
scalar(s.eta_charge,'eta_charge',0,1,true);
scalar(s.eta_discharge,'eta_discharge',0,1,true);
if ~isfield(s,'continuous_loss_rate_per_h')
    error('DCHR:v28:StorageDomain', ...
        'Set explicit storage.continuous_loss_rate_per_h in h^-1.');
end
scalar(s.continuous_loss_rate_per_h,'continuous_loss_rate_per_h',0,Inf,false);
scalar(E_MWh,'E_MWh',0,s.capacity_MWh,false);
scalar(surplus_MW,'surplus_MW',0,Inf,false);
scalar(deficit_MW,'deficit_MW',0,Inf,false);
decay=double(s.continuous_loss_rate_per_h)*double(dt);
if ~isfinite(decay)
    error('DCHR:v28:StorageDomain','Continuous decay rate times dt must be finite.');
end
if surplus_MW>0 && deficit_MW>0
    error('DCHR:v28:SimultaneousStorageRequests','Charge and discharge requests must be mutually exclusive.');
end
E=double(E_MWh); dt=double(dt);
after=E*exp(-decay);
% expm1 avoids subtractive cancellation for small positive decay rates.
standing=-E*expm1(-decay);
charge=0; discharge=0;
if surplus_MW>0
    charge=min([double(surplus_MW),double(s.charge_limit_MW), ...
        ((double(s.capacity_MWh)-after)/dt)/double(s.eta_charge)]);
elseif deficit_MW>0
    discharge=min([double(deficit_MW),double(s.discharge_limit_MW), ...
        (after/dt)*double(s.eta_discharge)]);
end
storedCharge=double(s.eta_charge)*charge*dt;
removedDischarge=discharge*dt/double(s.eta_discharge);
next=after+storedCharge-removedDischarge;
% Only roundoff at the two analytically bounded endpoints is corrected.
tolerance=64*eps(max(1,double(s.capacity_MWh)));
if ~isfinite(next) || next < -tolerance || next > double(s.capacity_MWh)+tolerance
    error('DCHR:v28:StorageBalance','Computed storage state is outside its bounded interval.');
end
next=min(double(s.capacity_MWh),max(0,next));
st=struct('charge_MW',charge,'discharge_MW',discharge, ...
    'energy_after_loss_MWh',after,'energy_next_MWh',next, ...
    'standing_loss_MWh',standing, ...
    'charge_loss_MWh',(1-double(s.eta_charge))*charge*dt, ...
    'discharge_loss_MWh',removedDischarge-discharge*dt);
end

function scalar(value,name,lo,hi,strictLo)
if ~isnumeric(value) || ~isreal(value) || ~isscalar(value) || ~isfinite(value)
    error('DCHR:v28:StorageDomain','%s must be a finite real numeric scalar.',name);
end
v=double(value);
if v<lo || v>hi || (strictLo && v==lo)
    error('DCHR:v28:StorageDomain','%s is outside its physical domain.',name);
end
end
