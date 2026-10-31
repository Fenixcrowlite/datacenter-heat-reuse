function st = storage_step_v16(E_MWh, surplus_MW, deficit_MW, cfg)
%STORAGE_STEP_V16 Strict loss-first, one-node discrete thermal storage step.
% Engineering assumption: linear standing retention 1-lambda*dt, followed
% by constant charge/discharge powers. This is not a continuous UA model.
% Charge input and discharge output are measured at the external TES ports.
s=cfg.storage; dt=cfg.sim.dt_h;
scalar(dt,'dt_h',0,Inf,true);
scalar(s.capacity_MWh,'capacity_MWh',0,Inf,false);
scalar(s.charge_limit_MW,'charge_limit_MW',0,Inf,false);
scalar(s.discharge_limit_MW,'discharge_limit_MW',0,Inf,false);
scalar(s.eta_charge,'eta_charge',0,1,true);
scalar(s.eta_discharge,'eta_discharge',0,1,true);
scalar(s.loss_fraction_per_h,'loss_fraction_per_h',0,Inf,false);
scalar(E_MWh,'E_MWh',0,s.capacity_MWh,false);
scalar(surplus_MW,'surplus_MW',0,Inf,false);
scalar(deficit_MW,'deficit_MW',0,Inf,false);
lossFraction=double(s.loss_fraction_per_h)*double(dt);
if ~isfinite(lossFraction) || lossFraction>1
    error('DCHR:v16:StorageDomain','Standing loss fraction times dt must be at most one.');
end
if surplus_MW>0 && deficit_MW>0
    error('DCHR:v16:SimultaneousStorageRequests','Charge and discharge requests must be mutually exclusive.');
end
E=double(E_MWh); dt=double(dt);
after=E*(1-lossFraction); standing=E-after;
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
    error('DCHR:v16:StorageBalance','Computed storage state is outside its bounded interval.');
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
    error('DCHR:v16:StorageDomain','%s must be a finite real numeric scalar.',name);
end
v=double(value);
if v<lo || v>hi || (strictLo && v==lo)
    error('DCHR:v16:StorageDomain','%s is outside its physical domain.',name);
end
end
