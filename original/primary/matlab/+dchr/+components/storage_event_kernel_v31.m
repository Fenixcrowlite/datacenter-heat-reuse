function z = storage_event_kernel_v31(A,chargeRequest,dischargeRequest,p)
%STORAGE_EVENT_KERNEL_V31 Full commanded power until a TES boundary event.
% Engineering comparator only; NOT embedded in the saved v30 Stateflow model.
% p uses the first ten v30 dimensional parameters. Constant requests/ambient.
% At capacity, modulate charge to replace standing loss. At delivery cutoff,
% turn discharge off and integrate passive cooling for the remaining time.
% z=[chargeAvg;dischargeAvg;passive;next;standing;chargeLoss;dischargeLoss;
% startT;nextT;usableStart;usableNext;fullCharge;fullDischarge;eventTime;
% eventKind(0=none,1=capacity,2=cutoff);tailCharge;tailDischarge;eventEnergy;
% chargeEnergy;dischargeEnergy]. No-event eventTime equals interval duration.
assert(isreal(p) && numel(p)==10 && all(isfinite(p)), 'DCHR:v31:Domain','Invalid parameter vector.');
dt=p(1);cap=p(2);ec=p(5);ed=p(6);rate=p(7);cut=p(8);C=p(9);Ta=p(10);
assert(dt>0 && cap>=0 && all(p(3:4)>=0) && ec>0 && ec<=1 && ...
    ed>0 && ed<=1 && rate>=0 && cut>=0 && cut<=cap && C>0 && Ta>-273.15 && ...
    isfinite(rate*dt), 'DCHR:v31:Domain','Invalid TES physical domain.');
assert(isreal(A) && isscalar(A) && isfinite(A) && A>=0 && A<=cap && ...
    isreal(chargeRequest) && isscalar(chargeRequest) && isfinite(chargeRequest) && chargeRequest>=0 && ...
    isreal(dischargeRequest) && isscalar(dischargeRequest) && isfinite(dischargeRequest) && dischargeRequest>=0, ...
    'DCHR:v31:Domain','Invalid state or request.');
assert(chargeRequest==0 || dischargeRequest==0, 'DCHR:v31:Domain','Simultaneous TES requests.');
qc=min(chargeRequest,p(3));qd=0;
if A>cut,qd=min(dischargeRequest,p(4));end
P=ec*qc-qd/ed;
[unconstrained,~]=segment(A,P,rate,dt);
t=dt;kind=0;tailC=0;tailD=0;
if qc>0 && P>rate*cap && unconstrained>=cap
    kind=1;
    if rate==0 || rate*dt==0
        t=(cap-A)/P;
    else
        % log1p form avoids subtracting two large equilibrium energies.
        t=log1p(rate*(cap-A)/(P-rate*cap))/rate;
    end
    tailC=rate*cap/ec;
elseif qd>0 && unconstrained<=cut
    kind=2;
    if rate==0 || rate*dt==0
        t=(A-cut)/(qd/ed);
    else
        t=log1p(rate*(A-cut)/(qd/ed+rate*cut))/rate;
    end
end
assert(isfinite(t) && t>=0 && t<=dt+64*eps(max(1,dt)), ...
    'DCHR:v31:NumericalDomain','Nonrepresentable event time.');
t=min(dt,t);tail=dt-t;
[eventA,L1]=segment(A,P,rate,t);
tol=1e-11*max(1,cap+abs(P)*dt);
if kind==1
    assert(abs(eventA-cap)<=tol, 'DCHR:v31:Balance','Capacity event mismatch.');
    eventA=cap;next=cap;L2=rate*cap*tail;
elseif kind==2
    assert(abs(eventA-cut)<=tol, 'DCHR:v31:Balance','Cutoff event mismatch.');
    eventA=cut;[next,L2]=segment(cut,0,rate,tail);
else
    next=eventA;L2=0;
end
chargeE=qc*t+tailC*tail;dischargeE=qd*t+tailD*tail;
standing=L1+L2;Lc=(1-ec)*chargeE;Ld=(1/ed-1)*dischargeE;
assert(next>=-tol && next<=cap+tol && standing>=-tol && ...
    abs(A+chargeE-dischargeE-next-standing-Lc-Ld)<=tol, ...
    'DCHR:v31:Balance','TES event integration violates first law/bounds.');
next=min(cap,max(0,next));standing=max(0,standing);
passive=A*exp(-rate*dt);
z=[chargeE/dt;dischargeE/dt;passive;next;standing;Lc;Ld;Ta+A/C;Ta+next/C; ...
    max(0,A-cut);max(0,next-cut);qc;qd;t;kind;tailC;tailD;eventA;chargeE;dischargeE];
assert(all(isfinite(z)), 'DCHR:v31:NumericalDomain','Nonfinite event output.');
end

function [endpoint,loss]=segment(A,P,rate,h)
x=rate*h;f=-expm1(-x);phi=h;beta=0;
if rate>0 && x>0
    phi=f/rate;
    if x<1e-4
        beta=h*x*(0.5-x*(1/6-x*(1/24-x*(1/120-x/720))));
    else
        beta=h-phi;
    end
end
endpoint=A*exp(-x)+P*phi;loss=A*f+P*beta;
end
