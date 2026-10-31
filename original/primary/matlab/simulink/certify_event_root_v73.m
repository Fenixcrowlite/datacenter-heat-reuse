function z=certify_event_root_v73(E,B,lambda,target,direction,horizon,dwell,age)
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
[en,~]=inventory_flow_v73(initial,t,lambda,B);
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
