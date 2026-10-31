function checked = stateflow_contract_gate_v24(raw,hpPorts,energyStart,cfgPorts,model_dt)
%#codegen
% Executed after the operational chart, before accepted trace/TES feedback.
% All powers MW; energies MWh; dt h. No new physical-model assumption.
dt=cfgPorts(1); cap=cfgPorts(2); etaC=cfgPorts(5); etaD=cfgPorts(6);
assert(isfinite(model_dt) && model_dt>0 && dt==model_dt, ...
    'Physical interval must equal the model sample time.');
assert(all(isfinite(raw)) && all(isfinite(cfgPorts)), ...
    'Accepted dispatch and parameters must be finite.');
assert(all(isfinite(hpPorts([1 2 3 4 5 7 8]))), ...
    'HP ports except off-state COP must be finite.');
% Scale tolerance with total interval energy, never with a reported residual.
scale=max(1,abs(energyStart)+(abs(hpPorts(2))+abs(cfgPorts(8)))*dt+abs(cap));
tol=1e-10*scale;
powerTol=tol/max(dt,eps);
assert(isfinite(scale) && isfinite(tol) && isfinite(powerTol), 'Overflow in contract tolerance.');
assert(energyStart>=0 && energyStart<=cap && cap>=0, 'TES start outside capacity.');
assert(all(raw([2:6 12])>=-powerTol) && all(raw(7:11)>=-tol) && ...
    all(hpPorts([1 2 3 4 5 7 8])>=0), ...
    'Negative dispatch/HP port.');
assert(raw(1)==floor(raw(1)) && raw(1)>=0 && raw(1)<=5, 'Undefined mode.');
assert(raw(3)<=cfgPorts(3)+powerTol && raw(4)<=cfgPorts(4)+powerTol && ...
    raw(5)<=cfgPorts(8)+powerTol, 'TES/backup power limit exceeded.');
assert(raw(7)>=-tol && raw(7)<=cap+tol && raw(8)>=-tol && raw(8)<=cap+tol, ...
    'TES state outside capacity.');
assert(raw(3)*raw(4)==0, 'Simultaneous TES charge and discharge.');
assert(abs(hpPorts(2)-hpPorts(3)-hpPorts(4))*dt<=tol, 'HP first-law failure.');
assert(abs(hpPorts(2)-raw(2)-raw(3))*dt<=tol, 'Unallocated HP condenser heat.');
assert(abs(hpPorts(1)-raw(2)-raw(4)-raw(5)-raw(6))*dt<=tol, 'Demand closure failure.');
assert(abs(raw(12)-raw(2)-raw(4)-raw(5))*dt<=tol, 'Useful heat mismatch.');
assert(abs(raw(7)-energyStart*(1-cfgPorts(7)*dt))<=tol, 'Standing-retention mismatch.');
assert(abs(raw(9)-(energyStart-raw(7)))<=tol && ...
    abs(raw(10)-(1-etaC)*raw(3)*dt)<=tol && ...
    abs(raw(11)-(1/etaD-1)*raw(4)*dt)<=tol, 'TES loss reporting mismatch.');
tesResidual=energyStart+(raw(3)-raw(4))*dt-raw(8)-sum(raw(9:11));
assert(abs(tesResidual)<=tol, 'TES first-law failure.');
systemResidual=(hpPorts(4)+hpPorts(3)+raw(5))*dt+energyStart ...
    -raw(12)*dt-raw(8)-sum(raw(9:11));
assert(abs(systemResidual)<=tol && abs(raw(13)-systemResidual)<=tol, ...
    'System first-law failure or false residual.');
expected=0;
if raw(6)>0, expected=5;
elseif raw(5)>0, expected=4;
elseif raw(4)>0, expected=3;
elseif raw(3)>0, expected=2;
elseif raw(2)>0, expected=1;
end
assert(raw(1)==expected, 'Active state does not match delivered flows.');
if hpPorts(2)>0
    assert(isfinite(hpPorts(6)) && hpPorts(6)>1 && hpPorts(7)==1, 'Invalid operating COP/availability.');
    assert(abs(hpPorts(3)*hpPorts(6)-hpPorts(2))*dt<=tol, 'COP port inconsistency.');
else
    assert(isnan(hpPorts(6)) && hpPorts(7)==0, 'Off HP must have undefined COP.');
end
checked=raw;
end
