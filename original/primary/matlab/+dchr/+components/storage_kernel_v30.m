function z = storage_kernel_v30(A,chargeRequest,dischargeRequest,p)
%STORAGE_KERNEL_V30 Exact constant-port, ambient-referenced sensible TES.
%#codegen
% p=[dt_h;capacity_MWh;charge_limit_MW;discharge_limit_MW;etaC;etaD;
%    lambda_per_h;cutoff_MWh;heat_capacity_MWh_per_K;ambient_C].
% z=[charge_MW;discharge_MW;passive_MWh;next_MWh;standing_loss_MWh;
%    charge_loss_MWh;discharge_loss_MWh;start_C;next_C;usable_start_MWh;
%    usable_next_MWh;charge_bound_MW;discharge_bound_MW].
% Ports are constant across the complete following dt interval. Throttle
% before integration; there are no event pulses or clipping at the cutoff.
assert(numel(p)==10 && all(isfinite(p)), 'Invalid TES parameter vector.');
dt=p(1); cap=p(2); etaC=p(5); etaD=p(6); lambda=p(7); cut=p(8);
C=p(9); ambient=p(10);
assert(dt>0 && cap>=0 && all(p(3:4)>=0) && etaC>0 && etaC<=1 && ...
    etaD>0 && etaD<=1 && lambda>=0 && cut>=0 && cut<=cap && ...
    C>0 && ambient>-273.15, 'TES parameters outside physical domain.');
assert(isfinite(A) && A>=0 && A<=cap && isfinite(chargeRequest) && ...
    chargeRequest>=0 && isfinite(dischargeRequest) && dischargeRequest>=0, ...
    'TES state or request outside physical domain.');
assert(chargeRequest==0 || dischargeRequest==0, 'Simultaneous TES requests.');
x=lambda*dt;
assert(isfinite(x), 'Nonfinite continuous rate times interval.');
r=exp(-x); lossFraction=-expm1(-x);
if lambda==0 || x==0
    phi=dt; beta=0;
else
    phi=lossFraction/lambda;
    % beta=dt-phi. Series avoids cancellation near the zero-rate limit.
    if x<1e-4
        beta=dt*x*(0.5-x*(1/6-x*(1/24-x*(1/120-x/720))));
    else
        beta=dt-phi;
    end
end
assert(isfinite(phi) && phi>0 && isfinite(beta) && beta>=0, ...
    'Nonrepresentable exact TES integration coefficients.');
passive=A*r;
chargeBound=((cap-passive)/phi)/etaC;
dischargeBound=(max(0,passive-cut)/phi)*etaD;
assert(isfinite(chargeBound) && isfinite(dischargeBound), ...
    'Nonrepresentable TES port bounds.');
charge=0; discharge=0;
if chargeRequest>0
    charge=min([chargeRequest,p(3),max(0,chargeBound)]);
elseif dischargeRequest>0
    discharge=min([dischargeRequest,p(4),dischargeBound]);
end
power=etaC*charge-discharge/etaD;
next=passive+power*phi;
tol=64*eps(max(1,cap));
assert(isfinite(next) && next>=-tol && next<=cap+tol, ...
    'Exact TES integration violates ambient/capacity bounds.');
% Physical bounds only: correct endpoint roundoff, never force A>=cut.
next=min(cap,max(0,next));
standing=A*lossFraction+power*beta;
chargeLoss=(1-etaC)*charge*dt;
dischargeLoss=(1/etaD-1)*discharge*dt;
assert(isfinite(standing) && standing>=-tol && isfinite(chargeLoss) && ...
    isfinite(dischargeLoss), 'Nonrepresentable TES loss integrals.');
standing=max(0,standing);
startT=ambient+A/C; nextT=ambient+next/C;
assert(isfinite(startT) && isfinite(nextT), 'Nonrepresentable TES temperature.');
z=[charge;discharge;passive;next;standing;chargeLoss;dischargeLoss; ...
    startT;nextT;max(0,A-cut);max(0,next-cut);chargeBound;dischargeBound];
end
