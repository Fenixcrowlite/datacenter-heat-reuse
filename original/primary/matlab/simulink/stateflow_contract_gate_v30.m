function checked = stateflow_contract_gate_v30(raw,hpPorts,energyStart,cfgPorts,model_dt)
%#codegen
% Independent first-law and exact constant-power/temperature contract.
dt=cfgPorts(1); cap=cfgPorts(2); etaC=cfgPorts(5); etaD=cfgPorts(6);
rate=cfgPorts(7); cutoff=cfgPorts(8); C=cfgPorts(9); Ta=cfgPorts(10);
assert(all(isfinite(cfgPorts)) && isfinite(energyStart) && all(isfinite(raw)), 'Nonfinite accepted state/parameters.');
assert(isfinite(model_dt) && dt==model_dt && dt>0 && isfinite(rate*dt), 'Physical interval/decay mismatch.');
assert(cap>=0 && C>0 && rate>=0 && cutoff>=0 && cutoff<=cap && Ta>-273.15 && ...
    cfgPorts(3)>=0 && cfgPorts(4)>=0 && cfgPorts(11)>=0 && etaC>0 && etaC<=1 && etaD>0 && etaD<=1, 'Invalid TES physical domain.');
assert(all(isfinite(hpPorts([1:5 7 8]))) && all(hpPorts([1:5 7 8])>=0), 'Invalid HP port.');
scale=max(1,abs(energyStart)+cap+(hpPorts(2)+cfgPorts(11))*dt);
tol=1e-10*scale; powerTol=tol/max(dt,eps);
assert(isfinite(scale) && isfinite(powerTol), 'Overflow in contract scale.');
assert(energyStart>=0 && energyStart<=cap && raw(8)>=-tol && raw(8)<=cap+tol, 'TES state outside capacity.');
assert(raw(1)==floor(raw(1)) && raw(1)>=0 && raw(1)<=5, 'Undefined mode.');
assert(all(raw([2:6 12])>=-powerTol) && all(raw(7:11)>=-tol), 'Negative dispatch or loss.');
assert(raw(3)<=cfgPorts(3)+powerTol && raw(4)<=cfgPorts(4)+powerTol && raw(5)<=cfgPorts(11)+powerTol, 'TES/boiler power bound.');
assert(raw(3)*raw(4)==0, 'Simultaneous TES ports.');
r=exp(-rate*dt); phi=dt;
if rate>0 && rate*dt>0, phi=-expm1(-rate*dt)/rate; end
P=etaC*raw(3)-raw(4)/etaD;
assert(abs(raw(7)-energyStart*r)<=tol && abs(raw(8)-(energyStart*r+P*phi))<=tol, 'Exact constant-power solution mismatch.');
assert(raw(4)==0 || raw(8)>=cutoff-tol, 'TES discharge crosses delivery cutoff.');
assert(abs(raw(9)-(energyStart+P*dt-raw(8)))<=tol && ...
    abs(raw(10)-(1-etaC)*raw(3)*dt)<=tol && abs(raw(11)-(1/etaD-1)*raw(4)*dt)<=tol, 'TES loss mismatch.');
assert(abs(raw(14)-(Ta+energyStart/C))<=tol/C && abs(raw(15)-(Ta+raw(8)/C))<=tol/C && ...
    abs(raw(16)-max(0,energyStart-cutoff))<=tol && abs(raw(17)-max(0,raw(8)-cutoff))<=tol, 'Temperature/usable-energy mismatch.');
assert(abs(hpPorts(2)-hpPorts(3)-hpPorts(4))*dt<=tol, 'HP first-law failure.');
assert(abs(hpPorts(2)-raw(2)-raw(3))*dt<=tol, 'Unallocated condenser heat.');
assert(abs(hpPorts(1)-raw(2)-raw(4)-raw(5)-raw(6))*dt<=tol, 'Demand closure failure.');
assert(abs(raw(12)-raw(2)-raw(4)-raw(5))*dt<=tol, 'Supplied heat mismatch.');
assert(abs(energyStart+(raw(3)-raw(4))*dt-raw(8)-sum(raw(9:11)))<=tol, 'TES first-law failure.');
residual=(hpPorts(4)+hpPorts(3)+raw(5))*dt+energyStart-raw(12)*dt-raw(8)-sum(raw(9:11));
assert(abs(residual)<=tol && abs(raw(13)-residual)<=tol, 'System first-law or reported residual failure.');
expected=0;
if raw(6)>0, expected=5;
elseif raw(5)>0, expected=4;
elseif raw(4)>0, expected=3;
elseif raw(3)>0, expected=2;
elseif raw(2)>0, expected=1;
end
assert(raw(1)==expected, 'Active state does not match delivered flows.');
if hpPorts(2)>0
    assert(isfinite(hpPorts(6)) && hpPorts(6)>1 && hpPorts(7)==1, 'Invalid operating COP.');
    assert(abs(hpPorts(3)*hpPorts(6)-hpPorts(2))*dt<=tol, 'COP mismatch.');
else
    assert(isnan(hpPorts(6)) && hpPorts(7)==0, 'Off HP must have undefined COP.');
end
checked=raw;
end
