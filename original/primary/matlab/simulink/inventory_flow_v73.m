function [en,integral]=inventory_flow_v73(initial,t,lambda,B)
%#codegen
% Monotone affine inventory image. Exact E and B dependence occurs once.
% Each corner is monotone in time (its derivative has constant sign).
% Positive Taylor exp(+lambda*t), followed by reciprocal, avoids passive
% subtraction/wrapping. All arithmetic bounds expand by two binary ulps.
assert(initial(1)>=0&&initial(1)<=initial(2)&&t(1)>=0&&t(1)<=t(2)&& ...
    lambda>=0&&lambda*t(2)<=2&&B(1)<=B(2),'v73 flow domain');
if all(t==0),en=initial;integral=[0 0];return;end
lo=zeros(1,4);hi=zeros(1,4);n=0;
for ei=1:2
    for ti=1:2
        n=n+1;[value,~]=corner(initial(ei),t(ti),lambda,B(ei));lo(n)=value(1);hi(n)=value(2);
    end
end
en=[min(lo) max(hi)];
% Integral's positive trajectory has monotone initial/forcing dependence;
% its direct phi image remains conservative for variable time.
[~,f1,f2]=coeff(t,lambda);
integral=plusiv(muliv(initial,muliv(t,f1)),muliv(B,muliv(muliv(t,t),f2)));
end
function [en,unused]=corner(E,t,lambda,B)
P=@(x)[x x];[r,f1,~]=coeff(P(t),lambda);
if t==0,en=P(E);
elseif B==0,en=muliv(P(E),r);
else
    % Singleton corner evaluation retains small active changes without
    % subtracting rounded exponential factors. Uncertain inventory is never
    % used twice as independent operands: its monotone corners are separate.
    v=plusiv(muliv(P(-lambda),P(E)),P(B));
    en=plusiv(P(E),muliv(muliv(v,P(t)),f1));
end
unused=0;
end
function [r,f1,f2]=coeff(t,lambda)
P=@(x)[x x];
if lambda==0,r=P(1);f1=P(1);f2=P(.5);return;end
x=muliv(P(lambda),t);term=P(1);ex=P(1);
for j=1:30,term=diviv(muliv(term,x),P(j));ex=plusiv(ex,term);end
fac=P(1);for j=2:31,fac=muliv(fac,P(j));end
% e^2<8; positive-series remainder <=8*2^31/31! on [0,2].
tail=diviv(P(17179869184),fac);ex=plusiv(ex,[0 tail(2)]);r=diviv(P(1),ex);
x=-[x(2) x(1)];term=P(1);f1=P(1);f2=P(.5);
for j=1:24,term=diviv(muliv(term,x),P(j+1));f1=plusiv(f1,term);f2=plusiv(f2,diviv(term,P(j+2)));end
fac=P(1);for j=2:26,fac=muliv(fac,P(j));end
tail=diviv(P(268435456),fac);f1=plusiv(f1,[-tail(2) tail(2)]);f2=plusiv(f2,[-tail(2) tail(2)]);
end
function z=plusiv(x,y)
if all(x==0),z=y;elseif all(y==0),z=x;else,z=out([x(1)+y(1) x(2)+y(2)]);end
end
function z=muliv(x,y)
if all(x==0)||all(y==0),z=[0 0];return;end
t=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(t) max(t)]);
end
function z=diviv(x,y)
assert(y(1)>0,'v73 flow denominator');if all(x==0),z=[0 0];return;end
t=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(t) max(t)]);
end
function z=out(t)
assert(all(isfinite(t)),'v73 flow overflow');z=[t(1)-2*eps(t(1)) t(2)+2*eps(t(2))];
assert(all(isfinite(z)),'v73 flow outward overflow');
end
