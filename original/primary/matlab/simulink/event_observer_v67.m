function z=event_observer_v67(u,cfg,plant_trace)
%#codegen
% Potential FULL held-power paths, not the sampled allocated charge/discharge.
% Each candidate retains the complete incoming inventory/age interval.
z=zeros(51,1);if u(1)==0,return;end
assert(u(4)==0||u(4)==1,'v67 strict event flag');
p=cfg(36:60);E=plant_trace(160:161)';age=plant_trace(162:163)';P=@(x)[x x];
C=P(p(1));Ta=P(p(2));lam=p(6);H=u(5);
stop=muliv(C,minusiv(P(p(25)),Ta));cut=muliv(C,minusiv(P(p(4)),Ta));restart=muliv(C,minusiv(P(p(5)),Ta));
Te=minusiv(minusiv(P(p(12)),P(p(13))),P(p(14)));a=muliv(P(p(15)),plusiv(Te,P(273.15)));
floor=plusiv(P(p(19)),P(p(20)));lift=minusiv(plusiv(floor,P(p(18))),Te);
source=muliv(muliv(P(u(7)),P(p(13))),plusiv(P(1),diviv(lift,a)));
hot=muliv(P(p(16)),P(p(17)));limit=max(0,min([p(11) source(1) hot(1)]));
charge=max(0,min(p(9),limit-min(u(6),limit)));
if u(8)==1&&u(9)==1&&charge>0
    B=muliv(P(p(7)),P(charge));
    % Only reachable increasing paths enter the root solver.
    deriv=minusiv(B,muliv(P(lam),stop));
    if deriv(1)>0,z(1:15)=certify_event_root_v67(E,B,lam,stop,1,H,0,[0 0]);z(46:47)=B';end
end
dis=min(u(6),p(10));
if dis>0
    B=-fliplr(diviv(P(dis),P(p(8))));z(16:30)=certify_event_root_v67(E,B,lam,cut,-1,H,0,[0 0]);z(48:49)=B';
end
if plant_trace(164)==0&&u(8)==1&&charge>0
    if lam>0,z(31:45)=certify_event_root_v67(E,[0 0],lam,restart,-1,H,p(23),age);
    elseif E(2)<=restart(1),z(31:45)=certify_event_root_v67(E,[0 0],lam,restart,-1,H,p(23),age);end
end
if u(4)==1
    assert(all(z([1 16 31])~=2)&&all(z([12 27 42])~=2),'v67 unresolved event ordering');
end
end
function z=certify_event_root_v67(E,B,lambda,target,direction,horizon,dwell,age)
%#codegen
% Held affine trajectory certificate. This returns a bracket, never a state reset.
% z=[status,tlo,thi,E(tlo).lo,hi,E(thi).lo,hi,wait.lo,hi,
%    ready.lo,hi,ordering,direction,target.lo,hi].
% status: 0 no crossing in horizon, 1 strict interior bracket,
% 2 unresolved contact/horizon, 3 already on the reached side.
% ordering: 0 no event, 1 ready strictly before horizon,
% 2 ordering unresolved, 3 ready strictly after horizon.
assert(all(isfinite([E B lambda target direction horizon dwell age])), 'v67 finite root domain');
assert(E(1)>=0&&E(1)<=E(2)&&B(1)<=B(2)&&target(1)>=0&&target(1)<=target(2)&& ...
    lambda>=0&&horizon>0&&lambda*horizon<=1&&ismember(direction,[-1 1])&& ...
    dwell>=0&&age(1)>=0&&age(1)<=age(2),'v67 root domain');
P=@(x)[x x];z=zeros(15,1);z(13)=direction;z(14:15)=target';
wait=minusiv(P(dwell),age);wait=max(0,wait);z(8:9)=wait';
before=@(v) (direction==1&&v(2)<target(1))||(direction==-1&&v(1)>target(2));
after=@(v) (direction==1&&v(1)>target(2))||(direction==-1&&v(2)<target(1));
reached=(direction==1&&E(1)>=target(2))||(direction==-1&&E(2)<=target(1));
if reached
    z(1)=3;z(4:7)=[E';E'];z(10:11)=wait';
elseif ~before(E)
    z(1)=2;z(2:3)=[0;horizon];z(12)=2;return;
else
    % Derivative sign at both ends certifies monotonicity on the entire
    % reachable segment. Equilibria and unresolved monotonicity are refused.
    d0=minusiv(B,muliv(P(lambda),E));d1=minusiv(B,muliv(P(lambda),target));
    if direction==1
        assert(d0(1)>0&&d1(1)>0,'v67 increasing root not certified');
    else
        assert(d0(2)<0&&d1(2)<0,'v67 decreasing root not certified');
    end
    endpoint=flow(E,P(horizon),lambda,B);
    if before(endpoint)
        z(1)=0;z(2:3)=horizon;z(4:7)=[endpoint';endpoint'];return;
    elseif ~after(endpoint)
        z(1)=2;z(2:3)=[0;horizon];z(4:7)=[E';endpoint'];z(12)=2;return;
    end
    % Search for the latest certainly-before and earliest certainly-after
    % witnesses independently. Ambiguous evaluations never choose a side.
    lo=0;right=horizon;
    for j=1:48
        mid=lo+(right-lo)/2;v=flow(E,P(mid),lambda,B);
        if before(v),lo=mid;else,right=mid;end
    end
    left=0;hi=horizon;
    for j=1:48
        mid=left+(hi-left)/2;v=flow(E,P(mid),lambda,B);
        if after(v),hi=mid;else,left=mid;end
    end
    elo=flow(E,P(lo),lambda,B);ehi=flow(E,P(hi),lambda,B);
    assert(before(elo)&&after(ehi)&&0<=lo&&lo<hi&&hi<horizon,'v67 root witnesses');
    z(1)=1;z(2:3)=[lo;hi];z(4:7)=[elo';ehi'];
    z(10:11)=[max(lo,wait(1));max(hi,wait(2))];
end
if z(11)<horizon,z(12)=1;elseif z(10)>horizon,z(12)=3;else,z(12)=2;end
end
function en=flow(initial,t,lambda,B)
if all(t==0),en=initial;return;end
P=@(v)[v v];k=-P(lambda);x=muliv(k,t);
assert(max(abs(x))<=1,'v67 outward root span');
v=plusiv(muliv(k,initial),B);f1=P(1);term=P(1);
for j=1:24,term=diviv(muliv(term,x),P(j+1));f1=plusiv(f1,term);end
fac=P(1);for j=2:26,fac=muliv(fac,P(j));end
tail=diviv(P(3),fac);f1=plusiv(f1,[-tail(2) tail(2)]);
en=plusiv(initial,muliv(muliv(v,t),f1));
end
function z=plusiv(x,y)
if all(x==0),z=y;elseif all(y==0),z=x;else,z=out([x(1)+y(1) x(2)+y(2)]);end
end
function z=minusiv(x,y)
if all(y==0),z=x;elseif x(1)==x(2)&&y(1)==y(2)&&x(1)==y(1),z=[0 0];else,z=out([x(1)-y(2) x(2)-y(1)]);end
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v67 positive root denominator');
if all(x==0),z=[0 0];return;end
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'v67 root arithmetic overflow');z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];
assert(all(isfinite(z))&&z(1)<=z(2),'v67 root expansion overflow');
end
