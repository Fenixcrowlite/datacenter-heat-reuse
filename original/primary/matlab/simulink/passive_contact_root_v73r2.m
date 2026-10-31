function z=passive_contact_root_v73r2(p,horizon,dwell,age)
%#codegen
% Exact symbolic STOP -> RESTART contact, B=0. The common heat capacity
% cancels: tau=log1p((Tstop-Trestart)/(Trestart-Ta))/lambda.
% This applies only with the retained STOP tag, never to a general E box.
P=@(v)[v v];assert(p(6)>0&&p(25)>p(5)&&p(5)>p(2),'v73r2 passive contact domain');
difference=minusiv(P(p(25)),P(p(5)));base=minusiv(P(p(5)),P(p(2)));
x=diviv(difference,base);assert(x(1)>0&&x(2)<=.5,'v73r2 log1p domain');
term=x;value=x;
for j=2:32
    term=muliv(term,x);part=diviv(term,P(j));
    if mod(j,2)==0,value=minusiv(value,part);else,value=plusiv(value,part);end
end
% Alternating log series error <=x^33/33 for 0<x<=1/2.
tail=diviv(muliv(term,x),P(33));value=plusiv(value,[0 tail(2)]);
time=diviv(value,P(p(6)));wait=max(0,minusiv(P(dwell),age));ready=max(time,wait);
target=muliv(P(p(1)),minusiv(P(p(5)),P(p(2))));
z=zeros(15,1);z(13)=-1;z(14:15)=target';z(8:9)=wait';z(10:11)=ready';z(2:3)=time';
if time(1)>horizon
    z(1)=0;z(12)=3;
elseif time(2)>=horizon
    z(1)=2;z(12)=2;
else
    z(1)=1;
    if ready(2)<horizon,z(12)=1;elseif ready(1)>horizon,z(12)=3;else,z(12)=2;end
end
end
function z=plusiv(x,y)
if all(x==0),z=y;elseif all(y==0),z=x;else,z=out([x(1)+y(1) x(2)+y(2)]);end
end
function z=minusiv(x,y)
if all(y==0),z=x;else,z=out([x(1)-y(2) x(2)-y(1)]);end
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
v=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(v) max(v)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v73r2 positive contact denominator');if all(x==0),z=[0 0];return;end
v=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(v) max(v)]);
end
function z=out(v)
assert(all(isfinite(v)),'v73r2 contact overflow');z=[v(1)-2*eps(v(1)) v(2)+2*eps(v(2))];
end
