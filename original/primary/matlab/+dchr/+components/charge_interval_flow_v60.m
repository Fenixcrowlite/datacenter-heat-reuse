function z=charge_interval_flow_v60(c,j,E,t,p,s,cells)
% Initial inventory AND duration intervals; all ports remain enclosures.
% Called only after a separate exact-manifold/regime proof. Not a controller.
if nargin<8,cells=128;end
assert(isreal(E)&&isreal(t)&&isequal(size(E),[1 2])&&isequal(size(t),[1 2]) && ...
    all(isfinite([E t]))&&E(1)<=E(2)&&E(1)>=0&&t(1)>0&&t(1)<=t(2) && ...
    isscalar(cells)&&cells==fix(cells)&&cells>=1&&cells<=4096, ...
    'DCHR:v60:Domain','Ordered finite inventory/duration intervals and cells required.');
iv=@(v)dchr.components.exact_rational_v60('interval',v);P=@(v)[v v];
A=iv(c.alpha{j});beta=iv(c.beta{j});a=iv(c.a);l0=iv(c.l0);l1=iv(c.l1);
k=sub(mul(P(p.eta_charge),A),P(p.loss_rate_per_h));B=mul(P(p.eta_charge),beta);
v=add(mul(k,E),B);assert(max(abs(mul(k,t)))<=1,'DCHR:v60:Span','Require outward |kt|<=1.');
[finish,intE]=flow(t);heat=add(mul(A,intE),mul(beta,t));source=P(0);
width=div(t,P(cells));
for n=1:cells
    t0=mul(t,div(P(n-1),P(cells)));t1=mul(t,div(P(n),P(cells)));
    % dy/dt has fixed sign for each exact affine solution; endpoint hull suffices.
    [e0,~]=flow(t0);[e1,~]=flow(t1);eh=[min(e0(1),e1(1)) max(e0(2),e1(2))];
    q=add(mul(A,eh),beta);lift=add(l0,mul(l1,eh));
    src=mul(q,div(a,add(a,lift)));source=add(source,mul(src,width));
end
work=sub(heat,source);standing=mul(P(p.loss_rate_per_h),intE);
chargeLoss=mul(sub(P(1),P(p.eta_charge)),heat);
aux=mul(P(s.aux_per_compressor),work);
balance=sub(sub(sub(add(E,heat),finish),standing),chargeLoss);
assert(source(1)>=0&&work(1)>=0&&balance(1)<=0&&balance(2)>=0,'DCHR:v60:Resolution','Unresolved port positivity/first law.');
z=struct('initial_energy_MWh_interval',E,'duration_h_interval',t,'end_energy_MWh_interval',finish, ...
    'integral_energy_MWh_h_interval',intE,'heat_MWh_interval',heat,'source_MWh_interval',source, ...
    'compressor_MWh_interval',work,'standing_loss_MWh_interval',standing, ...
    'charge_loss_MWh_interval',chargeLoss,'aux_rejected_MWh_interval',aux,'first_law_MWh_interval',balance);
    function [energy,integral]=flow(span)
        x=mul(k,span);assert(max(abs(x))<=1,'DCHR:v60:Span','Outward evaluation node exceeds span.');
        f1=P(1);f2=P(.5);term=P(1);
        for ii=1:24,term=div(mul(term,x),P(ii+1));f1=add(f1,term);f2=add(f2,div(term,P(ii+2)));end
        factorial=P(1);for ii=2:26,factorial=mul(factorial,P(ii));end
        tail=div(P(3),factorial);f1=add(f1,[-tail(2) tail(2)]);f2=add(f2,[-tail(2) tail(2)]);
        energy=add(E,mul(mul(v,span),f1));integral=add(mul(E,span),mul(mul(v,mul(span,span)),f2));
    end
end
function z=add(x,y),z=out([x(1)+y(1) x(2)+y(2)]);end
function z=sub(x,y),z=out([x(1)-y(2) x(2)-y(1)]);end
function z=mul(x,y),v=[x(1)*y(1) x(1)*y(2) x(2)*y(1) x(2)*y(2)];z=out([min(v) max(v)]);end
function z=div(x,y)
assert(y(1)>0,'DCHR:v60:Resolution','Positive denominator required.');
v=[x(1)/y(1) x(1)/y(2) x(2)/y(1) x(2)/y(2)];z=out([min(v) max(v)]);
end
function z=out(v)
assert(all(isfinite(v)),'DCHR:v60:Resolution','Nonfinite arithmetic.');z=[v(1)-2*eps(v(1)) v(2)+2*eps(v(2))];
assert(all(isfinite(z))&&z(1)<=z(2),'DCHR:v60:Resolution','Outward expansion failed.');
end
